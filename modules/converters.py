from discord.ext.commands import Converter
from typing import Union
from datetime import timedelta
from re import search
from modules.exceptions import TimeConvertError, InvalidTopMode
from modules.db_manager import Data

class Time(Converter, timedelta):
    def __str__(self):
        days = self.days
        days = str(days) + ' days ' if days != 0 else ''
        hours = self.seconds // 3600
        hours = str(hours) + ' hours ' if hours != 0 else ''
        minutes = self.seconds // 60 % 60
        minutes = str(minutes) + ' minutes ' if minutes != 0 else ''
        seconds = self.seconds % 60
        seconds = str(seconds) + ' seconds ' if seconds != 0 else ''
        return f'{days}{hours}{minutes}{seconds}'

    async def convert(self, ctx, argument) -> Union[timedelta, None]:
        string = argument.lower()
        if string == 'perm':
            return None
        days, hours, minutes, seconds = 0, 0, 0, 0
        if 'd' in string:
            try:
                days = search(r'\d+d', string).group()
                days = int(search(r'\d+', days).group())
            except: days = 0
        if 'h' in string:
            try:
                hours = search(r'\d+h', string).group()
                hours = int(search(r'\d+', hours).group())
            except: hours = 0
        if 'm' in string:
            try:
                minutes = search(r'\d+m', string).group()
                minutes = int(search(r'\d+', minutes).group())
            except: minutes = 0
        if 's' in string:
            try:
                seconds = search(r'\d+s', string).group()
                seconds = int(search(r'\d+', seconds).group())
            except: seconds = 0

        if days == 0 and hours == 0 and minutes == 0 and seconds == 0:
            raise TimeConvertError(f'Couldn\'t convert `{argument}` to time')

        return timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

class Rule(Converter):
    def __init__(self):
        self.index = ''
        self.text = ''

    def __str__(self):
        return self.text

    async def convert(self, ctx, argument):
        rule_text = Data().get_rule(argument.lower())
        rule = Rule.__new__(Rule)
        rule.index = argument.lower()
        rule.text = rule_text

        return rule

class TopMode(Converter):
    async def convert(self, ctx, argument):
        argument = argument.lower()
        if argument in ('total', 'daily', 'weekly'):
            return argument

        raise InvalidTopMode(argument)