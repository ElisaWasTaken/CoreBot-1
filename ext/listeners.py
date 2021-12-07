import discord, ids
from discord.ext import commands
from modules.db_manager import Data, CoreBot
from modules.utils import check_member_nick, check_nick
from datetime import datetime

class MessageListeners(commands.Cog):
    def __init__(self, bot: CoreBot):
        self.bot = bot

    @commands.Cog.listener('on_message')
    async def FilemutedController(self, msg: discord.Message):
        if any((msg.is_system(), msg.channel.type == discord.ChannelType.private, msg.author.bot)): return
        if self.bot.server.get_role(ids.FILEMUTED_ROLE_ID) in msg.author.roles and len(msg.attachments) > 0 and not self.bot.staff in msg.author.roles \
            and not msg.channel.id == ids.ANNOUNCEMENTS_CHANNEL_ID:
            await msg.delete()
            await msg.channel.send(f'Sorry, {msg.author.mention}, but you are filemuted and can\'t attach any files', delete_after=5)
            if len(msg.content) > 100:
                try:
                    await msg.author.send('You sent a long message but it was deleted, here is its backup if you wanted it!', 
                    embed=discord.Embed(color=discord.Color.random(), title='Text Backup', description=msg.content))
                except: pass

    @commands.Cog.listener('on_message')
    async def AFKController(self, msg: discord.Message):
        if any((msg.is_system(), msg.channel.type == discord.ChannelType.private, msg.author.bot)): return
        memberData = Data.get_member(msg.author.id)
        for user in msg.mentions:
            userData = Data.get_member(user.id)
            if userData.afk != None:
                await msg.reply(f'**{user}** is AFK: {userData.afk}', delete_after=3,
                allowed_mentions=discord.AllowedMentions(everyone=False))
                break

        #check author's AFK
        isAfkCMD = False
        for p in ['h!', 'H!', '//']:
            if msg.content.lower().startswith(f'{p}afk'):
                isAfkCMD = True
        if memberData.afk != None and msg.edited_at == None and not msg.channel.id in ids.AFK_IGNORED and not isAfkCMD:
            memberData.afk = None
            memberData.save()
            await msg.channel.send(embed=discord.Embed(
                color=0x00ffff,
                title='👋 Welcome back',
                description=f'**{msg.author}**\'s AFK was removed'
            ), delete_after=3)
            try:
                await msg.author.edit(nick=msg.author.nick.replace('[AFK] ', ''))
            except: pass

    @commands.Cog.listener('on_message_delete')
    async def DeleteController(self, message: discord.Message):
        channel = self.bot.server.get_channel(ids.DELETED_LOG_CHANNEL_ID)
        if message.guild.id == self.bot.server.id and not message.channel.id in ids.DELETE_IGNORED \
        and not message.author.bot:
            files = []
            for attachment in message.attachments:
                files.append(await attachment.to_file())
            embed = discord.Embed(
                color=0xffff00,
                title=f'Message deleted from #{message.channel.name}',
                description=message.content
            )
            embed.set_author(name=str(message.author), icon_url=message.author.avatar_url)
            try:
                await channel.send(embed=embed, files=files)
            except:
                await channel.send(embed=embed)


