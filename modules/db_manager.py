import sqlite3, os, ids
from discord.ext import commands
from discord import Intents, Guild, Member, Role, TextChannel, Embed
from os import listdir
from cryptography.fernet import Fernet
from typing import Optional, Any, Union
from datetime import datetime, date, timedelta
from modules.exceptions import LengthInequality, NoData, NoRule
from modules.youtube import *
from modules.constants import TaskStatus
from json import load, dump
from numpy import array as np_array

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

class FetchMode:
    NONE = 0
    ONE = 1
    ALL = 2

class SQLType:
    TEXT = 'TEXT'
    INT = 'INT'
    REAL = 'REAL'
    BOOL = 'BOOL'
    BLOB = 'BLOB'

    @staticmethod
    def get_type(obj):
        types_dict = {
            str: SQLType.TEXT,
            int: SQLType.INT,
            float: SQLType.REAL,
            bool: SQLType.BOOL
        }
        return types_dict[type(obj)]

    @staticmethod
    def PRIMARY_KEY(type):
        return f'{type} PRIMARY KEY'

class Database():
    def __init__(self, name) -> None:
        self.name = name
        tables = self.execute('SELECT name FROM sqlite_master WHERE type="table"', FetchMode.ALL)
        self.tables = [Table(self, t[0]) for t in tables] #type: list[Table]

    def connect(self):
        self.con = sqlite3.connect(self.name+'.db')
        self.cur = self.con.cursor()

    def execute(self, code, fetch_mode: FetchMode = 0) -> Optional[Any]:
        self.connect()
        result = self.cur.execute(code)
        self.con.commit()

        if fetch_mode == FetchMode.NONE:
            result = None

        elif fetch_mode == FetchMode.ONE:
            result = result.fetchone()

        elif fetch_mode == FetchMode.ALL:
            result = result.fetchall()

        self.disconnect()
        return result

    def disconnect(self):
        self.con.close()
        self.con = None
        self.cur = None

    def get_table(self, name):
        for table in self.tables:
            if table.name == name:
                return table

        return None

    def create_table(self, _name, **columns: SQLType):
        cols = []
        for title in columns:
            cols.append(f'{title} {columns[title]}')
        self.execute(f'CREATE TABLE {_name} ({", ".join(cols)})')
        newtable = Table(self, _name)
        self.tables.append(newtable)
        return newtable

class Table():
    def __init__(self, db: Database, name) -> None:
        self.db = db
        self.name = name
        self.columns = self.get_columns()

    def get_columns(self):
        return [i[1] for i in self.db.execute(f'PRAGMA table_info({self.name})', FetchMode.ALL)]

    def get_value(self, **conditions):
        result = list(self.db.execute(f'SELECT * FROM {self.name} WHERE {get_condition(conditions)}', FetchMode.ONE))
        return cross_lists(self.columns, result)

    def get_all_values(self, **conditions):
        result = self.db.execute(f'SELECT * FROM {self.name} WHERE {get_condition(conditions)}', FetchMode.ALL)
        return [cross_lists(self.columns, list(data)) for data in result]

    def get_all_values_manual_conditions(self, conditions):
        result = self.db.execute(f'SELECT * FROM {self.name} WHERE {conditions}', FetchMode.ALL)
        return [cross_lists(self.columns, list(data)) for data in result]

    def get_all_values_no_condition(self):
        result = self.db.execute(f'SELECT * FROM {self.name}', FetchMode.ALL)
        return [cross_lists(self.columns, list(data)) for data in result]

    def insert_row(self, data: list):
        data = [to_sql_format(obj) for obj in data]
        self.db.execute(f'INSERT INTO {self.name} ({", ".join(self.columns)}) VALUES ({", ".join(data)})')

    def delete(self, **conditions):
        self.db.execute(f'DELETE FROM {self.name} WHERE {get_condition(conditions)}')

    def update(self, conditions: dict, **data):
        data_txt = [f'{col} = {to_sql_format(data[col])}' for col in data]

        self.db.execute(f'UPDATE {self.name} SET {", ".join(data_txt)} WHERE {get_condition(conditions)}')

    def exists(self, **conditions):
        return len(self.db.execute(f'SELECT * FROM {self.name} WHERE {get_condition(conditions)}', FetchMode.ALL)) > 0

def date_to_datetime(date: date) -> datetime:
    return datetime(date.year, date.month, date.day)

