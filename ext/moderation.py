import discord, os, ids
from discord.ext import commands
from typing import Optional, Union
from datetime import datetime, timedelta
from modules.exceptions import StaffOnly, OwnerOnly, InvalidBlacklistMode
from modules.db_manager import Data, CoreBot, Case, Database, Youtuber
from modules.utils import td_to_str, td_to_timestamp, check_hierarchy
from modules.converters import Time, Rule
from modules.youtube import is_id_valid
from modules import embeds

class MembersModeration(commands.Cog):
    def __init__(self, bot: CoreBot):
        self.bot = bot

    def cog_check(self, ctx: commands.Context):
        cond = self.bot.staff in ctx.author.roles
        if not cond: raise StaffOnly()
        return True

    @commands.command(
        name='mute',
        description='Mutes the user for a certain time',
        usage='//mute <user> <time> <rule index>')
    async def mute(self, ctx: commands.Context, user: discord.Member, time: Optional[Time], rule: Rule):
        check_hierarchy(ctx.author, user)
        data = Data()
        await ctx.message.delete()
        if not self.bot.muted in user.roles:
            await self.bot.add_case(Case(user.id, 'mute', ctx.author.id, time, rule.text))
            await user.add_roles(self.bot.muted, reason=f'Responsible user: {ctx.author} \
| Time: {td_to_str(time)} | Rule: {rule.index}')
            await ctx.send(embed=embeds.success(ctx, 'Action Applied', f'**{user}** \
({user.mention}) was muted for `{td_to_str(time)}` (until {td_to_timestamp(time)})\n\
Violated rule: **{rule.index}. {rule}**', footer_user=user))
            
        else:
            await ctx.send(embed=embeds.error(ctx, f'{user.mention} is already muted'))

    @commands.command(   
        name='unmute',
        description='Unmutes the user',
        usage='//unmute <user>')
    async def unmute(self, ctx, *, user: discord.Member):
        check_hierarchy(ctx.author, user)
        if self.bot.muted in user.roles:
            await user.remove_roles(self.bot.muted, reason=f'Responsible user: {ctx.author}')
            await ctx.send(embed=embeds.success(ctx, 'Action Applied', 
            f'**{user}** ({user.mention}) was unmuted'))
            await self.bot.logCase(Case(user.id, 'unmute', ctx.author.id, None, 'Not specified'))
        else:
            await ctx.send(embed=embeds.error(ctx, f'{user.mention} is not muted'))

    @commands.command(   
        name='filemute',
        aliases=['fm'],
        description='Removes permission to attach files for a user',
        usage='//filemute <user> <time>')
    async def filemute(self, ctx, user: discord.Member, time: Time):
        check_hierarchy(ctx.author, user)
        if not self.bot.filemuted in user.roles:
            await ctx.message.delete()
            new_case = Case(user.id, 'filemute', ctx.author.id, time, 'Inappropriate images')
            Data().add_case(new_case)
            await self.bot.logCase(new_case)
            await user.add_roles(self.bot.filemuted)
            try:
                await user.send(embed=embeds.warning(user, f'You were filemuted in {self.bot.server.name}', f'Your permission to attach \
files was removed for `{td_to_str(time)}` (until {td_to_timestamp(time)}). It is probably because you broke one of \
our rules by posting inappropriate images/videos.', footer_user=user))
            except: pass

            await ctx.send(embed=embeds.success(ctx, 'Action Applied', f'**{user}** ({user.mention}) was \
filemuted for `{td_to_str(time)}` (until {td_to_timestamp(time)})', footer_user=user))
        else:
            await ctx.send(f'{user.mention} is already filemuted')

    @commands.command(   
        name='unfilemute',
        aliases=['unfm'],
        description='Unfilemutes the user',
        usage='//unfilemute <user>')
    async def unfilemute(self, ctx, user: discord.Member):
        check_hierarchy(ctx.author, user)
        if self.bot.filemuted in user.roles:
            await user.remove_roles(self.bot.filemuted, reason=f'Responsible user: {ctx.author}')
            await ctx.send(embed=embeds.success(ctx, 'Action Applied', f'**{user}** ({user.mention}) was unfilemuted'))
            await self.bot.logCase(Case(user.id, 'unfilemute', ctx.author.id, None, 'Not specified'))

        else:
            await ctx.send(f'{user.mention} is not filemuted')


    @commands.command(   
        name='ban',
        description='Bans user',
        usage='//ban <user> <time> <rule index>')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, user: discord.Member, time: Optional[Time], rule: Rule):
        check_hierarchy(ctx.author, user)
        await ctx.message.delete()
        try:
            await user.send(embed=embeds.base_embed(ctx,
                color=0xff0000,
                title=f'🔨 You were banned from {self.bot.server.name}',
                description=f'Violated rule: **{rule.index}. {rule}**\n\
Responsible moderator: **{ctx.author}**\n\
Time: `{td_to_str(time)}` (until {td_to_timestamp(time)})', footer_user=user
            ))
        except: pass

        await self.bot.add_case(Case(user.id, 'ban', ctx.author.id, time, rule.text))
        await user.ban(reason=f'Responsible user: {ctx.author} | Time: {td_to_str(time)} | Rule: {rule.index}')
        await ctx.send(embed=embeds.success(ctx, 'Action Applied', f'**{user}** ({user.id}) was banned\n\
Time: `{td_to_str(time)}` (until {td_to_timestamp(time)})\n\
Violated rule: **{rule.index}. {rule}**'))

    @commands.command(   
        name='kick',
        description='Kicks user',
        usage='//kick <user> <rule index>')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, user: discord.Member, rule: Rule):
        check_hierarchy(ctx.author, user)
        await ctx.message.delete()
        try:
            await user.send(embed=embeds.warning(ctx, f'You were kicked from {self.bot.server.name}', f'Violated rule: **{rule.index}. {rule}**\n\
Responsible moderator: **{ctx.author}**\n', footer_user=user))
        except: pass

        await self.bot.add_case(Case(user.id, 'kick', ctx.author.id, None, rule.text))
        await user.kick(reason=f'Responsible user: {ctx.author} | Rule: {rule.index}')
        await ctx.send(embed=embeds.success(ctx, 'Action Applied', f'**{user}** ({user.id}) was kicked\n\
Violated rule: **{rule.index}. {rule}**', footer_user=user))

    @commands.command(   
        name='setnick',
        aliases=['nick', 'nickname'],
        description='Changes user\'s nickname',
        usage='//nick <user> [new nickname (leave empty to reset)]')
    async def setnick(self, ctx, user: discord.Member, *, newNick=None):
        check_hierarchy(ctx.author, user)
        await ctx.message.delete()
        await user.edit(nick=newNick)
        if newNick == None:
            desc = 'was reset'
        else:
            desc = f'was set to **{newNick}**'
        await ctx.send(embed=embeds.success(ctx, 'Action Applied', f'**{user}**\'s nickname {desc}'))

    @commands.command(   
        name='addrole',
        description='Adds a role to the user',
        usage='//addrole <user> <role>')
    @commands.has_permissions(manage_roles=True)
    async def addrole(self, ctx, user: discord.Member, *, role: discord.Role):
        check_hierarchy(ctx.author, user)
        if role.position >= ctx.author.top_role.position:
            await ctx.send(embed=embeds.error(ctx, 'You cannot assign a role that is higher than your top one'))
        await user.add_roles(role, reason=f'Responsible moderator: {ctx.author}')
        await ctx.send(embed=discord.Embed(
            color=0x00ff00,
            title='✅ Action applied',
            description=f'**{user}** ({user.mention}) was given **{role.name}**'
        ))

    @commands.command(   
        name='removerole',
        description='Removes a role from the user',
        usage='//removerole <user> <role>')
    @commands.has_permissions(manage_roles=True)
    async def removerole(self, ctx, user: discord.Member, *, role: discord.Role):
        check_hierarchy(ctx.author, user)
        if role.position >= ctx.author.top_role.position:
            await ctx.send(embed=embeds.error(ctx, 'You cannot remove a role that is higher than your top one'))

        await user.remove_roles(role, reason=f'Responsible moderator: {ctx.author}')
        await ctx.send(embed=discord.Embed(
            color=0xffff00,
            title='✅ Action applied',
            description=f'Removed **{role}** from **{user}**'
        ))


