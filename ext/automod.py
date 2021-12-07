import discord, requests, ids
from discord.ext import commands
from modules.db_manager import CoreBot, Data, Case, ASMTracker
from modules.utils import checkword, checkprint, antispam
from modules.embeds import success
from base64 import urlsafe_b64encode
from datetime import datetime

class AutomodListeners(commands.Cog):
    def __init__(self, bot: CoreBot):
        self.bot = bot
        self.asmTracker = ASMTracker()

    @commands.Cog.listener('on_message')
    async def AutomodController(self, msg: discord.Message):
        data = Data()
        event_manager = self.bot.server.get_role(ids.EVENT_MANAGER_ROLE_ID) #type: discord.Role
        if msg.channel.type != discord.ChannelType.private and not msg.author.bot:
            try:
                adminperm = msg.author.guild_permissions.administrator
            except:
                adminperm = False
            if not adminperm:
                check = checkword(msg.content)

                #links filter
                for word in msg.content.split():
                    if any([word.startswith(i) for i in (
                        'http://', 
                        'https://', 
                        'https://discord.com', 
                        'https://discord.gg')]) and word not in ('https://', 'http://'):
                        linksafe = True
                        if not word in data.normal_links and not word in data.bad_links:
                            link = urlsafe_b64encode(word.encode()).decode().strip('=')
                            headers = {'x-apikey': ids.VIRUSTOTAL_APIKEY}
                            try:
                                r = requests.get(f'https://www.virustotal.com/api/v3/urls/{link}', headers=headers).json()['data']['attributes']['last_analysis_stats']
                                if r['malicious'] > 0 or r['suspicious'] > 0:
                                    linksafe = False
                            except:
                                requests.post(f'https://www.virustotal.com/api/v3/urls', data={'url': word}, headers=headers)
                                try:
                                    r = requests.get(f'https://www.virustotal.com/api/v3/urls/{link}', headers=headers).json()['data']['attributes']['last_analysis_stats']
                                    if r['malicious'] > 0 or r['suspicious'] > 0:
                                        linksafe = False
                                except: pass
                            if linksafe:
                                data.normal_links.append(word)
                                data.save()

                        if not linksafe:
                            data.bad_links.append(word)
                            data.save()

                        if word in data.bad_links:
                            try:
                                try:
                                    await msg.author.send(embed=discord.Embed(
                                        color=0xff0000,
                                        title=f'You were banned from {self.bot.server.name}',
                                        description='Reason: posting malicious link'
                                    ))
                                except: pass
                                await msg.author.ban(reason='Malicious link')
                                await self.bot.add_case(Case(msg.author.id, 'ban', self.bot.user.id, None, 'Malicious link'))
                            except: pass



                #font filter
                if checkprint(msg.content) == False and not self.bot.staff in msg.author.roles and not msg.channel.id == ids.ANNOUNCEMENTS_CHANNEL_ID:
                    try:
                        await msg.delete()
                    except: pass
                    await msg.channel.send(embed=discord.Embed(
                        color=0xff0000,
                        title='❌ Message blocked',
                        description=f"{msg.author.mention}, please do not use symbols outside A-Z, \
a-z, 0-9 and default special symbols in your messages"), delete_after=3)

                #words filter
                elif not check[0] and not msg.channel.id == ids.ANNOUNCEMENTS_CHANNEL_ID:
                    try:
                        await msg.delete()
                    except: pass
                    try:
                        self.bot.local_warns[msg.author.id] += 1
                        await self.bot.updateLocalWarns(msg.author.id)
                    except KeyError:
                        self.bot.local_warns[msg.author.id] = 1
                    warnsBeforeMute = 3-self.bot.local_warns[msg.author.id]
                    if warnsBeforeMute <= 0:
                        warnsBeforeMute = 'muted'
                    embed = discord.Embed(
                        color=0xff0000,
                        title='❌ Message blocked',
                        description=f'Message by **{msg.author}** ({msg.author.mention}) was blocked for containing blacklisted word(s)\n\
Warnings before mute: `{warnsBeforeMute}`\n\
Warnings reset in `{(self.bot.next_reset-datetime.now()).seconds//60} minutes`') 
                    await msg.channel.send(embed=embed, delete_after=3)
                    await msg.channel.send(embed=discord.Embed(
                        color=0xff0000,
                        title='Blocked content',
                        description=check[1]
                    ), delete_after=5)

                #spam filter
                elif not antispam(msg.content)[0] and not msg.channel.id in ids.ANTISPAM_IGNORED and not event_manager in msg.author.roles:
                    try:
                        await msg.delete()
                    except: pass

    @commands.Cog.listener('on_message')
    async def ASMController(self, msg: discord.Message):
        if msg.channel.type != discord.ChannelType.private and not msg.author.bot:
            if self.asmTracker.enabled and msg.channel.id == ids.GENERAL_CHANNEL_ID:
                general = self.bot.server.get_channel(ids.GENERAL_CHANNEL_ID)
                self.asmTracker.messages += 1
                if datetime.now() >= self.asmTracker.reset:
                    sm = general.slowmode_delay
                    newslowmode = None
                    d = {range(0, 11): 3,
                        range(11, 16): 5,
                        range(16, 21): 7,
                        range(21, 31): 15,
                        range(31, 41): 30,
                        range(50, 500): 600}
                    n = self.asmTracker.messages
                    for i in d:
                        if n in i:
                            newslowmode = d[i]
                            break
                    if newslowmode == None:
                        newslowmode = 600

                    if newslowmode < sm:
                        self.asmTracker.before_down -= 1
                        if self.asmTracker.before_down <= 0:
                            await general.edit(slowmode_delay=newslowmode)
                            self.asmTracker.before_down = 3
                    else:
                        await general.edit(slowmode_delay=newslowmode)
                        self.asmTracker.before_down = 3

                    self.asmTracker.update()

    @commands.Cog.listener('on_message_edit')
    async def EditedController(self, before, after):
        await self.AutomodController(after)

    @commands.command(   
        name='autoslowmode',
        aliases=['asm'],
        description='Enables/disables autoslowmode for general',
        usage='//asm')
    @commands.has_permissions(administrator=True)
    async def autoslowmode(self, ctx):
        asmTracker = self.asmTracker
        asmTracker.enabled = not asmTracker.enabled
        d = {True: 'enabled', False: 'disabled'}
        await ctx.send(embed=success(ctx, 'Action applied', f'Autoslowmode was successfully `{d[asmTracker.enabled]}`'
        ))

def setup(bot: CoreBot):
    bot.add_cog(AutomodListeners(bot))