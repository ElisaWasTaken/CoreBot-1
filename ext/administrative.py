import discord
from discord.ext import commands
from discord.ext.commands import Cog, Context
from modules.db_manager import CoreBot, Data
from modules.exceptions import OwnerOnly
from modules import embeds, constants, converters, errors, exceptions, utils, youtube, db_manager

class Administrative(Cog):
    def __init__(self, bot: CoreBot):
        self.bot = bot

    async def cog_check(self, ctx: Context):
        cond = await self.bot.is_owner(ctx.author)
        if not cond: raise OwnerOnly()
        return True

    @commands.command(   
        name='exec',
        description='Executes a code (owner only)',
        hidden=True,
        usage='//exec <code>')
    async def _exec(self, ctx, *, code):
        try:
            exec(code)
            await ctx.send(f'Code executed successfully')
        except Exception as e:
            await ctx.send(f'Code was not executed due to raised exception: {e}')
    
    @commands.command(   
        name='eval',
        description='Evaluates the code and returns the result (owner only)',
        usage='//eval <code>')
    async def _eval(self, ctx, *, code):
        try:
            result = str(eval(code))
            await ctx.send(embed=embeds.base_embed(ctx,
                color=0x00ff00,
                title='✅ Code evaluated',
                description=result
            ))
        except Exception as e:
            await ctx.send(embed=discord.Embed(ctx,
                color=0xff0000,
                title='❌ Error occured',
                description=str(e)
            ))

    @commands.command(
        name='reload',
        description='Reloads extensions',
        usage='//reload <exts>'
    )
    async def reload_ext(self, ctx, *exts):
        for ext in exts:
            self.bot.reload_extension(f'ext.{ext}')

        await ctx.send('Extensions reloaded')

def setup(bot: CoreBot):
    bot.add_cog(Administrative(bot))