class WarningsManagement(commands.Cog):
    def __init__(self, bot: CoreBot):
        self.bot = bot

    def cog_check(self, ctx: commands.Context):
        cond = self.bot.staff in ctx.author.roles
        if not cond: raise StaffOnly()
        return True

    @commands.command(   
        name='warn',
        description='Warns a user',
        usage='//warn <user> <rule index>')
    async def warn(self, ctx, user: discord.Member, rule: Rule):
        await self.bot.add_case(Case(user.id, 'warn', ctx.author.id, None, rule.text))
        member_data = Data.get_member(user.id)
        await ctx.send(embed=embeds.success(ctx, 'Warning Assigned', f'**{user}** ({user.mention}) was warned.\n\
Violated rule: **{rule.index}. {rule}**\n\n\
*Warnings for this rule: `{len(member_data.get_all_warns_with_reason(rule.text))}`*\n\
*Total warnings: `{len(member_data.get_all_warns())}`*'))
        try:
            await user.send(embed=embeds.warning(ctx, f'You were warned in {self.bot.server.name}',
            f'Violated rule: **{rule.index}. {rule}**\n\
Responsible moderator: **{ctx.author}**\n', footer_user=user))
        except: pass

    @commands.command(   
        name='warns',
        aliases=['warnings', 'infractions'],
        description='Shows user\'s warnings',
        usage='//warns <user>')
    async def warns(self, ctx, *, user: discord.Member):
        memberData = Data.get_member(user.id)
        warns = memberData.get_all_warns()
        if len(warns) > 0:
            embed = discord.Embed(
                color=0xffff00,
                title=f'Warnings for {user}',
                description=f'**{len(warns)} warning(s) found**'
            )
            for warn in warns:
                embed.add_field(name=f'#{warn.id} {warn.applied_at}',
                                value=f'Responsible moderator: **{self.bot.server.get_member(warn.responsible_id)}**\n\
Violated rule: **{warn.reason}**')
            embed.set_footer(text=str(user), icon_url=user.avatar_url)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f'No warnings found!')

    @commands.command(   
        name='delwarn',
        aliases=['removewarn', 'dw'],
        description='Removes the warning for the user',
        usage='//delwarn <warnID>')
    async def delwarn(self, ctx, warnID: int):
        try:
            Data.get_case(warnID).delete()
            await ctx.send(f'Successfully removed warning `#{warnID}`')
        except Exception as e:
            await ctx.send(f'I couldn\'t find the warning `#{warnID}`. Error:\n```{e}```')

    @commands.command(   
        name='delwarns',
        aliases=['clearwarns', 'clearwarn'],
        description='Removes ALL warnings for the user',
        usage='//delwarns <user>')
    async def delwarns(self, ctx, user: discord.Member):
        amount = len(Data.get_member(user.id).get_all_warns())
        if amount > 0:
            Database('database').get_table('cases').delete(type='warn', target_id=user.id)
            await ctx.send(embed=embeds.success(ctx, 'Warnings Removed', f'Deleted {amount} warning(s) from **{user}**'))
        else:
            await ctx.send(f'No warnings found!')