def to_sql_format(value):
    if type(value) in (int, float):
        return str(value)
    elif type(value) == str:
        return f'"{value}"'
    elif type(value) == bytes:
        return str(value.decode())
    elif type(value) == bool:
        return str(value).lower()
    elif value == None:
        return 'NULL'

def cross_lists(list1, list2):
    result_dict = {}
    if len(list1) != len(list2):
        raise LengthInequality(len(list1), len(list2))

    for i in range(len(list1)):
        result_dict[list1[i]] = list2[i]

    return result_dict

def get_condition(conditions):
    for i in conditions.copy():
        conditions[i] = to_sql_format(conditions[i])

    condition = ''
    for i in conditions:
        condition += f'{i} = {conditions[i]} AND '
    condition = condition[:-5]

    return condition

class Youtuber():
    def __init__(self, id, youtube_id, is_premium):
        self.id = id
        self.youtube_id = youtube_id
        self.last_video = get_last_video(self.youtube_id)
        self.premium = is_premium
        self.times_advertised = 0

    @classmethod
    def from_dict(cls, data):
        obj = cls.__new__(cls)
        obj.id = data['id']
        obj.youtube_id = data['youtube_id']
        obj.premium = data['premium']
        obj.last_video = data['last_video']
        obj.times_advertised = data['times_advertised']
        return obj

    def delete(self):
        Database('database').get_table('youtubers').delete(id=self.id)

    def save(self):
        table = Database('database').get_table('youtubers')
        if not table.exists(id=self.id, youtube_id=self.youtube_id):
            table.insert_row(
                [self.id, self.youtube_id, self.last_video, self.premium, self.times_advertised]
            )
        else:
            table.update({'id': self.id, 'youtube_id': self.youtube_id},
                last_video=self.last_video,
                premium=self.premium,
                times_advertised=self.times_advertised
                )

    def update_videos(self):
        last_video = get_last_video(self.youtube_id)
        if last_video == self.last_video:
            return None
        else:
            self.last_video = last_video
            self.save()
            return last_video

