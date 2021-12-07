from json import load, dump
from time import sleep
from cryptography.fernet import Fernet
from os import mkdir

print('Hello there, welcome to the setup of the core bot! You will be asked to fill in some values fort he bot to function properly.\n\
Please read CONFIG_INFO.TXT before!')
sleep(2)
print('-'*20)
if input('Would you like to create data files? Respond with "y" if you would, respond with the any other key if not.\n\
Use this only if you haven\'t created data files before').lower() == 'y':
    mkdir('.tmp')
    mkdir('backgrounds')
    print('Creating database...')
    from modules.db_manager import Database, SQLType, Data

    db = Database('database')
    db.create_table(
        'members',
        id=SQLType.INT,
        xp_total=SQLType.INT,
        xp_daily=SQLType.INT,
        xp_weekly=SQLType.INT,
        xp_cooldown=SQLType.REAL,
        afk=SQLType.TEXT,
        selfrole=SQLType.INT,
    )
    db.create_table(
        'cases',
        id=SQLType.INT,
        type=SQLType.TEXT,
        target_id=SQLType.INT,
        responsible_id=SQLType.INT,
        reason=SQLType.TEXT,
        applied_at=SQLType.REAL,
        applied_till=SQLType.REAL,
        additional=SQLType.TEXT
    )
    db.create_table(
        'youtubers',
        id=SQLType.INT,
        youtube_id=SQLType.TEXT,
        last_video=SQLType.TEXT,
        premium=SQLType.BOOL,
        times_advertised=SQLType.INT
    )
    print('Finished creating database')
    print('Creating data.json...')
    Data.empty_form().save()
    print('Finished creating data.json')
    print('Data files created successfully!')
    print('-'*20)

key = Fernet.generate_key()

with open('key.key', 'wb') as key_file, open('token.crypt', 'wb') as token_file:
    key_file.write(key)
    token_file.write(Fernet(key).encrypt(input('Insert bot token here and press [ENTER]: ').encode()))

print('Your token was successfully encrypted with Fernet technology.')
print('-'*20)
data = load(open('config.json'))
for v in data.copy():
    vtype = type(data[v])
    if vtype == int:
        data[v] = int(input(f'Please enter {v.replace("_", " ").title()} (int): '))
    elif vtype == list:
        data[v] = [int(i) for i in input(f'Please enter {v.replace("_", " ").title()} (list of integers), separate items from each other by SPACE: ').split(' ')]
    else:
        data[v] = input(f'Please enter {v.replace("_", " ").title()}: ')
dump(data, open('config.json', 'w'))
print('All values recorded!')
