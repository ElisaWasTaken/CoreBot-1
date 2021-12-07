import discord
from typing import Union
from discord.ext.commands import Context, Bot
from modules.exceptions import InputCancelled, TimeOut, HierarchyError, DJOnly
from modules.db_manager import Data
from datetime import datetime, timedelta
from emoji import demojize
from emojis import decode as emdecode
from string import ascii_letters

async def wait_for_message(ctx: Context, bot: Bot, msg: discord.Message, timeout: int = 30) -> discord.Message:
    def check(m):
        return m.channel.id == ctx.channel.id and m.author.id == ctx.author.id

    try:
        m = await bot.wait_for('message', check=check, timeout=timeout)
    except TimeoutError:
        raise TimeOut(msg)
    if m.content.lower() == 'cancel':
        raise InputCancelled(msg)
    return m

async def wait_for_confirmation(ctx: Context, bot: Bot, msg: discord.Message, timeout: int = 10):
    def check(r, u):
        return u == ctx.author and r.message == msg and str(r.emoji) == '✅'

    await msg.add_reaction('✅')
    try:
        await bot.wait_for('reaction_add', check=check, timeout=timeout)
    except TimeoutError:
        raise TimeOut(msg)

def extract_json(json):
    new_dict = {}
    for i in json:
        new_dict[int(i)] = json[i]

    return new_dict

def td_to_str(time: timedelta):
    if time == None: return 'permanent'
    string = ''
    if time.days > 0:
        string += f'{time.days} days'
    if time.seconds // 3600 > 0:
        string += f'{time.seconds // 3600} hours'
    if time.seconds // 60 % 60 > 0:
        string += f'{time.seconds // 60 % 60} minutes'
    if time.seconds % 60 > 0:
        string += f'{time.seconds % 60} seconds'

    return string

def td_to_timestamp(time: timedelta, mode = 'F'):
    if time == None: return 'manual restrictions lifting'
    return f'<t:{int((datetime.now()+time).timestamp())}:{mode}>'

def checkprint(s):
	s = s.lower()
	s = demojize(s)
	s = emdecode(s)
	checkstring = "qwertyuiopasdfghjklzxcvbnm1234567890@#$_&-+()/*\"':;!?,.—–~`|•√π÷×¶∆£¢€¥^°={}\\%©®™✓[]<>‚‘’„“”±’ "
	for symbol in s:
		if not symbol in checkstring and symbol != '\n' and symbol != '\t': return False
	return True

async def addReactions(m: discord.Message, emojis=['✅', '❌']):
    for emoji in emojis:
        await m.add_reaction(emoji)
		
def checkword(s):
    blocked = []
    s = s.lower()
    nospace = s.replace(" ", "")
    for symb in "~`|•√π÷×¶∆£¢€¥^°={}\\%©®™✓[]<>@#$_&-+()/*\"':;!?.,‘’1234567890":
        d = {'1': 'i',
        '!': 'i',
        '0': 'o',
        '$': 's'}
        if symb in d:
            s = s.replace(symb, d[symb])
        else:
            s = s.replace(symb, "")
    splitted = s.split(" ")
    foundSuper = False
    blacklist = Data().blacklist
    for word in splitted:
        if word in blacklist.common: blocked.append(word)
    for w in blacklist.wildcard:
        if w in s and not w in blocked: blocked.append(word)
    for word in blacklist.super:
        if word in nospace and not word in blocked:
            blocked.append(word)
            foundSuper = True
    if len(blocked) > 0:
        blocked = set(blocked)
        if foundSuper:
            for word in blocked:
                nospace = nospace.replace(word, '#'*len(word))
            return [False, nospace]
        else:
            for word in blocked:
                s = s.replace(word, '#'*len(word))
            return [False, s]
    else:
        return [True, None]

def antispam(text):
    basic_text = text
    s = text
    for symb in "~`|•√π÷×¶∆£¢€¥^°={}\\%©®™✓[]@#$_&-+()/*\"'';!?.,‘’1234567890<>:":
        if symb in ("1", "!"):
            s = s.replace(symb, "i")
        elif symb == "0":
            s = s.replace(symb, "o")
        else:
            s = s.replace(symb, "")
    text = s
    words_list = text.split()
    words = set(words_list)
    if len(text) > 30 and len(words_list) <= 1 and basic_text.count("<:") > len(words_list): return [False, text]
    for word in words:
        if words_list.count(word) >= 5: return [False, word]
        if len(word) > 10:
            letters = set(word)
            if len(letters) < len(word)//3 and len(letters) > 3: return [False, word]
    return [True, None]

def check_nick(nick: str) -> Union[str, None]:
    typable_count = 0
    is_typable = False
    rule_broken = None
    if not checkword(nick)[0]:
        rule_broken = '6.3'
    for s in nick:
        if s in ascii_letters+"1234567890@#$_&-+()/*\"':;!?,.—–~`|•√π÷×¶∆£¢€¥^°={}\\%©®™✓[]<>‚‘’„“”±’ ":
            typable_count += 1
        else:
            typable_count = 0
        
        if typable_count >= 3:
            is_typable = True
            break

    if not is_typable:
        rule_broken = '6.2'

    return rule_broken

async def check_member_nick(member: discord.Member):
    rule_broken = check_nick(member.display_name)
    if rule_broken != None:
        await member.edit(nick=f'Bad nick (rule {rule_broken})', reason=rule_broken)

    return rule_broken

def check_hierarchy(user: discord.Member, target: discord.Member):
    if user.top_role.position <= target.top_role.position:
        raise HierarchyError(user, target)

def is_dj():
    def subf(ctx):
        if not ctx.author.guild_permissions.manage_guild \
            and not 'DJ' in [r.name for r in ctx.author.roles] \
            and (ctx.voice_client != None or len(ctx.voice_client.channel.members) <= 1):
            raise DJOnly

        return True

    return discord.ext.commands.check(subf)

def get_dict_slice(d, start, end):
    new_dict = {}
    for i in range(start, end+1):
        try:
            new_dict[i] = d[i]
        except: break

    return new_dict