class Data():
    def __init__(self):
        data = load(open('data.json'))

        self.case_id: int = data['case_id']
        self.task_id: int = data['task_id']
        self.afkIgnored: list = data['afk_ignored']
        self.rules: dict = data['rules']
        self.score_today: int = data['score_today']
        self.locked_channels: list = data['locked_channels']
        self.bad_links: list = data['bad_links']
        self.normal_links: list = data['good_links']
        self.score_multiplier: int = data['score_multiplier']
        self.report_ignored: list = data['report_ignored']
        self.notified_youtubers: list = data['notified_youtubers']
        self.voted_users: list = data['voted_users']
        self.tasks = []

        self.blacklist = BlacklistData.from_dict(data['blacklist'])
        self.resets = ResetsData.from_dict(data['resets'])
        
        self.staff_votes = extract_json(data['staff_votes'])
        self.youtube_queue = extract_json(data['youtube_queue'])
        self.staff_points = extract_json(data['staff_points'])
        self.levels = extract_json(data['levels'])

        self.dm_channels = {} #type: dict[int, DMChannel]
        for i in data['dm_channels']:
            self.dm_channels[int(i)] = DMChannel.from_dict(data['dm_channels'][i])

        self.reaction_roles = {} #type: dict[int, dict[Union[int, str], int]]
        for i in data['reaction_roles']:
            key = data['reaction_roles'][i]
            try: parse_key = int(key)
            except: pass
            self.reaction_roles[int(i)] = {parse_key: data['reaction_roles'][i][key]}

    @classmethod
    def empty_form(cls):
        obj = cls.__new__(cls)
        obj.case_id = 0
        obj.task_id = 0
        obj.blacklist = BlacklistData()
        obj.levels = {}
        obj.afkIgnored = []
        obj.rules = {}
        obj.score_today = 0
        obj.resets = ResetsData()
        obj.locked_channels = []
        obj.bad_links = []
        obj.normal_links = []
        obj.reaction_roles = {}
        obj.staff_points = {}
        obj.score_multiplier = 1
        obj.report_ignored = []
        obj.youtube_queue = {}
        obj.notified_youtubers = []
        obj.tasks = []
        obj.staff_votes = {}
        obj.voted_users = []
        obj.dm_channels = {}
        return obj

    def save(self):
        dm_channels_dumpable = {}
        for i in self.dm_channels:
            dm_channels_dumpable[i] = self.dm_channels[i].to_dict()
        with open('data.json', 'w') as f:
            dump({
                'case_id': self.case_id,
                'task_id': self.task_id,
                'blacklist': self.blacklist.to_dict(),
                'levels': self.levels,
                'afk_ignored': self.afkIgnored,
                'rules': self.rules,
                'score_today': self.score_today,
                'resets': self.resets.to_dict(),
                'locked_channels': self.locked_channels,
                'bad_links': self.bad_links,
                'good_links': self.normal_links,
                'reaction_roles': self.reaction_roles,
                'staff_points': self.staff_points,
                'score_multiplier': self.score_multiplier,
                'dm_channels': dm_channels_dumpable,
                'report_ignored': self.report_ignored,
                'youtube_queue': self.youtube_queue,
                'notified_youtubers': self.notified_youtubers,
                'staff_votes': self.staff_votes,
                'voted_users': self.voted_users,
                'reaction_roles': self.reaction_roles
            }, f)

    @staticmethod
    def get_member(member_id):
        members_table = Database('database').get_table('members')
        if members_table.exists(id=member_id):
            return MemberData.from_dict(members_table.get_value(id=member_id))
        else:
            return MemberData(member_id)

    @staticmethod
    def get_case(id):
        cases_table = Database('database').get_table('cases')
        if cases_table.exists(id=id):
            return Case.from_dict(cases_table.get_value(id=id))

        raise NoData('No such case')

    @staticmethod
    def get_youtuber(id):
        youtubers_table = Database('database').get_table('youtubers')
        if youtubers_table.exists(id=id):
            return Youtuber.from_dict(youtubers_table.get_value(id=id))
        
        raise NoData('No such youtuber')

    @staticmethod
    def get_all_members():
        return [MemberData.from_dict(d) for d in Database('database').get_table('members').get_all_values_no_condition()]

    @staticmethod
    def get_all_cases():
        return [Case.from_dict(d) for d in Database('database').get_table('cases').get_all_values_no_condition()]

    @staticmethod
    def get_all_recent_cases(days=1):
        timestamp_threshold = (datetime.now()-timedelta(days=days)).timestamp()
        return [Case.from_dict(d) for d in Database('database').get_table('cases')\
            .get_all_values_manual_conditions(f'applied_till NOT NULL AND applied_till > {timestamp_threshold}')]

    @staticmethod
    def get_all_youtubers():
        return [Youtuber.from_dict(d) for d in Database('database').get_table('youtubers').get_all_values_no_condition()]

    @staticmethod
    def get_top_scores(mofidier = 'total'):
        result = Database('database').execute(f'''SELECT id, xp_{mofidier} AS xp FROM members WHERE xp != 0 ORDER BY xp DESC''', FetchMode.ALL)
        d = {}
        for index, item in enumerate(result, 1):
            d[index] = item
        return d

    def get_rule(self, index):
        try: 
            return self.rules[index]
        except KeyError:
            raise NoRule(index)

    def create_reaction_role(self, message_id, emoji, role_id):
        if not message_id in self.reaction_roles:
            self.reaction_roles[message_id] = {emoji: role_id}
        else:
            self.reaction_roles[message_id][emoji] = role_id

        self.save()

    def add_case(self, case):
        self.case_id += 1
        self.save()
        case.save()

    def add_level(self, score_required, role_id):
        self.levels[score_required] = role_id
        self.save()
        
    def remove_level(self, score):
        try:
            self.levels.pop(score)
            self.save()
        except: raise NoData()

class DMChannel():
    def __init__(self, id: int, owner: int) -> None:
        self.id = id
        self.owner = owner
        self.closes_at = datetime.now()+timedelta(days=1)

    @classmethod
    def from_dict(cls, data):
        obj = cls(data['id'], data['owner'])
        obj.closes_at = datetime.fromtimestamp(data['closes_at'])
        return obj

    def to_dict(self):
        return {
            'id': self.id,
            'owner': self.owner,
            'closes_at': self.closes_at.timestamp()
        }

    async def close(self, bot):
        try:
            Data().dm_channels.pop(self.id)
        except: pass
        try:
            await bot.server.get_channel(self.id).delete()
        except: pass

