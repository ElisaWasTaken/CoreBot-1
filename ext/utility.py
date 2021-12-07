import discord, os, ids
from discord.ext import commands
from asyncio import sleep
from typing import Optional, Union
from datetime import datetime, timedelta
from requests import get as http_get
from py_expression_eval import Parser
from youtube_dl import YoutubeDL
from modules.exceptions import PermissionDenied
from modules.db_manager import Data, CoreBot, DMChannel, Track
from modules.utils import addReactions, is_dj
from modules.converters import Rule
from modules import embeds
from random import choice
from PIL import Image

queue = []
now_playing = None

class Entertainment(commands.Cog):
    def __init__(self, bot: CoreBot):
        self.bot = bot

    @commands.command(   
        name='bitcoin',
        aliases=['bc', 'btc'],
        description='Shows bitcoin course',
        usage='//btc')
    @commands.cooldown(1, 300, type=commands.BucketType.guild)
    async def bitcoin(self, ctx):
        m = await ctx.send('Requesting bitcoin information...')
        await m.edit(embed=embeds.base_embed(ctx,
            color=discord.Color.random(),
            title=f'Current bitcoin course',
            description=f'1 BTC = `{http_get("https://blockchain.info/ticker").json()["USD"]["15m"]}` USD'))

    @commands.command(   
        name='rickroll',
        description='Sends a fake nitro to user and edits it to rickroll emoji',
        usage='//rickroll <user>')
    @commands.cooldown(1, 10, type=commands.BucketType.member)
    async def rickroll(self, ctx, victim: discord.Member):
        await ctx.message.delete()
        try:
            m = await victim.send("https://discord.gift/pSdh5vOMwvZmy62j4 here's ur free nitro man!")
            await m.edit(content="||NEVER GONNA GIVE YOU UP||")
            await ctx.send(f"{ctx.author.mention} rickrolled em :wik:")
        except:
            ctx.command.reset_cooldown(ctx)
            await ctx.send(f"{ctx.author.mention} they have DMs closed LOLLLLL")

    @commands.command(   
        name='hack',
        description='Hacks user',
        usage='//hack <user>')
    @commands.cooldown(1, 10, type=commands.BucketType.member)
    async def hack(self, ctx, victim: discord.Member):
        alg = [ f"Getting {victim.mention}'s token...",
                f"Finding weird stuff in discriminator {victim.discriminator}...",
                f"Searching {victim.name} at Pentagon databases...",
                "Hacking account data...",
                f"Email: {victim.name.lower()+choice(['@yahoo.com', '@gmail.com', '@pp.com'])}\n\
Password: {choice(['koolkid69420', '12345678', 'brawlstars'])}",
                "Reporting account to Discord...",
                "Finding favourite emoji...",
                str(choice(self.bot.server.emojis)),
                "Sending test message..."]
        m = await ctx.send("Starting hacking...")
        for text in alg:
            await sleep(1)
            await m.edit(content=text)
        try:
            m2 = await victim.send("free nitro for u! https://discord.gift/ib8H7yha7UHs2bK99o")
            await m2.edit(content="||NEVER GONNA GIVE YOU UP||")
            await m.edit(content="Message sent successfully")
        except:
            await m.edit(content="They have DMs closed, what a noob")

        alg = [ "Finding out most common word...",
                choice(["poop", "aloha", "* moan *", "cheeze", "LMAO"]),
                "Finding their girlfriend :smirk:...",
                f"{victim.name}'s gf is {choice([user for user in self.bot.server.members if user.status != discord.Status.offline]).mention}",
                "Banning pg account...",
                "Sending parcel with vodka to their address...",
                f"Hack for **{victim.name}** is completed"]
        for text in alg:
            await sleep(1)
            await m.edit(content=text)
        
        await ctx.send(f"Hack for **{victim.name}** is completed", delete_after=3)
        await sleep(3)
        await m.delete()
        await ctx.message.delete()

    @commands.command(   
        name='gf',
        aliases=['egirl', 'egirls', 'girlfriend'],
        description='Looks for a girlfriend for user',
        usage='//gf [user]')
    @commands.cooldown(1, 10, type=commands.BucketType.member)
    async def gf(self, ctx, victim: Optional[discord.Member]):
        if victim == None: victim = ctx.author
        m = await ctx.send(f"Looking for a gf for {victim.mention}")
        await sleep(3)
        members = [member for member in self.bot.server.members if member.status != discord.Status.offline]
        await m.edit(content=f"{victim.name}'s gf is {choice(members).mention} :heart:", delete_after=5)

    @commands.command(   
        name="1v1",
        description='Looks for opponents for 1v1',
        usage='//1v1')
    @commands.cooldown(1, 10, type=commands.BucketType.channel)
    async def _1v1(self, ctx):
        fighters = []
        messages = []
        timeout = datetime.now()+timedelta(minutes=1)
        m = await ctx.send(
            embed=discord.Embed(color=discord.Color.random(),
            title=f'{ctx.author} is looking for someone to 1v1!',
            description=f'React with ⚔️ if you would like to 1v1 them')
        )
        await m.add_reaction('⚔️')
        def check(reaction, user):
            return not user in fighters and str(reaction.emoji) == '⚔️' and reaction.message == m and user != self.bot.user
        while len(fighters) < 5 and timeout > datetime.now():
            try:
                _, user = await self.bot.wait_for('reaction_add', check=check, timeout=20)
                m2 = await ctx.send(f'{user.mention} wants to 1v1 {ctx.author.mention}!')
                fighters.append(user)
                messages.append(m2)
            except TimeoutError: break
        await ctx.channel.delete_messages(messages)
        await m.delete()
        if len(fighters) > 0:
            fighters2 = []
            for f in fighters: fighters2.append(f.mention)
            embed = embeds.base_embed(ctx, 
                color=discord.Color.random(),
                title=f'The following people want to 1v1 {ctx.author}',
                description='\n'.join(fighters2)
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f'{ctx.author.mention}, seems like no one wants to 1v1 you :(', delete_after=5)

    @commands.command(   
        name='say',
        description='Makes the bot say something',
        usage='//say [channel] <text>')
    @commands.has_any_role(ids.LVL8_ROLE_ID, ids.STAFF_ROLE_ID)
    async def say(self, ctx, channel: Optional[discord.TextChannel], *, text):
        ref = ctx.message.reference
        if channel == None: channel = ctx.channel
        if "https://" in text or "http://" in text:
            await ctx.send(f"LMAO I WON'T SEND A LINK HAHA FAILLLL {ctx.author.mention}")
        elif ref != None:
            await ctx.message.delete()
            await channel.send(text, allowed_mentions=discord.AllowedMentions(everyone=False), reference=ref)
        else:
            await ctx.message.delete()
            await channel.send(text, allowed_mentions=discord.AllowedMentions(everyone=False))

    @commands.command(
        name='setbackground',
        aliases=['bg', 'setbg'],
        description='Sets background for your rank card. Its ratio should be 7:3 otherwise it will be resized in improper way',
        usage='//setbg [{image}]'
    )
    @commands.has_any_role(ids.LVL4_ROLE_ID)
    async def setbackground(self, ctx):
        if len(ctx.message.attachments) == 0:
            try:
                os.remove(Data.get_member(ctx.author.id).get_bg())
            except: pass
            await ctx.send(f'Reset your background. Please provide an image to set a new one (ratio should be 7:3)')

        else:
            await ctx.message.attachments[0].save(f'backgrounds/{ctx.author.id}.png')
            Image.open(f'backgrounds/{ctx.author.id}.png').resize((1400, 600)).save(f'backgrounds/{ctx.author.id}.png')
            await ctx.send(f'Successfully set your background! Use `//rank` to check it out')


