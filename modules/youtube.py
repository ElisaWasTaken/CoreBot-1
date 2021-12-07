from ids import GOOGLE_API_KEY
from requests import get

BASIC_API_URL = 'https://www.googleapis.com/youtube/v3/'

def is_id_valid(id):
    channel_data = get(f'{BASIC_API_URL}channels', params={'key': GOOGLE_API_KEY, 'part': 'id', 'id': id}).json()
    if channel_data['pageInfo']['totalResults'] >= 1:
        return True
    else:
        return False

def get_last_video(id):
    return get(f'{BASIC_API_URL}activities', params={'key': GOOGLE_API_KEY, 'part': 'contentDetails', 'channelId': id, 'maxResults': 1}).json()['items'][0]['contentDetails']['upload']['videoId']

def get_video_link(id):
    return f'https://youtube.com/watch?v={id}'