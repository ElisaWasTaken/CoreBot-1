import discord, os, ids
from discord.ext import commands, tasks
from modules.db_manager import Data, CoreBot
from modules.errors import get_error_msg
from modules.constants import Mentions
from modules.youtube import get_video_link
from modules import embeds
from datetime import datetime, timedelta
from traceback import format_exc

class SystemLoops(commands.Cog):
    def __init__(self, bot: CoreBot):
        self.bot = bot
        self.mainLoop.start()
        self.localWarnsReset.start()
        self.multiTaskLoop.start()
        self.YoutubeDataFetcher.start()
        self.YoutubeContentPoster.start()

    @tasks.loop(minutes=10)
    async def YoutubeDataFetcher(self):
        for youtuber in Data.get_all_youtubers():
            try:
                new_video = youtuber.update_videos()
            except:
                print(f'Failed to fetch videos for youtuber {youtuber.id}')
                continue
            if new_video != None and (youtuber.premium or youtuber.times_advertised <= 2):
                youtuber.times_advertised += 1
                data = Data()
                data.youtube_queue[youtuber.id] = new_video
                data.save()
                youtuber.save()

    @tasks.loop(minutes=5)
    async def YoutubeContentPoster(self):
        data = Data()
        if len(data.youtube_queue) > 0:
            youtube_channel = self.bot.server.get_channel(ids.YOUTUBE_CHANNEL_ID)
            member_id = list(data.youtube_queue.keys())[0]
            video_id = data.youtube_queue[member_id]
            data.youtube_queue.pop(member_id)
            m = await youtube_channel.send(f'<@&{ids.NEW_VIDEO_ROLE_ID}>\nOur content creator <@{member_id}> \
just posted a new video!\n\n{get_video_link(video_id)}')
            await m.publish()

        data.save()

    @tasks.loop(seconds=20)
    async def mainLoop(self):
        for case in Data.get_all_recent_cases(2):
            try:
                if case.length != None and case.applied_at + case.length <= datetime.now():
                    case.delete()
                    if case.type != 'warn':
                        await self.bot.logCase(case)
                    member = self.bot.server.get_member(case.victim_id)
                    if case.type == "unban":
                        await self.bot.get_user(case.victim_id).unban()
                    elif case.type == "unmute":
                        await member.remove_roles(self.bot.muted)
                    elif case.type == "uncmute":
                        channel = self.bot.server.get_channel(int(case.additional))
                        overwrites = self.bot.server.channel.overwrites_for(member)
                        overwrites.update(send_messages=None)
                        await channel.set_permissions(member, overwrite=overwrites)
                    elif case.type == "unfilemute":
                        await member.remove_roles(self.bot.filemuted)

            except Exception as e: print(e)

        for member in Data.get_all_members():
            for warn in member.get_all_warns():
                if (datetime.now()-warn.applied_at).days >= 30:
                    warn.delete()

        if self.bot.server.voice_client != None and len(self.bot.server.voice_client.channel.members) == 1:
            await self.bot.server.voice_client.disconnect()

    @tasks.loop(minutes=30)
    async def localWarnsReset(self):
        self.bot.next_reset = datetime.now()+timedelta(minutes=30)
        self.bot.local_warns.clear()

    @tasks.loop(minutes=30)
    async def multiTaskLoop(self):
        data = Data()
        server = self.bot.server
        if datetime.date(datetime.now()) >= data.resets.daily:
            data.score_today = 0

        membersTracker = server.get_channel(ids.MEMBERS_TRACKER_ID)
        scoreTodayTracker = server.get_channel(ids.SCORE_TODAY_TRACKER_ID)
        topChatterTracker = server.get_channel(ids.TOP_CHATTER_TRACKER_ID)

        await membersTracker.edit(name=f'Members: {len(server.members)}')
        await scoreTodayTracker.edit(name=f'Score today: {Data().score_today}')

        highest = 0
        user = None
        nowDate = datetime.date(datetime.now())
        for member in Data.get_all_members():
            if member.xp.daily > highest:
                highest = member.xp.daily
                user = server.get_member(member.id)

        if user == None: user = 'Not defined'
        await topChatterTracker.edit(name=f'Top chatter: {user}')

        if nowDate >= data.resets.daily:
            print('Daily reset')
            os.system('cp database.db database.db.bck')
            data.voted_users.clear()
            data.resets.daily = nowDate+timedelta(days=1)
            staff_ids = [user.id for user in server.get_role(ids.STAFF_ROLE_ID).members]
            staff_scores = {}
            for member in Data.get_all_members():
                if member.id in staff_ids:
                    staff_scores[member.id] = member.xp.daily
                member.xp.daily = 0
                member.save()

            text = ''
            ri_text = ''
            for id in staff_scores:
                passed = staff_scores[id] > 500
                if passed:
                    try:
                        data.staff_points[id] += 1
                    except:
                        data.staff_points[id] = 1

                if not id in data.report_ignored and not server.get_member(id).guild_permissions.administrator:
                    text += f'{server.get_member(id)} (<@{id}>) - `{staff_scores[id]}` -- **{"PASS ✅" if passed else "NOT PASS ❌"}**\n'
                else:
                    ri_text += f'{server.get_member(id)} (<@{id}>) - `{staff_scores[id]}`\n'
            await server.get_channel(ids.STAFF_REPORTS_CHANNEL_ID).send(f'<@&{ids.STAFF_ROLE_ID}>', embed=discord.Embed(
                color=0x00ffff,
                title=f'Staff Score Report {datetime.now().date()}',
                description=text
            ))
            await server.get_channel(ids.STAFF_REPORTS_CHANNEL_ID).send(embed=discord.Embed(
                title='Report Ignored',
                description=ri_text
            ))
        if nowDate >= data.resets.weekly:
            print('Weekly reset')
            data.resets.weekly = nowDate+timedelta(days=7-nowDate.weekday())
            for member in Data.get_all_members():
                member.xp.weekly = 0
                member.save()

            text = ''
            ri_text = ''
            for id in data.staff_points.copy():
                modif = ''
                if data.staff_points[id] < 3:
                    modif = '❌ DEMOTION'
                elif data.staff_points[id] >= 6:
                    modif = '⭐ ACTIVE'
                else:
                    modif = '✅ PASS'

                if not id in data.report_ignored and not server.get_member(id).guild_permissions.administrator:
                    text += f'{server.get_member(id)} (<@{id}>) - `{data.staff_points[id]}` days passed -- **{modif}**\n'
                else:
                    ri_text += f'{server.get_member(id)} (<@{id}>) - `{data.staff_points[id]}` days passed {"- **[[UNIGNORED SINCE TODAY]]**" if id in data.report_ignored else ""}\n'

            embed = discord.Embed(
                color=0x00ffff,
                title=f'Weekly Pass Report {datetime.now().date()}',
                description=text
            )
            report_channel = server.get_channel(ids.STAFF_REPORTS_CHANNEL_ID)
            await report_channel.send(f'<@&{ids.STAFF_ROLE_ID}>', embed=embed)
            await report_channel.send(embed=discord.Embed(
                title='Report Ignored',
                description=ri_text
            ))
            text = ''
            for i in data.staff_votes:
                text += f'{server.get_member(i)} (<@{i}>) - `{data.staff_votes[i]}` reputation points {"-- ❤️ HIGH" if data.staff_votes[i] >= 10 else ""}\n'
            await report_channel.send(embed=discord.Embed(
                title='Staff Reputation Points',
                description=text
            ))
            data.staff_points.clear()
            data.report_ignored.clear()
            data.staff_votes.clear()
            
        for channel in list(data.dm_channels.values()).copy():
            if datetime.now() >= channel.closes_at:
                await channel.close()
        data.save()

    @mainLoop.before_loop
    @localWarnsReset.before_loop
    @multiTaskLoop.before_loop
    @YoutubeDataFetcher.before_loop
    @YoutubeContentPoster.before_loop
    async def loop_waiter(self):
        await self.bot.wait_until_ready()


class SystemListeners(commands.Cog):
    def __init__(self, bot: CoreBot):
        self.bot = bot

    @commands.Cog.listener('on_ready')
    async def on_ready(self):
        self.bot.load_variables()
        print('Bot was successfully launched')
        await self.bot.change_presence(  
            status=discord.Status.dnd,
            activity=discord.Activity(name='the server', type=discord.ActivityType.watching))

    @commands.Cog.listener('on_command_error')
    async def ErrorController(self, ctx: commands.Context, error: commands.CommandError):
        error_msg = get_error_msg(ctx, error)

        if error_msg != False:
            await ctx.send(embed=embeds.error(ctx, error_msg), allowed_mentions=Mentions.NONE)

        with open('errors.txt', 'a') as f:
            f.write(format_exc()+'-'*20+'\n')

def setup(bot: CoreBot):
    for cls in (
        SystemLoops,
        SystemListeners
    ):
        bot.add_cog(cls(bot))