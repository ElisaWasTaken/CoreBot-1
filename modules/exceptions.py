from ids import RULES_CHANNEL_ID
from discord.ext.commands import CommandError
from discord import Member

class LengthInequality(Exception):
    def __init__(self, len1: int, len2: int):
        self.len1 = len1
        self.len2 = len2

    def __str__(self):
        return f'Lists\' lengths are not equal: {self.len1} != {self.len2}'

class StaffOnly(CommandError):
    def __init__(self, message='This command is **staff only**'):
        super().__init__(message)

class OwnerOnly(CommandError):
    def __init__(self, message='This command is **owner only**'):
        super().__init__(message)

class TimeOut(CommandError):
    def __init__(self, message='The response timed out'):
        super().__init__(message)

class InputCancelled(CommandError):
    def __init__(self, message='The input was cancelled'):
        super().__init__(message)

class NoData(CommandError):
    def __init__(self, message='No such data'):
        super().__init__(message)

class TimeConvertError(CommandError):
    def __init__(self, message='Invalid time provided'):
        super().__init__(message)

class DJOnly(CommandError):
    def __init__(self, message='This command may only be used by a DJ'):
        super().__init__(message)

class NoRule(CommandError):
    def __init__(self, rule_index):
        super().__init__(f'Rule `{rule_index}` does not exist. \
Look up a valid rule code in <#{RULES_CHANNEL_ID}>')

class HierarchyError(CommandError):
    def __init__(self, user: Member, target: Member):
        msg = None
        if user.top_role.position == target.top_role.position:
            msg = f'You cannot use this command on someone \
with the same top role with you ({user.top_role.mention})'
        else:
            msg = f'Top role of your target is higher at position than yours:\n\
{target.top_role.mention} > {user.top_role.mention}'

        super().__init__(msg)

class PermissionDenied(CommandError):
    def __init__(self, message='You do not have permission to use this command \
because your access was restricted'):
        super().__init__(message)

class InvalidBlacklistMode(CommandError):
    def __init__(self, message='This mode does not exist.\nAvalaible modes: `common`, `wild`, `super`'):
        super().__init__(message)

class InvalidTopMode(CommandError):
    def __init__(self, mode):
        super().__init__(message=f'Mode `{mode}` does not exist.\nAvalaible modes: `total`, `daily`, `weekly`')