class ChannelModeration(commands.Cog):
    def __init__(self, bot: CoreBot):
        self.bot = bot

    def cog_check(self, ctx: commands.Context):
        cond = self.bot.staff in ctx.author.roles
        if not cond: raise StaffOnly()
        return True

    @commands.command(   
        name='lock',
        description='Locks a channel for an indefinite time',
        usage='//lock [channel]')
    async def lock(self, ctx, channel: Optional[discord.TextChannel]):
        if channel == None: channel = ctx.channel
        if not channel.permissions_for(ctx.author).manage_messages:
            raise commands.MissingPermissions(['manage messages'])
        perms = channel.overwrites
        perms[ctx.guild.default_role].update(send_messages=False)
        await channel.edit(overwrites=perms)
        await ctx.send(embed=embeds.base_embed(ctx,
            color=0x0000ff,
            title='🔒 Channel locked',
            description=f'{channel.mention} was locked'
        ))

    @commands.command(   
        name='unlock',
        description='Unlocks a locked channel',
        usage='//unlock [channel]')
    async def unlock(self, ctx, channel: Optional[discord.TextChannel]):
        if channel == None: channel = ctx.channel
        if not channel.permissions_for(ctx.author).manage_messages:
            raise commands.MissingPermissions(['manage messages'])
        perms = channel.overwrites
        perms[ctx.guild.default_role].update(send_messages=None)
        await channel.edit(overwrites=perms)
        await ctx.send(embed=embeds.base_embed(ctx,
            color=0x0000ff,
            title='🔓 Channel unlocked',
            description=f'{channel.mention} was unlocked'
        ))

    @commands.command(   
        name='purge',
        aliases=['clear', 'p'],
        description='Clears certain amount of message in channel\'s history',
        usage='//purge [channel] [user] <amount>')
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx,
                    channel: Optional[discord.TextChannel],
                    user: Optional[discord.Member],
                    amount: int):
        await ctx.message.delete()
        if channel == None:
            channel = ctx.channel
        if user == None:
            def check(m):
                return not m.pinned
        else:
            def check(m):
                return not m.pinned and m.author.id == user.id

        messages = await channel.purge(limit=amount, check=check)
        await ctx.send(f'Successfully deleted `{len(messages)}` messages from {channel.mention}', delete_after=3)

    @commands.command(   
        name='purgetill',
        aliases=['pt'],
        description='Clears all messages after replied one',
        usage='//purgetill {reply to msg}')
    @commands.has_permissions(manage_messages=True)
    async def purgetill(self, ctx: commands.Context):
        msg = ctx.message.reference.resolved

        def check(m):
            return not m.pinned
        await ctx.channel.purge(after=msg.created_at, check=check)

    @commands.command(
        name='slowmode',
        aliases=['sm'],
        description='Sets the slowmode for the channel. Leave `[slowmode]` empty to disable it',
        usage='//sm [channel] [slowmode]'
    )
    async def slowmode(self, ctx: commands.Context, channel: Optional[discord.TextChannel], delay: Optional[Time]):
        if channel == None: channel = ctx.channel
        sm_delay = int(delay.total_seconds()) if delay != None else 0
        if sm_delay > 21600:
            await ctx.send(embed=embeds.error(ctx, 'The slowmode cannot be higher than 6 hours'))
            return
        await channel.edit(slowmode_delay=sm_delay)
        await ctx.send(embed=embeds.success(ctx, 'Action Applied', f'Slowmode in {channel.mention} was \
{"reset" if delay == 0 else "set to " + str(delay)}'))


