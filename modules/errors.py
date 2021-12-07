from discord.ext import commands
from modules.exceptions import *

def get_error_msg(ctx, error: commands.CommandError):
    if isinstance(error, commands.MissingRequiredArgument): return  f'The command is missing `{error.param.name}` argument\n\
Please make sure to follow command usage: `{ctx.command.usage}`'

    elif isinstance(error, commands.ArgumentParsingError): return f'Invalid argument parsed\n\
Please make sure to follow command usage: `{ctx.command.usage}`'

    elif isinstance(error, commands.BadArgument): return f'Invalid argument parsed\n\
Please make sure to follow command usage: `{ctx.command.usage}`'

    elif isinstance(error, commands.CommandNotFound): return f'This command does not exist'

    elif isinstance(error, commands.DisabledCommand): return f'This command is disabled'

    elif isinstance(error, commands.CommandOnCooldown): return f'Command is on cooldown. Try again in {int(error.retry_after)} seconds'

    elif isinstance(error, commands.NotOwner): return f'This command is administrative'

    elif isinstance(error, commands.MemberNotFound): return f'Member {error.argument} does not exist'

    elif isinstance(error, commands.UserNotFound): return f'User {error.argument} does not exist'

    elif isinstance(error, commands.ChannelNotFound): return f'Channel {error.argument} does not exist'

    elif isinstance(error, commands.RoleNotFound): return f'Role {error.argument} does not exist'

    elif isinstance(error, commands.MissingPermissions): return f'You need `{", ".join([str(perm) for perm in error.missing_perms])}` permission(s) to use this command'

    elif isinstance(error, commands.MissingRole): return f'You need `{error.missing_role}` role to use this command'

    elif isinstance(error, commands.MissingAnyRole): return f'You need one of the following roles to use this command: `{", ".join([str(role) for role in error.missing_roles])}`'

    elif isinstance(error, commands.CheckFailure): return False

    return str(error)