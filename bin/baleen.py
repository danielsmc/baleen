import json
import redis
import twitter
import os
import sys
import time
import traceback


class Baleen:
    def __init__(self):
        config_path = os.path.join(sys.path[0],"../config.json")
        with open(config_path) as fh:
            self.config = json.load(fh)

        tc = self.config['twitter']
        auth=twitter.OAuth( tc['access_token'],
                            tc['access_token_secret'],
                            tc['consumer_key'],
                            tc['consumer_secret'])

        self.twitter = twitter.Twitter(auth=auth)
        self.twitterstream = twitter.TwitterStream(auth=auth)

        self.redis = redis.StrictRedis(host='localhost', port=6379, db=0)

        self.oneyear = 60 * 60 * 24 * 365

    def getFollowGraph(self):
        def makeKey(uid):
            return "friends:%d"%uid
        def parseRaw(res):
            return {int(x) for x in res.decode('utf-8').split(',')} if res else {}
        def fetchFriends(uid):
            return parseRaw(self.redis.get(makeKey(uid)))
        def fetchFriendsMulti(uids):
            uid_list = list(uids)
            res_list = map(parseRaw,self.redis.mget(map(makeKey,uid_list)))
            return {fid:ffriends for fid,ffriends in zip(uid_list,res_list)}
            
        seed_uid = self.getUserId(self.config['twitter']['seed'])
        seed_friends = fetchFriends(seed_uid)
        out = fetchFriendsMulti(seed_friends)
        out[seed_uid]=seed_friends
        return out

    def getUserId(self,screen_name):
        res = self.redis.get("user_id:%s"%screen_name)
        if res is not None:
            return int(res)
        else:
            uid = self.twitter.users.show(screen_name=screen_name)['id']
            self.redis.set("user_id:%s"%screen_name,uid)
            return uid

    def getTweet(self,tid):
        res = self.redis.get("tweet:%s"%tid)
        if res is not None:
            return json.loads(res.decode('utf-8'))

    def getUrl(self,url):
        res = self.redis.get("url:%s"%url)
        if res is not None:
            return res.decode('utf-8')

def loopForever(func):
    sleep_time = 1
    while True:
        if sleep_time > 1:
            print("sleeping for %s seconds"%sleep_time)
            time.sleep(sleep_time)
        try:
            func()
            sleep_time = 1
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            sleep_time *= 2
            traceback.print_exc()