class ServerModeration(commands.Cog):
    def __init__(self, bot: CoreBot):
        self.bot = bot

    def cog_check(self, ctx: commands.Context):
        cond = self.bot.staff in ctx.author.roles
        if not cond: raise StaffOnly()
        return True

    @commands.command(   
        name='lockserver',
        description='Locks a server immediately. Needs to be activated by at least 3 staff members or an admin',
        usage='//lockserver')
    async def lockserver(self, ctx):
        m = await ctx.send(embed=discord.Embed(
            color=0xffff00,
            title='⚠️ Confirm server locking',
            description='At least **3** of staff members or an admin need to react'
        ))
        await m.add_reaction('✅')

        reacted = []
        def check(r, u):
            return r.message.id == m.id and str(r.emoji) == '✅' and self.bot.staff in u.roles \
                and not u in reacted and u.id != self.bot.user.id
        try:
            while len(reacted) < 3:
                _, u = await self.bot.wait_for('reaction_add', check=check, timeout=30)
                if u.guild_permissions.administrator: break
                else:
                    reacted.append(u)
            await m.delete()

            channels = [channel for channel in ctx.guild.text_channels if channel.type != discord.ChannelType.category and \
                channel.overwrites_for(self.bot.server.default_role).send_messages != False]
            amount = len(channels)
            m = await ctx.send(f'Locking channels... (0/{amount})')
            edit_at = datetime.now() + timedelta(seconds=3)
            completed = 0
            for channel in channels:
                perms = channel.overwrites
                try:
                    perms[ctx.guild.default_role].update(send_messages=False)
                except KeyError:
                    perms[ctx.guild.default_role] = discord.PermissionOverwrite(send_messages=False)
                await channel.edit(overwrites=perms)
                completed += 1
                if datetime.now() >= edit_at:
                    await m.edit(content=f'Locking channels... ({completed}/{amount})')
                    edit_at = datetime.now() + timedelta(seconds=3)

            data = Data()
            data.locked_channels = [channel.id for channel in channels]
            data.save()
            await m.delete()
            await ctx.send('Operation completed')

        except TimeoutError:
            await m.delete()
            await ctx.send(f'Didn\'t get response in time, operation cancelled', delete_after=3)

    @commands.command(   
        name='unlockserver',
        description='Unlocks locked channels that were locked while serverlock',
        usage='//unlockserver')
    async def unlockserver(self, ctx):
        channels = []
        data = Data()
        for id in data.locked_channels:
            channel = self.bot.server.get_channel(id)
            if channel != None and channel.overwrites_for(self.bot.server.default_role).send_messages == False: channels.append(channel)
        amount = len(channels)
        m = await ctx.send(f'Unlocking channels... (0/{amount})')
        edit_at = datetime.now() + timedelta(seconds=3)
        completed = 0
        for channel in channels:
            perms = channel.overwrites
            try:
                perms[ctx.guild.default_role].update(send_messages=None)
            except KeyError:
                perms[ctx.guild.default_role] = None
            await channel.edit(overwrites=perms)
            completed += 1
            if datetime.now() >= edit_at:
                await m.edit(content=f'Unlocking channels... ({completed}/{amount})')
                edit_at = datetime.now() + timedelta(seconds=3)

        data.locked_channels.clear()
        data.save()
        await m.delete()
        await ctx.send('Operation completed')

    @commands.command(   
        name='assignselfrole',
        aliases=['asr'],
        description='Assigns a role as a selfrole to a member',
        usage='//asr <member> <role>')
    @commands.has_permissions(administrator=True)
    async def assignSelfRole(self, ctx, user: discord.Member, role: discord.Role):
        memberData = Data.get_member(user.id)
        memberData.selfrole = role.id
        memberData.save()
        await ctx.send(embed=embeds.success(ctx, 'Action Applied', f'Assigned {role.mention} as a selfrole of **{user}** ({user.mention})'))

    @commands.command(   
        name='deleteselfrole',
        aliases=['delselfrole', 'removeselfrole', 'dsr', 'delself'],
        description='Removes a selfrole from a user if they have one',
        usage='//dsr <user>')
    @commands.has_permissions(administrator=True)
    async def deleteSelfRole(self, ctx, user: discord.Member):
        memberData = Data.get_member(user.id)
        if memberData.selfrole == None:
            await ctx.reply(f'They don\'t have a selfrole assigned')
        else:
            memberData.selfrole = None
            memberData.save()
            await ctx.send(embed=embeds.embed(ctx, '✅ Action applied', f'Removed selfrole from **{user}** ({user.mention})'))

    @commands.group(
        name='reactionrole',
        description='Module for managing reaction roles',
        aliases=['rr'],
        usage='//rr <subcommand>'
    )
    @commands.has_guild_permissions(manage_guild=True)
    async def reactionrole(self, ctx):
        if ctx.invoked_subcommand == None:
            pass

    @reactionrole.command(
        name='add',
        description='Adds a reaction role',
        usage='//rr add [channel] <message_id> <emoji> <role>'
    )
    async def rr_add(self, ctx, channel: Optional[discord.TextChannel], message_id: int, emoji: Union[discord.Emoji, str], role: discord.Role):
        if channel == None:
            channel = ctx.channel

        try:
            message = await channel.fetch_message(message_id)
        except:
            await ctx.send(embed=discord.Embed(
                color=0xff0000,
                title='Error',
                description=f'Couldn\'t find that message in channel {channel.mention}'
            ))
            return

        Data().create_reaction_role(message_id, getattr(emoji, 'id', str(emoji)), role.id)
        await message.add_reaction(emoji)
        await ctx.send(f'Reaction role added successfully')

    @reactionrole.command(
        name='remove',
        description='Removes a single existing reaction role',
        usage='//rr remove <message_id> <emoji>'
    )
    async def rr_remove(self, ctx, message_id: int, emoji: discord.Emoji):
        try:
            data = Data()
            data.reaction_roles[message_id].pop(getattr(emoji, 'id', str(emoji)))
            data.save()
            await ctx.send(f'Reaction role removed successfully')
        except:
            await ctx.send('That reaction role doesn\'t exist')

    @reactionrole.command(
        name='removeall',
        description='Removes __**all**__ reaction roles from the message',
        usage='//rr removeall <message_id>'
    )
    async def rr_removeall(self, ctx, message_id: int):
        try:
            data = Data()
            data.reaction_roles.pop(message_id)
            data.save()
            await ctx.send(f'Reaction roles removed successfully')
        except:
            await ctx.send('Seems like there are no reaction roles connected to that message')

    @commands.group( 
        name='blacklist',
        aliases=['bl'],
        description='Commands module for operating with blacklisted expressions.\n\
Available subcommands: `add, remove`')
    async def blacklist(self, ctx):
        if ctx.invoked_subcommand == None:
            embed = embeds.base_embed(ctx,
                color=0xff0000,
                title='Blacklisted expressions',
                description='**Common** - scans every single word for match ignoring special characters\n\
**Wildcard** - scans entire text for match ignoring special characters\n\
**Super** - scans entire text for math ignoring special characters AND spaces'
            )
            data = Data()
            commons = '` `'.join(data.blacklist.common)
            wilds = '` `'.join(data.blacklist.wildcard)
            supers = '` `'.join(data.blacklist.super)
            embed.add_field(name='Common', value=f'`{commons}`')
            embed.add_field(name='Wildcard', value=f'`{wilds}`')
            embed.add_field(name='Super', value=f'`{supers}`')
            await ctx.send(embed=embed)

    @blacklist.command( 
        name='add',
        description='Adds a word/expression to blacklist',
        usage='//blacklist add <mode> <expression>')
    async def blacklist_add(self, ctx, mode, *, word):
        await ctx.message.delete()
        data = Data()
        d = {'common': data.blacklist.common,
            'wild': data.blacklist.wildcard,
            'super': data.blacklist.super}
        if not mode in d: raise InvalidBlacklistMode()
        blacklistData = d[mode]
        if word in blacklistData:
            await ctx.send(f'This word is already in {mode} blacklist!')
        else:
            blacklistData.append(word)
            data.save()
            await ctx.send(embed=embeds.success(ctx, 'Action Applied', f'**{word}** was added to {mode} blackllist'),
            delete_after=3)

    @blacklist.command( 
        name='remove',
        description='Removes a word/expresssion from blacklist',
        usage='//blacklist remove <mode> <expression>')
    async def blacklist_remove(self, ctx, mode, *, word):
        data = Data()
        await ctx.message.delete()
        d = {'common': data.blacklist.common,
            'wild': data.blacklist.wildcard,
            'super': data.blacklist.super}
        if not mode in d: raise InvalidBlacklistMode()
        blacklistData = d[mode]
        if not word in blacklistData:
            await ctx.send(f'This word is not in {mode} blacklist!')
        else:
            blacklistData.remove(word)
            data.save()
            await ctx.send(embed=embeds.success(ctx, 'Action Applied', f'**{word}** was removed from {mode} blackllist'),
            delete_after=3)