class ResetsData():
    def __init__(self):
        now = datetime.now()
        self.daily = datetime.date(now+timedelta(days=1))
        self.weekly = datetime.date(now+timedelta(days=7-now.weekday()))
        now += timedelta(days=31)
        self.monthly = date(now.year, now.month, 1)

    @classmethod
    def from_dict(cls, data):
        obj = cls.__new__(cls)
        obj.daily = datetime.fromtimestamp(data['daily']).date()
        obj.weekly = datetime.fromtimestamp(data['weekly']).date()
        obj.monthly = datetime.fromtimestamp(data['monthly']).date()
        return obj

    def to_dict(self):
        return {
            'daily': date_to_datetime(self.daily).timestamp(),
            'weekly': date_to_datetime(self.weekly).timestamp(),
            'monthly': date_to_datetime(self.monthly).timestamp()
        }

class MemberData():
    '''A data class that initializates member's information.'''
    def __init__(self, id):
        self.id = id
        self.xp = XPData()
        self.afk = None
        self.selfrole = None

    @classmethod
    def from_dict(cls, data):
        obj = cls.__new__(cls)
        obj.id = data['id']
        obj.xp = XPData()
        obj.xp.total = data['xp_total']
        obj.xp.daily = data['xp_daily']
        obj.xp.weekly = data['xp_weekly']
        obj.xp.cooldown = datetime.fromtimestamp(data['xp_cooldown'])
        obj.afk = data['afk']
        obj.selfrole = data['selfrole']
        return obj

    def save(self):
        table = Database('database').get_table('members')
        if not table.exists(id=self.id):
            table.insert_row(
                [self.id, self.xp.total, self.xp.daily, self.xp.weekly, self.xp.cooldown.timestamp(), self.afk, self.selfrole]
            )
        else:
            table.update({'id': self.id},
                xp_total=self.xp.total,
                xp_daily=self.xp.daily,
                xp_weekly=self.xp.weekly,
                xp_cooldown=self.xp.cooldown.timestamp(),
                afk=self.afk
                )

    def get_leaderboard_place(self, modifier='total'):
        return list(np_array(Database('database').execute(f'''SELECT id, xp_{modifier} AS xp FROM members WHERE xp != 0 ORDER BY xp DESC''', FetchMode.ALL))[:,0]).index(self.id) + 1

    def get_warn(self, id):
        try:
            return Case.from_dict(Database('database').get_table('cases').get_value(id=id, type='warn'))
        except: 
            raise NoData('No such warning')

    def get_all_warns(self):
        return [Case.from_dict(d) for d in Database('database').get_table('cases').get_all_values(target_id=self.id, type='warn')]

    def get_all_warns_with_reason(self, reason):
        return [Case.from_dict(d) for d in Database('database').get_table('cases').get_all_values(target_id=self.id, type='warn', reason=reason)]

    def get_bg(self):
        return f'backgrounds/{self.id}.png' if os.path.exists(f'backgrounds/{self.id}.png') else None

class XPData():
    '''A data class that initializates member's XP data.'''
    def __init__(self):
        self.total = 0
        self.daily = 0
        self.weekly = 0
        self.cooldown = datetime.now()

class Case():
    '''A data class that represents moderation case.
    Types of cases:
    --- "ban"
    --- "mute"
    --- "warn"
    --- "kick"
    --- "filemute"'''
    def __init__(self, target_id, type, responsible_id, length, reason, additional=None):
        self.victim_id = target_id
        self.id = Data().case_id
        self.type = type
        self.responsible_id = responsible_id
        self.applied_at = datetime.now()
        self.length = length
        self.reason = reason
        if length != None:
            self.applied_till = self.applied_at + length
        else:
            self.applied_till = None
        self.additional = additional

    @classmethod
    def from_dict(cls, data):
        if data['applied_till'] == None: data['length'] = None
        else:
            data['length'] = timedelta(seconds=(datetime.fromtimestamp(data['applied_till']) - datetime.fromtimestamp(data['applied_at'])).total_seconds())
        obj = cls.__new__(cls)
        obj.id = data['id']
        obj.type = data['type']
        obj.victim_id = data['target_id']
        obj.responsible_id = data['responsible_id']
        obj.length = data['length']
        obj.reason = data['reason']
        obj.additional = data['additional']
        obj.applied_at = datetime.fromtimestamp(data['applied_at'])
        obj.applied_till = datetime.fromtimestamp(data['applied_till']) if data['applied_till'] != None else None
        return obj

    def save(self):
        table = Database('database').get_table('cases')
        applied_till_dumpable = self.applied_till.timestamp() if self.applied_till != None else None
        if not table.exists(id=self.id):
            table.insert_row(
                [self.id, self.type, self.victim_id, self.responsible_id, self.reason, self.applied_at.timestamp(),
                applied_till_dumpable, self.additional]
            )
        else:
            table.update({'id': self.id},
                type=self.type)

    def delete(self):
        Database('database').get_table('cases').delete(id=self.id)
        if self.type != 'warn':
            self.type = 'un'+self.type
            self.length = None

