from json import load

_d = load(open('config.json'))

SERVER_ID = _d['server_id']

STAFF_ROLE_ID = _d['staff_role_id']
EVENT_MANAGER_ROLE_ID = _d['event_manager_role_id']
FILEMUTED_ROLE_ID = _d['filemuted_role_id']
LVL3_ROLE_ID = _d['lvl3_role_id']
LVL4_ROLE_ID = _d['lvl4_role_id']
LVL8_ROLE_ID = _d['lvl8_role_id']
LVL10_ROLE_ID = _d['lvl10_role_id']
SR_SEPARATOR_ROLE_ID = _d['sr_separator_role_id']
DM_MUTED_ROLE_ID = _d['dm_muted_role_id']
MUTED_ROLE_ID = _d['muted_role_id']
CHAT_REVIVE_ROLE_ID = _d['chat_revive_role_id']
NEW_VIDEO_ROLE_ID = _d['new_video_role_id']

ANNOUNCEMENTS_CHANNEL_ID = _d['announcements_channel_id']
GENERAL_CHANNEL_ID = _d['general_channel_id']
WELCOME_CHANNEL_ID = _d['welcome_channel_id']
LEAVE_LOGS_CHANNEL_ID = _d['leave_logs_channel_id']
YOUTUBE_CHANNEL_ID = _d['youtube_channel_id']
MEMBERS_TRACKER_ID = _d['members_tracker_id']
SCORE_TODAY_TRACKER_ID = _d['score_today_tracker_id']
TOP_CHATTER_TRACKER_ID = _d['top_chatter_tracker_id']
STAFF_REPORTS_CHANNEL_ID = _d['staff_reports_channel_id']
STAFF_CHANNEL_ID = _d['staff_channel_id']
LOG_CHANNEL_ID = _d['log_channel_id']
DELETED_LOG_CHANNEL_ID = _d['deleted_log_channel_id']
RULES_CHANNEL_ID = _d['rules_channel_id']

DM_CHANNELS_CATEGORY_ID = _d['dm_channels_category_id']

VIRUSTOTAL_APIKEY = _d['virustotal_apikey']
GOOGLE_API_KEY = _d['google_api_key']

ANTISPAM_IGNORED = _d['antispam_ignored']
AFK_IGNORED = _d['afk_ignored']
DELETE_IGNORED = _d['delete_ignored']
XP_IGNORED = _d['xp_ignored']