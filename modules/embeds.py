from discord import Embed, Message
from discord.ext.commands import Context
from datetime import datetime, timezone, timedelta
from typing import Union

tz = timezone(timedelta(seconds=0), name='UTC')

def error(ctx: Context, description, title='Error Occured', *, footer_user=None):
    if footer_user == None: footer_user = ctx.author
    embed = Embed(
        color=0xff0000,
        title=f'❌ {title}',
        description=description,
        timestamp=datetime.now(tz),
    )
    embed.set_footer(text=str(footer_user), icon_url=footer_user.avatar_url)
    return embed

def success(ctx: Context, title, description, *, footer_user=None):
    if footer_user == None: footer_user = ctx.author
    embed = Embed(
        color=0x00ff00,
        title=f'✅ {title}',
        description=description,
        timestamp=datetime.now(tz)
    )
    embed.set_footer(text=str(footer_user), icon_url=footer_user.avatar_url)
    return embed

def warning(ctx: Context, title, description, *, footer_user=None):
    if footer_user == None: footer_user = ctx.author
    embed = Embed(
        color=0xffff00,
        title=f'⚠️ {title}',
        description=description,
        timestamp=datetime.now(tz)
    )
    embed.set_footer(text=str(footer_user), icon_url=footer_user.avatar_url)
    return embed

def confirm(ctx: Context, description, add_footer=True, *, footer_user=None):
    if footer_user == None: footer_user = ctx.author
    embed = Embed(
        color=0xffff00,
        title='⚠️ Confirm Action',
        description=description,
        timestamp=datetime.now(tz)
    )
    if add_footer:
        embed.set_footer(text='React with ✅ to proceed, otherwise operation will be cancelled automatically in 10 seconds')
    else:
        embed.set_footer(text=str(footer_user), icon_url=footer_user.avatar_url)
    return embed

def wait(ctx: Context, description, *, footer_user=None):
    if footer_user == None: footer_user = ctx.author
    embed = Embed(
        color=0xffff00,
        title='🕓 Waiting for Response',
        description=description,
        timestamp=datetime.now(tz)
    )
    embed.set_footer(text=str(footer_user) + ' | Respond with "cancel" to cancel input', icon_url=footer_user.avatar_url)
    return embed

def base_embed(ctx: Union[Context, Message], *, footer_user=None, **kwargs):
    if footer_user == None: footer_user = ctx.author
    embed = Embed(**kwargs, timestamp=datetime.now(tz))
    embed.set_footer(text=str(footer_user), icon_url=footer_user.avatar_url)
    return embed