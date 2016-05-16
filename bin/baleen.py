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
        def fetchFriends(uid):
            res = self.redis.get("friends:%d"%uid)
            return {int(x) for x in res.decode('utf-8').split(',')} if res else {}
        seed_sn = self.config['twitter']['seed']
        seed_uid = self.twitter.users.show(screen_name=seed_sn)['id']
        seed_friends = fetchFriends(seed_uid)
        out = {fid:fetchFriends(fid) for fid in seed_friends}
        out[seed_uid]=seed_friends
        return out


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