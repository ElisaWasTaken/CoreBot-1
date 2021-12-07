import discord, os, ids
from discord.ext import commands
from modules.db_manager import CoreBot, Data
from modules.converters import TopMode
from modules.utils import get_dict_slice
from modules.image_generator import draw_leaderboard, draw_rank_card
from modules import embeds
from datetime import datetime, timedelta
from discord.ext import commands
from random import randint
from typing import Optional
from math import ceil

class XPListeners(commands.Cog):
    def __init__(self, bot: CoreBot):
        self.bot = bot

    async def loop_waiter(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener('on_message')
    async def XPController(self, msg: discord.Message):
        if msg.channel.type == discord.ChannelType.private or msg.author.bot: return
        memberData = Data.get_member(msg.author.id)
        data = Data()
        if msg.edited_at == None and not msg.channel.id in ids.XP_IGNORED:
            if datetime.now() >= memberData.xp.cooldown:
                xp = randint(15, 25)
                memberData.xp.total += xp * data.score_multiplier
                memberData.xp.daily += xp
                memberData.xp.weekly += xp
                memberData.xp.cooldown = datetime.now()+timedelta(minutes=1)
                data.score_today += xp
                data.save()
                memberData.save()
            xp = memberData.xp.total
            roles = []
            removeroles = []
            highest = [None, 0]
            for required in data.levels:
                if xp >= required:
                    role = self.bot.server.get_role(data.levels[required])
                    if role == None:
                        data.remove_level(required)
                    elif not role in msg.author.roles:
                        roles.append(role)
                        if required > highest[1]:
                            highest = [role, required]
                else:
                    role = self.bot.server.get_role(data.levels[required])
                    if role == None:
                        data.remove_level(required)
                    elif role in msg.author.roles:
                        removeroles.append(role)
            await msg.author.remove_roles(*removeroles)
            if len(roles) > 0:
                await msg.author.add_roles(*roles)
                await msg.channel.send(embed=embeds.base_embed(msg,
                    color=0x00ff00,
                    title='⬆️ Level up',
                    description=f'Congratulations, {msg.author.mention}, you leveled up to {highest[0].mention}!'
                ))


class XPCommands(commands.Cog):
    def __init__(self, bot: CoreBot):
        self.bot = bot

    def get_user_xp_embed(self, user: discord.User, leaderboard_mode = 'total'):
        member_data = Data.get_member(user.id)
        xpData = member_data.xp
        next = None
        for required in Data().levels:
            if required > xpData.total:
                if next == None:
                    next = required
                else:
                    if required < next:
                        next = required
        description = ''
        leaderboard_position = member_data.get_leaderboard_place(leaderboard_mode)
        next_role: discord.Role = self.bot.server.get_role(Data().levels[next]) if next else None
        if next == None:
            description = f'''Total score: `{xpData.total}` | **#{leaderboard_position}** on leaderboard
(All roles obtained)
Daily score: `{xpData.daily}`
Weekly score: `{xpData.weekly}`'''
        else:
            description = f'''Total score: `{xpData.total}/{next}` | **#{leaderboard_position}** on leaderboard
Next role: {next_role.mention} `({next-xpData.total} left)`
Daily score: `{xpData.daily}`
Weekly score: `{xpData.weekly}`'''
        embed = discord.Embed(
            color=discord.Color.random(),
            title=f'Level info of {user}',
            description=description
        )
        rank_card_name = draw_rank_card(
            user,
            leaderboard_position,
            next_role,
            getattr(xpData, leaderboard_mode),
            next,
            Data.get_member(user.id).get_bg()
        )
        file = discord.File(rank_card_name, 'rank.png')
        embed.set_image(url=f'attachment://rank.png')
        return embed, file, rank_card_name

    @commands.group( 
        name='level',
        aliases=['lvl', 'rank'],
        description='See your level.\n\
Available subcommands: `user, add, remove, levels`',
        usage='//level')
    async def _level(self, ctx):
        if ctx.invoked_subcommand == None:
            async with ctx.typing():
                xp_embed, file, filename = self.get_user_xp_embed(ctx.author)
                await ctx.send(file=file, embed=xp_embed)
                os.remove(filename)

    @_level.command(    
        name='user',
        description='Shows level info of user.',
        usage='//level user <user>')
    @commands.cooldown(1, 5, type=commands.BucketType.member)
    async def level_user(self, ctx, user: discord.Member):
        async with ctx.typing():
            xp_embed, file, filename = self.get_user_xp_embed(user)
            await ctx.send(file=file, embed=xp_embed)
            os.remove(filename)

    @_level.command(    
        name='add',
        description='Adds a single leveled role',
        usage='//level add <role> <required score>')
    @commands.has_permissions(manage_guild=True)
    async def level_add(self, ctx, role: discord.Role, score: int):
        Data().add_level(score, role.id)
        await ctx.send(embed=embeds.success(ctx, 'Action Applied', f'{role.mention} added with `{score}` xp required'))

    @_level.command(    
        name='remove',
        description='Removes a single leveled role',
        usage='//level remove <score>')
    @commands.has_permissions(manage_guild=True)
    async def level_remove(self, ctx, score: int):
        Data().remove_level(score)
        await ctx.send(embed=embeds.success(ctx, 'Level Removed', f'Level with required score of `{score}` was successfully removed'))

    @_level.command(    
        name='levels',
        aliases=['show', 'lvls', 'list'],
        description='Shows all leveled roles',
        usage='//level levels')
    @commands.cooldown(1, 10, type=commands.BucketType.channel)
    async def level_show(self, ctx):
        data = Data()
        keys = list(data.levels.keys())
        keys.sort()
        description = ''
        for i in keys:
            role = self.bot.server.get_role(data.levels[i])
            if role == None:
                data.remove_level(i)
                continue
            else:
                description += f'{role.mention}\t`{i}`\n'
        await ctx.send(embed=embeds.base_embed(ctx,
            color=discord.Color.random(),
            title='Levels info',
            description=description
        ))

    @commands.command(
        name='top',
        description='Shows the top-100 chatters on the server.\n\
Available variants: `total (default)`, `daily`, `weekly`.'
    )
    @commands.cooldown(1, 7, commands.BucketType.user)
    async def top(self, ctx, mode: Optional[TopMode] = 'total', page: int = 1):
        async with ctx.typing():
            top_data = Data.get_top_scores(mode)
            max_page = ceil(max(top_data.keys()) / 10)
            if page > max_page:
                page = max_page
            file_name = draw_leaderboard(self.bot, get_dict_slice(Data.get_top_scores(mode), page * 10 - 9, page * 10), page)
            member_data = Data.get_member(ctx.author.id)
            embed = embeds.base_embed(ctx, 
                color=discord.Color.random(),
                title=f'{mode.capitalize() if mode != "total" else "Global"} Leaderboard',
                description=f'Your score: `{getattr(member_data.xp, mode)}`\n\
Your {mode if mode != "total" else "global"} leaderboard position: `{member_data.get_leaderboard_place(mode)}`')
            
            file = discord.File(file_name, 'leaderboard.png')
            embed.set_image(url=f'attachment://leaderboard.png')
            await ctx.send(file=file, embed=embed)
            os.remove(file_name)

    @commands.command(   
        name='getscoremultiplier',
        aliases=['gsm'],
        description='Shows current score multiplier')
    async def getscoremultiplier(self, ctx):
        await ctx.send(f'Current score multiplier is `x{Data().score_multiplier}`')

    
class AdminXPCommands(commands.Cog):
    def __init__(self, bot: CoreBot):
        self.bot = bot

    def cog_check(self, ctx):
        if not ctx.author.guild_permissions.manage_guild:
            raise commands.MissingPermissions(['manage guild'])
        return True
    
    @commands.command(   
        name='setscoremultiplier',
        aliases=['ssm', 'setscoremult', 'setmult'],
        description='Sets a new score multiplier',
        usage='//setscoremultiplier <new multiplier>')
    async def setscoremultiplier(self, ctx, newmulti: int):
        data = Data()
        data.score_multiplier = newmulti
        data.save()
        await ctx.send(f'Set score multiplier to `x{newmulti}`')

    @commands.command(   
        name='addscore',
        description='Adds score to a user',
        usage='//addscore <user> <score>')
    async def addscore(self, ctx, user: discord.Member, score: int):
        memberData = Data.get_member(user.id)
        memberData.xp.total += score
        memberData.save()
        await ctx.send(embed=embeds.success(ctx, 'Action Applied', f'Added `{score}` score to **{user}** ({user.mention})'))

    @commands.command(   
        name='removescore',
        description='Substracts score from a user. Leave `[score]` empty to substract __**all**__ score',
        usage='//removescore <user> [score]')
    async def removescore(self, ctx, user: discord.Member, score: Optional[int]):
        memberData = Data.get_member(user.id)
        if score == None:
            memberData.xp.total = 0
        else:
            memberData.xp.total -= score
        memberData.save()
        await ctx.send(embed=embeds.success(ctx, 'Action Applied', f'Removed `{score}` score from **{user}** ({user.mention})'))

def setup(bot: CoreBot):
    for cls in (
        XPListeners,
        XPCommands,
        AdminXPCommands
    ):
        bot.add_cog(cls(bot))