class OtherModeration(commands.Cog):
    def __init__(self, bot: CoreBot):
        self.bot = bot

    def cog_check(self, ctx: commands.Context):
        cond = self.bot.staff in ctx.author.roles
        if not cond: raise StaffOnly()
        return True

    @commands.command(
        name='checkyt',
        description='Checks if the member was notified by a staff member',
        usage='//checkyt <id>'
    )
    async def checkyt(self, ctx, id: int):
        if id in Data().notified_youtubers:
            await ctx.send(f'That youtuber is **already notified**')
        else: 
            await ctx.send(f'That youtuber is **not notified**')

    @commands.command(
        name='claimyt',
        description='Marks the youtuber as notified',
        usage='//claimyt <id>'
    )
    async def claimyt(self, ctx, id: int):
        data = Data()
        if id in data.notified_youtubers:
            await ctx.send(f'That youtuber is **already notified**')
        else:
            data.notified_youtubers.append(id)
            data.save()
            await ctx.send(f'Added new youtuber')

    @commands.command(   
        name='delafk',
        aliases=['deleteafk', 'resetafk', 'removeafk'],
        description='Resets user\'s AFK',
        usage='//delafk <user>')
    async def delafk(self, ctx, user: discord.Member):
        memberData = Data.get_member(user.id)
        memberData.afk = None
        memberData.save()
        await ctx.send(embed=embeds.success(ctx, 'Action Applied', f'Reset **{user}**\'s AFK'
        ))

    @commands.command(
        name='deletebackground',
        aliases=['delbg', 'rmbg'],
        description='Resets the background for a member',
        usage='//rmbg <user>'
    )
    async def deletebackground(self, ctx, user: discord.Member):
        try:
            os.remove(Data.get_member(user.id).get_bg())
        except: pass
        await ctx.send(f'Successfully reset the background for {user.mention}')

    @commands.command(
        name='revive',
        description='Pings chat revive',
        usage='//revive [text]'
    )
    @commands.cooldown(1, 3600, commands.BucketType.guild)
    async def revive(self, ctx, *, text = None):
        await ctx.message.delete()
        await ctx.send(f'<@&{ids.CHAT_REVIVE_ROLE_ID}> {text}')

    
