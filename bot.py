from discord import ChannelType
from modules.db_manager import CoreBot
from modules.utils import checkword, checkprint

bot = CoreBot('6.2')
@bot.check
def globalCheck(ctx):
    return ctx.channel.type != ChannelType.private and \
    ((checkword(ctx.message.content)[0] and checkprint(ctx.message.content)) or ctx.author.guild_permissions.administrator) and \
    ctx.message.edited_at == None

print('Loading extensions...')
bot.load_all_extensions()
print('Connecting')

bot.run()