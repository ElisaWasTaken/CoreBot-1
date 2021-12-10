import os, logging
from json import load, dump
from time import sleep
from cryptography.fernet import Fernet

logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.DEBUG)

def y_n() -> bool:
    while 1:
        i = input().lower()
        if i == 'y': 
            return True
        elif i == 'n':
            return False
        else:
            logging.error('Incorrect input, please try again (you must type y or n)')
            continue

def create_database():
    if os.path.exists('database.db'):
        logging.warning('Found already existing database. Would you like to overwrite it? (y/n)')
        if y_n():
            os.remove('database.db')
            logging.info('Removed existing database')
        else:
            logging.info('Database will be kept unchanged')
            return

    logging.info('Creating database...')
    from modules.db_manager import Database, SQLType, Data

    db = Database('database')
    logging.info('Adding tables...')
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
    logging.info('Finished creating database')
    logging.info('Creating data.json...')
    Data.empty_form().save()
    logging.info('Finished creating data.json')

def encrypt_token():
    logging.info('Generating key...')
    key = Fernet.generate_key()
    logging.info('Key generated')
    with open('key.key', 'wb') as key_file, open('token.crypt', 'wb') as token_file:
        key_file.write(key)
        token_file.write(Fernet(key).encrypt(input('Insert bot token here and press [ENTER]: ').encode()))
    logging.info('Token was successfully encrypted')

def update_config():
    data = load(open('config.json'))
    for v in data.copy():
        vtype = type(data[v])
        input_successful = False
        while not input_successful:
            try:
                if vtype == int:
                    logging.info(f'Please enter {v.replace("_", " ").upper()} (int).\nExample: 298570982701223523\n\
To fill it with the current value ({data[v]}) please press [ENTER] without providing anything: ')
                    i = input()
                    if i != '':
                        data[v] = int(i)
                elif vtype == list:
                    logging.info(f'Please enter {v.replace("_", " ").upper()} (list of integers), \
separate items from each other by SPACE. Do not add brackets or any other unnecessary symbols!\n\
Example: 1394876587612948792 349871987205345 598719837045654\n\
To fill it with the current value ({data[v]}) please press [ENTER] without providing anything: ')
                    i = input()
                    if i != '':
                        data[v] = [int(i) for i in i.split(' ')]
                else:
                    logging.info(f'Please enter {v.replace("_", " ").upper()}.\n\
To fill it with the current value ({data[v]}) please press [ENTER] without providing anything: ')
                    i = input()
                    if i != '':
                        data[v] = i

                logging.info(f'Recorded successfully')
                input_successful = True
            except:
                logging.error('Wrong input, please try again')
                print()

    dump(data, open('config.json', 'w'))
    logging.info('Successfully updated config')

def install_requirements():
    logging.info('Attempting to install requirements...')
    try:
        os.system('pip install -r requirements.txt')
        logging.info('Successfully installed requirements')
    except:
        logging.warning('Could not install requirements, please do manual installation')

print('Hello there, welcome to the setup of the core bot! You will be asked to fill in some values fort he bot to function properly.\n\
Please read CONFIG_INFO.TXT before!')
sleep(2)

while 1:
    mode = input('Please select what do you want to do:\n\
[0] - setup everything\n\
[1] - encrypt token\n\
[2] - create database\n\
[3] - update config\n\
[4] - install requirements: ').lower()
    if mode == '0':
        create_database()
        encrypt_token()
        update_config()
        install_requirements()

    elif mode == '1':
        encrypt_token()

    elif mode == '2':
        create_database()

    elif mode == '3':
        update_config()

    elif mode == '4':
        install_requirements()

    else:
        logging.error('Invalid mode')
        continue

    break