class OwnerOnlyModeration(commands.Cog):
    def __init__(self, bot: CoreBot):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context):
        cond = await self.bot.is_owner(ctx.author)
        if not cond: raise OwnerOnly()
        return True

    @commands.command(
        name='addyoutuber',
        aliases=['addyt'],
        description='Adds a youtuber to the advertisable',
        usage='//addyt <user> <youtube_id> <is_premium{true|false}>'
    )
    async def addyoutuber(self, ctx, user: discord.Member, youtube_id, is_premium: bool):
        if is_id_valid(youtube_id):
            Youtuber(user.id, youtube_id, is_premium).save()
            await ctx.send(f'Successfully added {user.mention} to the content creators program')
        else:
            await ctx.send(f'Invalid channel ID')

    @commands.command(
        name='removeyoutuber',
        aliases=['rmyt', 'removeyt'],
        description='Removes a youtuber from advertisable',
        usage='//rmyoutuber <user>'
    )
    async def removeyoutuber(self, ctx, user: discord.Member):
        try:
            Data.get_youtuber(user.id).delete()
            await ctx.send(f'Successfully deleted {user.mention} from youtubers')
        except:
            await ctx.send(f'{user.mention} is not a youtuber')

    @commands.command(   
        name='reportignore',
        aliases=['ri'],
        description='Excludes user form being shown in staff activity reports',
        usage='//ri <user>')
    async def reportignore(self, ctx, user: discord.Member):
        data = Data()
        data.report_ignored.append(user.id)
        data.save()
        await ctx.send(f'{user.mention} will not be shown in staff activity reports until the next weekly reset')

    @commands.command(   
        name='unreportignore',
        aliases=['unri'],
        description='Adds user back to staff activity reports',
        usage='//unri <user>')
    async def unreportignore(self, ctx, user: discord.Member):
        try:
            data = Data()
            data.report_ignored.remove(user.id)
            data.save()
            await ctx.send(f'{user.mention} will now be shown in staff activity reports again')
        except: 
            await ctx.send(f'This user is not report ignored')

def setup(bot: CoreBot):
    for cls in (
        MembersModeration,
        WarningsManagement,
        ChannelModeration,
        ServerModeration,
        OtherModeration,
        OwnerOnlyModeration
    ):
        bot.add_cog(cls(bot))