class MembersListeners(commands.Cog):
    def __init__(self, bot: CoreBot):
        self.bot = bot

    @commands.Cog.listener('on_member_join')
    async def JoinController(self, member: discord.Member):
        server = self.bot.server
        channel = server.get_channel(ids.WELCOME_CHANNEL_ID)
        await channel.send(f'Hey {member.mention}, welcome to our server! \
We hope you will have a great time here. By the way, you are our **{len(server.members)}th member!**')
        await check_member_nick(member)

    @commands.Cog.listener('on_member_remove')
    async def MemberController(self, member: discord.Member):
        await self.bot.server.get_channel(ids.LEAVE_LOGS_CHANNEL_ID).send(f'**{member}** just left')
        memberData = Data.get_member(member.id)
        if memberData.selfrole == None:
            try:
                await self.bot.server.get_role(memberData.selfrole).delete()
            except:
                pass
            finally:
                memberData.selfrole = None
                memberData.save()

    @commands.Cog.listener('on_member_update')
    async def NicknameController(self, before, after):
        if self.bot.muted in after.roles and before.nick != after.nick:
            await after.edit(nick='Nickname Blocked')

        else:
            res = await check_member_nick(after)
            if res != None:
                if check_nick(after.name) == None:
                    await after.edit(nick=None)

    @commands.Cog.listener('on_user_update')
    async def NameController(self, _, after):
        if not after.display_name.startswith('Bad nick'):
            await check_member_nick(self.bot.server.get_member(after.id))
        else:
            res = check_nick(after.name)
            if res == None:
                await after.edit(nick=None)


class ReactionsListeners(commands.Cog):
    def __init__(self, bot: CoreBot):
        self.bot = bot

    @commands.Cog.listener('on_reaction_add')
    async def ReactionController(self, reaction, user):
        if str(reaction.emoji) == '⚠️' and self.bot.staff in user.roles and not self.bot.staff in reaction.message.author.roles:
            await reaction.message.delete()
            id = reaction.message.author.id
            try:
                self.bot.local_warns[id] += 1
            except:
                self.bot.local_warns[id] = 1
            warnsBeforeMute = 3-self.bot.local_warns[id]
            if warnsBeforeMute <= 0:
                warnsBeforeMute = 'muted'
            await self.bot.updateLocalWarns(id)
            await reaction.message.channel.send(embed=discord.Embed(
                color=0xffff00,
                title='⚠️ Bypass logged',
                description=f'{reaction.message.author.mention} was warned for avoiding automatic word filter\n\
Warnings before mute: `{warnsBeforeMute}`\n\
Warnings reset in `{(self.bot.next_reset-datetime.now()).seconds//60} minutes`'
            ))
            await self.bot.log_channel.send(embed=discord.Embed(
                color=0xffff00,
                title='⚠️ Bypass Logged',
                description=f'{user.mention} blocked a message by {reaction.message.author.mention} in {reaction.message.channel.mention}. Deleted content:\n\
{reaction.message.content}'
            ))

    @commands.Cog.listener('on_raw_reaction_add')
    async def ReactionRoleAddController(self, payload: discord.RawReactionActionEvent):
        server = self.bot.server
        data = Data()
        message_id = payload.message_id
        member = server.get_member(payload.user_id)
        emoji = payload.emoji.id if payload.emoji.is_custom_emoji() else str(payload.emoji)
        if message_id in data.reaction_roles and emoji in data.reaction_roles[message_id] and not member.bot:
            role = server.get_role(data.reaction_roles[message_id][emoji])
            await member.add_roles(role)
            await server.get_channel(payload.channel_id).send(
                f'{member.mention} was assigned {role.mention}', 
                delete_after=3, 
                allowed_mentions=discord.AllowedMentions(roles=False))

    @commands.Cog.listener('on_raw_reaction_remove')
    async def ReactionRoleRemoveController(self, payload: discord.RawReactionActionEvent):
        server = self.bot.server
        data = Data()
        message_id = payload.message_id
        member = server.get_member(payload.user_id)
        emoji = payload.emoji.id if payload.emoji.is_custom_emoji() else str(payload.emoji)
        if message_id in data.reaction_roles and emoji in data.reaction_roles[message_id] and not member.bot:
            role = server.get_role(data.reaction_roles[message_id][emoji])
            if role in member.roles:
                await member.remove_roles(role)
                await server.get_channel(payload.channel_id).send(
                    f'Removed {role.mention} from {member.mention}', 
                    delete_after=3, 
                    allowed_mentions=discord.AllowedMentions(roles=False))

def setup(bot: CoreBot):
    for cls in (
        MessageListeners,
        MembersListeners,
        ReactionsListeners
    ):
        bot.add_cog(cls(bot))