class Utilities(commands.Cog):
    def __init__(self, bot: CoreBot):
        self.bot = bot

    @commands.command(   
        name='rule',
        description='Shows a single rule',
        usage='//rule <rule index>')
    async def _rule(self, ctx, rule: Rule):
        await ctx.send(embed=embeds.base_embed(ctx,
            color=0x00ffff,
            title=f'Rule {rule.index}',
            description=f'**{rule.text}**'
        ))

    @commands.command(   
        name='report',
        description='Sends a report of a message you replied to',
        usage='//report <reply to message> [reason]')
    @commands.cooldown(1, 30, type=commands.BucketType.member)
    async def report(self, ctx, *, reason='No reason provided'):
        try:
            await ctx.message.delete()
            m = ctx.message.reference.resolved
            await self.bot.server.get_channel(ids.STAFF_CHANNEL_ID).send('@here', embed=embeds.base_embed(ctx,
                color=0xffff00,
                title=f'New report by {ctx.author}',
                description=f'Reported user: **{m.author}** ({m.author.mention})\n\
Reason: {reason}\n\
[Click here]({m.jump_url}) to jump to reported message', footer_user=m.author
            ))
            await ctx.send(embed=embeds.success(ctx, 'Report Submitted', 
            'Report was sent successfully and will be reviewed as soon as possible'
            ), delete_after=3)
        except:
            await ctx.reply('Please reply to the message you are reporting')

    @commands.command(   
        name='emergency',
        aliases=['pingstaff', 'staff'],
        description='Urgently pings all staff members. Unnecessary usage will lead to mute')
    @commands.cooldown(1, 60, type=commands.BucketType.guild)
    async def emergencyStaffPing(self, ctx):
        m = await ctx.send(embed=embeds.base_embed(ctx,
            color=0xff0000,
            title='⚠️ Confirm emergency staff ping',
            description='At least **3** members need to react.\n\
***Unnecessary usage will lead to an instant mute\n\
Request will be automatically cancelled in 60 seconds if bot gets less than 3 reactions***'
        ))
        await m.add_reaction('✅')
        reacted = []
        def check(r, u):
            return r.message.id == m.id and str(r.emoji) == '✅' and not u in reacted and not u.id == self.bot.user.id

        try:
            while len(reacted) < 3:
                _, u = await self.bot.wait_for('reaction_add', check=check, timeout=60)
                reacted.append(u)

            await m.delete()
            m = await ctx.send(f'Emergency staff ping in progress (approximately 30 seconds needed)...')
            channel = self.bot.server.get_channel(ids.STAFF_CHANNEL_ID)
            await channel.send('@everyone EMERGENCY PING', embed=discord.Embed(
                color=0xff0000,
                title=f'Emergency ping in {ctx.channel}',
                description=f'Started by **{ctx.author}** ({ctx.author.mention})'
            ))
            await sleep(3)
            for i in range(10):
                msg = await channel.send(f'⚠️ EMERGENCY IN {ctx.channel.mention} @everyone')
                await sleep(3)
                await msg.delete()

            await m.edit(content='Emergency ping completed')

        except TimeoutError:
            await m.delete()
            await ctx.send('Response timed out', delete_after=3)
        

    @commands.command(   
        name='dm',
        aliases=['send'],
        description='Sends a direct message to user',
        usage='//dm <user> <text>')
    async def _dm(self, ctx, user: discord.Member, *, text):
        await ctx.message.delete()
        m = await ctx.send(embed=embeds.base_embed(ctx,
            color=0xffff00,
            title='❓ Confirm action',
            description=f'Are you sure that you want to DM **{user}** ({user.mention}) the following text?\n\
`{text}`'
        ))
        await addReactions(m, ['✅', '❌'])
        def check(reaction, u):
            return u == ctx.author and reaction.message == m and str(reaction.emoji) in ('✅', '❌')
        try:
            reaction, _ = await self.bot.wait_for('reaction_add', check=check, timeout=30)
            await m.delete()
        except TimeoutError:
            await m.delete()
            raise TimeoutError()
        
        if str(reaction.emoji) == '✅':
            m = await ctx.send('Attempting to DM...')
            try:
                await user.send(embed=discord.Embed(
                    color=0x00ffff,
                    title=f'You got a message from \
{self.bot.server.name+ "Staff Team" if self.bot.staff in ctx.author.roles else str(ctx.author)}',
                    description=text
                ))
                await m.edit(content='Message sent successfully', delete_after=3)
            except Exception as e:
                await m.edit(content=f'Failed to DM: \n```{e}```')
        else:
            await ctx.send(f'You cancelled the operation', delete_after=3)
            await m.delete()

    #__ENTERTAINMENT__#

    @commands.command(
        name='help',
        description='Helps',
        usage='help [command]'
    )
    async def _help(self, ctx, *, name=None):
        if name != None:
            command = self.bot.get_command(name) #type: commands.Command
            if command != None and not command.hidden:
                aliases = ""
                if len(command.aliases) > 0:
                    aliases = f'Aliases: `{", ".join(command.aliases)}`'
                await ctx.send(embed=embeds.base_embed(ctx,
                    color=discord.Color.random(),
                    title=f'{command.qualified_name}',
                    description=f'{command.description}\n\nUsage: `{command.usage}`\n{aliases}'
                ))
            else:
                await ctx.send(embed=embeds.error(ctx, f'No command `{name}` found', 'No command'))
        else:
            embed = embeds.base_embed(ctx,
                color=discord.Color.random(),
                title='Commands',
                description=f'Totally **{len([c for c in self.bot.walk_commands() if not c.hidden])} commands**'
            )

            for cog in self.bot.cogs:
                cog_commands = [command.name for command in self.bot.cogs[cog].get_commands()]
                cog_name = str(cog)
                cogname = cog_name
                for l in cog_name:
                    if l.capitalize() == l:
                        cogname = cogname.replace(l, ' '+l)
                if cog_name == 'AdminXPCommands': cogname = 'Admin XP Commands'
                elif cog_name == 'XPCommands': cogname = 'XP Commands'
                if len(cog_commands) > 0:
                    if not cog_name in ('Administrative', 'AutomodListeners'): embed.add_field(name=cogname, value=f'`{"` `".join(cog_commands)}`')
            await ctx.send(embed=embed)

    @commands.command(   
        name='afk',
        description='Sets an AFK message',
        usage='//afk <message>')
    @commands.has_any_role(ids.STAFF_ROLE_ID, ids.LVL3_ROLE_ID)
    @commands.cooldown(1, 10, type=commands.BucketType.member)
    async def setafk(self, ctx, *, afkText='AFK'):
        memberData = Data.get_member(ctx.author.id)
        memberData.afk = afkText
        memberData.save()
        await ctx.send(embed=embeds.success(ctx, 'AFK set successfully', f'{ctx.author.mention} is now AFK: **{afkText}**'))
        try:
            if not ctx.author.display_name.startswith('[AFK]'):
                await ctx.author.edit(nick='[AFK] '+ctx.author.display_name)
        except: pass

    @commands.command(   
        name='selfrole',
        description='Creates a selfrole or edits existing',
        usage='//selfrole <color> <name>')
    @commands.has_role(ids.LVL10_ROLE_ID)
    async def selfrole(self, ctx, color: discord.Color, *, name):
        memberData = Data.get_member(ctx.author.id)
        if memberData.selfrole == None or self.bot.server.get_role(memberData.selfrole) == None:
            m = await ctx.send(f'Please wait, creating a role...')
            async with ctx.typing():
                role = await self.bot.server.create_role(
                    name=name,
                    color=color)
                await role.edit(position=self.bot.server.get_role(ids.SR_SEPARATOR_ROLE_ID).position+1)
                await ctx.author.add_roles(role)
                memberData.selfrole = role.id
                memberData.save()
                await m.delete()
                await ctx.send(embed=embeds.success('Role Created', 
                f'Created a role {role.mention} as a selfrole of **{ctx.author}** ({ctx.author.mention})'
                ))
        else:
            role = self.bot.server.get_role(memberData.selfrole)
            await role.edit(name=name, color=color)
            await ctx.send(embed=embeds.success('Role edited', f'Edited role {role.mention}'
            ))

    @commands.command(   
        name='vote',
        description='Starts a vote',
        usage='//vote <topic>')
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def vote(self, ctx, *, topic):
        m = await ctx.send(embed=embeds.base_embed(ctx,
            color=0x00ffff,
            title=f'Vote by {ctx.author}',
            description=topic
        ))
        await addReactions(m, ['👍', '👎'])

    @commands.command(   
        name='ping',
        description='Checks bot\'s latency',
        usage='//ping')
    @commands.cooldown(1, 5, commands.BucketType.channel)
    async def ping(self, ctx):
        m = ctx.message
        rt = int((datetime.now()-m.created_at).microseconds*0.001)
        latency = self.bot.latency
        m2 = await ctx.send(embed=discord.Embed(
            color=0x00ff00,
            description=f"API response time: `{rt} ms`\nOperation time: `calculating`\nLatency: `{int(latency*100)} ms`"))
        ot = int((m2.created_at-m.created_at).microseconds*0.001)
        await m2.edit(embed=discord.Embed(
            color=0x00ff00,
            description=f"API response time: `{rt} ms`\nOperation time: `{ot} ms`\nLatency: `{int(latency*100)} ms`"))

    @commands.command(   
        name='members',
        description='Represents a list of members in role. When you provide `[top]`, represents a list of members\
that have this role as top role',
        usage='//members <role> [top]')
    @commands.cooldown(1, 10, type=commands.BucketType.member)
    async def members(self, ctx, role: discord.Role, top=None):
        m = await ctx.send("Scanning members...")
        lst = []
        if top == None:
            lst = [str(member) for member in role.members]
        else:
            for user in self.bot.server.members:
                if user.top_role == role:
                    lst.append(str(user))
        if len(lst) > 40: lst = lst[:40]
        if len(lst) > 0:
            embed = embeds.base_embed(ctx, title=f"{len(lst)} members found", description="\n".join(lst))
            await m.edit(content=None, embed=embed)
        else:
            await m.delete()
            await ctx.send(f"{ctx.author.mention}, no members found in this role!")

    @commands.command(   
        name='whois',
        description='Shows information about user',
        usage='//whois <user>')
    async def whois(self, ctx, victim: discord.Member=None):
        if victim == None: victim = ctx.author
        embed = embeds.base_embed(ctx, color=0x00ffff)
        embed.set_author(  
            name=f"Information about **{victim.name}**",
            icon_url=victim.avatar_url)
        embed.add_field(
            name="Joined on",
            value=f"{victim.joined_at.strftime('%d %b %Y  %H:%M:%S')} ({(datetime.now()-victim.joined_at).days} days ago)")
        embed.add_field(
            name="Account created",
            value=f"{victim.created_at.strftime('%d %b %Y  %H:%M:%S')} ({(datetime.now()-victim.created_at).days} days ago)")
        embed.add_field(
            name='Score',
            value=str(Data.get_member(victim.id).xp.total))
        await ctx.send(embed=embed)
        
    @commands.command(   
        name='math',
        aliases=['count'],
        description='Calculates an expression. Leave `[expression]` empty to receive help about avalaible operations',
        usage='//math [expression]')
    @commands.cooldown(1, 5, type=commands.BucketType.member)
    async def math(self, ctx, *, expr='help'):
        if expr == 'help':
            await ctx.send(embed=discord.Embed(
                color=0x00ffff,
                title='Common math operations',
                description='+ - / *\taddition, substraction, division and multiplication\n\
**\texponentiation\n\
sqrt(x)\tsquare root of x\n\n\
Get more information about available math functions [here](https://docs.python.org/3/library/math.html)'
            ))
        else:
            time_start = datetime.now()
            try:
                result = str(Parser().parse(expr).evaluate({}))
                if result.count('\n') < 20:
                    time = (datetime.now()-time_start).microseconds*0.001
                    embed = discord.Embed(color=0x00ff00, title="Result", description=f"`{result}`")
                    embed.set_footer(text=f"Calculated within {time} microseconds")
                    await ctx.send(embed=embed)
                else:
                    await ctx.send(embed=embeds.error(ctx, 'Response was too huge, I can\'t send it here unfortunately'))
            except Exception as e:
                await ctx.reply(embed=embeds.error(ctx, f"The following error occured: ```{e}```"))

    @commands.command(
        name='rep',
        aliases=['repstaff'],
        description='Adds a reputation point to a staff member. Useable once per day',
        usage='//rep <user>'
    )
    async def repstaff(self, ctx, user: discord.Member):
        await ctx.message.delete()
        staff = self.bot.staff
        data = Data()
        if staff in ctx.author.roles:
            await ctx.send(f'{ctx.author.mention} staff members can\'t rep')
        elif not staff in user.roles:
            await ctx.send(f'{ctx.author.mention} you can only rep staff members')
        elif ctx.author.id in data.voted_users:
            await ctx.send(f'{ctx.author.mention} you have already gave your rep point today')
        else:
            if not user.id in data.staff_votes:
                data.staff_votes[user.id] = 1
            else:
                data.staff_votes[user.id] += 1

            data.voted_users.append(ctx.author.id)
            data.save()
            await ctx.send(f'{ctx.author.mention} assigned a reputation point to {user.mention}')

    @commands.group(
        name='dc',
        aliases=['dmchan', 'dmc'],
        description='Commands group for creating and managing DM channels. \n\
Subcommands: create, add, remove, close',
        usage='//dc <subcommand>'
    )
    async def dmchannel(self, ctx):
        if ctx.invoked_subcommand == None:
            pass

    @dmchannel.command(
        name='create',
        description='Creates a new DM channel and adds a chosen person(s) and role(s) to there',
        usage='//dc create <user | role 1> [user | role 2] ... [user | role N]'
    )
    async def dm_create(self, ctx, *users: Union[discord.Member, discord.Role]):
        server = self.bot.server
        data = Data()
        if server.get_role(ids.DM_MUTED_ROLE_ID) in ctx.author.roles:
            raise PermissionDenied
        
        m = await ctx.send(f'Please wait, gathering info...')
        count = 0
        for channel in list(data.dm_channels.values()).copy():
            if ctx.author.id == channel.owner:
                _channel = server.get_channel(channel.id)
                if _channel == None:
                    data.dm_channels.pop(channel.id)
                    data.save()
                else:
                    count += 1

        await m.delete()
        if server.get_role(ids.STAFF_ROLE_ID) in ctx.author.roles:
            count = 0
        if count >= 3:
            await ctx.send(f'You already have **{count}** DM channels opened. Please close at least {count-2} to create new')
            return
                
        overwrites = {
            server.default_role: discord.PermissionOverwrite(read_messages=False, attach_files=True),
            self.bot.staff: discord.PermissionOverwrite(read_messages=True),
            ctx.author: discord.PermissionOverwrite(read_messages=True, manage_messages=True)
        }
        for user in users:
            overwrites[user] = discord.PermissionOverwrite(read_messages=True)
        channel = await server.create_text_channel(
            f'dm-{ctx.author.name}',
            overwrites=overwrites,
            category=server.get_channel(ids.DM_CHANNELS_CATEGORY_ID))
        data.dm_channels[channel.id] = DMChannel(channel.id, ctx.author.id)
        data.save()
        await ctx.send(f'{ctx.author.mention} channel {channel.mention} was created successfully!')

    @dmchannel.command(
        name='add',
        description='Adds users/roles to DM channel. If [channel] is not provided, channel is the current one',
        usage='//dc add [channel] <user | role 1> [user | role 2] ... [user | role N]'
    )
    async def dm_add(self, ctx, channel: Optional[discord.TextChannel], *users: Union[discord.Member, discord.Role]):
        if channel == None: channel = ctx.channel
        data = Data()
        if not channel.id in data.dm_channels:
            await ctx.send(f'Channel {channel.mention} is not a DM channel')
        elif data.dm_channels[channel.id].owner != ctx.author.id and not self.bot.staff in ctx.author.roles:
            await ctx.send(f'You do not have permission to manage {channel.mention}')
        else:
            overwrites = channel.overwrites
            for user in users:
                overwrites[user] = discord.PermissionOverwrite(read_messages=True)
            await channel.edit(overwrites=overwrites)
            await ctx.send(f'Successfully added requested users/roles to {channel.mention}')

    @dmchannel.command(
        name='remove',
        description='Removes users/roles from DM channel. If [channel] is not provided, channel is the current one',
        usage='//dc remove [channel] <user | role 1> [user | role 2] ... [user | role N]'
    )
    async def dm_remove(self, ctx, channel: Optional[discord.TextChannel], *users: Union[discord.Member, discord.Role]):
        data = Data()
        if channel == None: channel = ctx.channel

        if not channel.id in data.dm_channels:
            await ctx.send(f'Channel {channel.mention} is not a DM channel')
        elif data.dm_channels[channel.id].owner != ctx.author.id and not self.bot.staff in ctx.author.roles:
            await ctx.send(f'You do not have permission to manage {channel.mention}')
        else:
            overwrites = channel.overwrites
            for user in users:
                try:
                    overwrites.pop(user)
                except: pass

            await channel.edit(overwrites=overwrites)
            await ctx.send(f'Successfully removed requested users/roles from {channel.mention}')

    @dmchannel.command(
        name='close',
        aliases=['delete'],
        description='Deletes DM channel. If [channel] is not provided, channel is the current one',
        usage='//dc close [channel]'
    )
    async def dm_close(self, ctx, channel: discord.TextChannel = None):
        data = Data()
        if channel == None: channel = ctx.channel

        if not channel.id in data.dm_channels:
            await ctx.send(f'Channel {channel.mention} is not a DM channel')
        elif data.dm_channels[channel.id].owner != ctx.author.id and not self.bot.staff in ctx.author.roles:
            await ctx.send(f'You do not have permission to manage {channel.mention}')
        else:
            await ctx.send(f'Deleting the channel...')
            await data.dm_channels[channel.id].close()


