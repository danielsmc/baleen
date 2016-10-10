import baleen
import sys
import time

b = baleen.Baleen()

def doWeHave(uid):
    return b.redis.exists("friends:%s"%uid)

def getFriends(uid):
    key = "friends:%s"%uid
    res = b.redis.get(key)
    if res is not None:
        return res.decode('utf-8').split(',')
    else:
        time.sleep(60)
        friends = b.twitter.friends.ids(user_id=uid,count=5000,stringify_ids='true')['ids']
        b.redis.set("friends:%s"%uid,",".join(friends))
        print(len(friends))
        return friends

def doSeed(sn):
    print(sn)
    seed_uid = b.twitter.users.show(screen_name=sn)['id_str']
    seed_friends = getFriends(seed_uid)
    to_fetch = [x for x in seed_friends if not doWeHave(x)]
    print("need to fetch %s out of %s."%(len(to_fetch),len(seed_friends)))
    for fuid in to_fetch:
        getFriends(fuid)

for sn in sys.argv[1:]:
    try:
        doSeed(sn)
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as err:
        print(err)
