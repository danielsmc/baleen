import baleen
import time

b = baleen.Baleen()

def getFriends(uid):
    time.sleep(60)
    friends = b.twitter.friends.ids(user_id=uid,count=5000,stringify_ids='true')['ids']
    b.redis.set("friends:%s"%uid,",".join(friends))
    print(len(friends))
    return friends

seed_sn = b.config['twitter']['seed']
seed_uid = b.twitter.users.show(screen_name=seed_sn)['id_str']
seed_friends = getFriends(seed_uid)
for fuid in seed_friends:
    getFriends(fuid)