class Music(commands.Cog):
    YTDL_PARAMS = {
    'quality': 'beastaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'noplaylist': True,
    'default_search': 'ytsearch',
    'quiet': True
}

    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }

    def __init__(self, bot: CoreBot):
        self.bot = bot
        self.ytdl = YoutubeDL(Music.YTDL_PARAMS)

    @staticmethod
    def play_next_track(_=None):
        global now_playing
        if len(queue) > 0: 
            track = queue[0]
            queue.remove(track)
            now_playing = track
            track.server.voice_client.play(discord.FFmpegPCMAudio(track.url, executable='ffmpeg', **Music.FFMPEG_OPTIONS), 
            after=Music.play_next_track)

    @commands.command(
        name='play',
        aliases=['pl'],
        description='Plays a track or adds it to the queue',
        usage='//play <track>'
    )
    async def play(self, ctx, *, track):
        m = await ctx.send('Downloading audio...')
        try:
            if ctx.author.voice == None or ctx.voice_client == None or ctx.voice_client.channel != ctx.author.voice.channel:
                await ctx.author.voice.channel.connect()
        except: 
            await ctx.send(f'You have to be in vc to use this command')
            return
        info = None
        try:
            info = self.ytdl.extract_info(track, download=False)['entries'][0]
        except:
            await ctx.send(f'Failed to fetch `{track}` track')
            return
        finally:
            await m.delete()
        url = info['formats'][0]['url']
        title = info['title']
        desc = info['description']
        if len(desc) > 500:
            desc = desc[:500] + '...'
        track = Track(self.bot.server, title, url, desc, ctx.author)
        queue.append(track)
        if not ctx.voice_client.is_playing():
            Music.play_next_track()
            await ctx.send(embed=embeds.base_embed(ctx,
                color=0x00ffff,
                title='Now Playing',
                description=f'[{title}]({url})\n{desc}'
            ))
        else:
            await ctx.send(embed=embeds.base_embed(ctx,
                color=0x00ff00,
                title=f'Added to queue - `{len(queue)}` positions in queue now',
                description=f'[{title}]({url})\n{desc}'
            ))

    @commands.command( 
        name='playskip',
        aliases=['ps'],
        description='Skips the current song and immediately plays the new',
        usage='//playskip <track>'
    )
    @is_dj()
    async def playskip(self, ctx, *, track):
        m = await ctx.send('Downloading audio...')
        info = None
        try:
            info = self.ytdl.extract_info(track, download=False)['entries'][0]
        except:
            await ctx.send(f'Failed to fetch `{track}` track')
            return
        finally:
            await m.delete()
        url = info['formats'][0]['url']
        title = info['title']
        desc = info['description']
        if len(desc) > 500:
            desc = desc[:500] + '...'
        track = Track(self.bot.server, title, url, desc, ctx.author)
        queue.insert(0, track)
        await ctx.send(embed=discord.Embed(
                color=0x00ffff,
                title='Now Playing',
                description=f'[{title}]({url})\n{desc}'
            ))
        self.bot.server.voice_client.stop()

    @commands.command(
        name='stop',
        description='Stops the current soundtrack and clears the queue',
        usage='//stop'
    )
    @is_dj()
    async def _stop(self, ctx):
        queue.clear()
        self.bot.server.voice_client.stop()
        await ctx.send(f'Stopped the soundtrack')

    @commands.command(
        name='skip',
        aliases=['skp'],
        description='Skips to the next track track or adds it to the queue',
        usage='//skip'
    )
    @is_dj()
    async def skip(self, ctx):
        self.bot.server.voice_client.stop()
        await ctx.send(f'Skipped :white_check_mark:')

    @commands.command( 
        name='queue',
        description='Lists the songs in the queue',
        usage='//queue'
    )
    async def showqueue(self, ctx):
        if now_playing == None:
            await ctx.send(f'No songs in queue')
            return
        desc = f"**[[NOW PLAYING]] [{now_playing.name}]({now_playing.url})**\n\n"
        num = 1
        for track in queue:
            desc += f'[{num}] -- {track.name}\n\n'
            num += 1
            if num > 10:
                break
        if len(desc) > 6000: desc = desc[:5990]
        embed = embeds.base_embed(ctx,
            color=discord.Color.blue(),
            title=f'Current queue - `{len(queue)}` positions in',
            description=desc
        )
        await ctx.send(embed=embed)

    @commands.command(
        name='removetrack',
        aliases=['rmtrack', 'rmqueue'],
        description='Removes a track from the queue by its number',
        usage='//rmtrack <number>'
    )
    @is_dj()
    async def removetrack(self, ctx, number: int):
        try:
            track = queue.pop(number-1)
            await ctx.send(f'Successfully removed [{track.name}]({track.url}) from the queue')
        except:
            await ctx.send('Couldn\'t find a track with that number')

    @commands.command(
        name='disconnect',
        aliases=['dsc'],
        description='Disconnects from a voice channel',
        usage='//dc'
    )
    @is_dj()
    async def disconnect(self, ctx):
        queue.clear()
        await self.bot.server.voice_client.disconnect()

def setup(bot: CoreBot):
    for cls in (
        Entertainment,
        Utilities,
        Music
    ):
        bot.add_cog(cls(bot))