class BlacklistData():
    def __init__(self):
        self.common = []
        self.wildcard = []
        self.super = []

    @classmethod
    def from_dict(cls, data):
        obj = cls.__new__(cls)
        obj.common = data['common']
        obj.wildcard = data['wildcard']
        obj.super = data['super']
        return obj

    def to_dict(self):
        return {
            'common': self.common,
            'wildcard': self.wildcard,
            'super': self.super}

class ASMTracker():
    def __init__(self):
        self.enabled = True
        self.messages = 0
        self.reset = datetime.now()+timedelta(seconds=20)
        self.before_down = 3

    def update(self):
        self.reset = datetime.now()+timedelta(seconds=20)
        self.messages = 0

class Track():
    def __init__(self, server, name, url, description, requested_by: Member):
        self.server = server
        self.name = name
        self.url = url
        self.description = description
        self.requested_by = requested_by

class CoreBot(commands.Bot):
    def __init__(self, version, **options):
        super().__init__(
            command_prefix='//',
            help_command=None,
            intents=Intents.all(),
            case_insentive=True,
            strip_after_prefix=True, **options)
        self.__version__ = version

    def load_all_extensions(self):
        for name in listdir('ext'):
            if name.endswith('.py'): self.load_extension(f'ext.{name[:-3]}')

    def load_variables(self):
        self.server: Guild = self.get_guild(ids.SERVER_ID)
        self.staff: Role = self.server.get_role(ids.STAFF_ROLE_ID)
        self.muted: Role = self.server.get_role(ids.MUTED_ROLE_ID)
        self.filemuted: Role = self.server.get_role(ids.FILEMUTED_ROLE_ID)
        self.log_channel: TextChannel = self.server.get_channel(ids.LOG_CHANNEL_ID)
        self.launched_at = datetime.now()
        self.local_warns = {}
        self.queue = []
        self.now_playing = None
        self.next_reset = datetime.now()+timedelta(minutes=30)

    def run(self):
        super().run(self.get_token())

    @staticmethod
    def get_token():
        with open('key.key', 'rb') as key, open('token.crypt', 'rb') as token:
            token = Fernet(key.read()).decrypt(token.read()).decode()

        return token

    async def logCase(self, case):
        d = {'mute': 0xffff00,
            'ban': 0xff0000,
            'kick': 0xffff00,
            'warn': 0xffff00,
            'filemute': 0xffff00}
        e = {'mute': '🔇',
            'ban': '🔨',
            'kick': '🦶',
            'warn': '⚠️',
            'filemute': '🔇',
            'unfilemute': '🔓',
            'unmute': '🔊',
            'unban': '🔓'}
        if case.type.startswith('un'):
            color = 0x00ff00
        else:
            color = d[case.type]

        title = f'#{case.id} | ({e[case.type]} {case.type})'
        target = self.server.get_member(case.victim_id)
        responsibleUser = self.server.get_member(case.responsible_id)
        desc = f'''Target user: **{target}** ({target.mention})
Responsible moderator: **{responsibleUser}** ({responsibleUser.mention})
Length: `{td_to_str(case.length)}` (until {td_to_timestamp(case.length)})
Reason: **{case.reason}**
'''
        await self.log_channel.send(
            embed=Embed(color=color,
                                title=title,
                                description=desc,
                                timestamp=datetime.now()))

    async def updateLocalWarns(self, id):
        if self.local_warns[id] >= 3:
            await self.server.get_member(id).add_roles(self.muted)
            await self.add_case(Case(id, 'mute', self.user.id, timedelta(minutes=15), 'automod'))

    async def add_case(self, case):
        Data().add_case(case)
        if not case.type.startswith('un'):
            await self.logCase(case)