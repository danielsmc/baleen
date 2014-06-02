#!/usr/bin/python

import collections
import json
import MySQLdb
import MySQLdb.cursors
import time
import twitter

with open("config.json") as fh:
    config = json.load(fh)

auth=twitter.OAuth(config['twitter']['access_token'],
                   config['twitter']['access_token_secret'],
                   config['twitter']['consumer_key'],
                   config['twitter']['consumer_secret'])

t = twitter.Twitter(auth=auth)

conn = MySQLdb.connect(
    host=config['mysql']['host'],
    port=config['mysql']['port'],
    user=config['mysql']['user'],
    passwd=config['mysql']['passwd'],
    db=config['mysql']['database'],
    use_unicode=True,
    charset="utf8mb4",
    cursorclass = MySQLdb.cursors.DictCursor)
conn.autocommit(True)
cur = conn.cursor()
cur.execute("SET time_zone='+0:00'")


last_friend_call_ts = 0
def rate_limited_friend_call(screen_name,cursor):
    global last_friend_call_ts
    secs_to_wait = last_friend_call_ts+65-time.time()
    if secs_to_wait > 0:
        time.sleep(secs_to_wait)
    last_friend_call_ts = time.time()
    return t.friends.ids(screen_name=screen_name,cursor=cursor)


def get_friends(screen_name):
    # if screen_name in friend_cache:
    #     return friend_cache[screen_name]
    # else:
    all_ids = []
    cursor = -1
    while (cursor != 0):
        response = rate_limited_friend_call(screen_name,cursor)
        all_ids.extend(response['ids'])
        cursor = response['next_cursor']
    # friend_cache[screen_name] = all_ids
    return all_ids

def get_screen_names(ids):
    out  = []
    while len(ids) > 0:
        out.extend([x['screen_name'] for x in t.users.lookup(user_id=",".join(map(str,ids[:100])))])
        ids=ids[100:]
    return out


# with open('friend_cache.json') as fh:
#     friend_cache = json.load(fh)

seeds = get_screen_names(get_friends(config['twitter']['seed']))

impacts = collections.Counter()
for seed in seeds:
    print seed
    impacts.update(get_friends(seed))
    print len(impacts)

# with open('friend_cache.json','w') as fh:
#     json.dump(friend_cache,fh)

cur.execute("UPDATE users SET impact = 0")

for user_id,impact in impacts.iteritems():
    cur.execute("INSERT INTO users (user_id,impact) VALUES (%s,%s) ON DUPLICATE KEY UPDATE impact = %s",(user_id,impact,impact))