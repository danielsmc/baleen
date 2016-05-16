import baleen
import collections
import json
import traceback
import twitter
import urllib

b = baleen.Baleen()

def addRetweet(t):
    uid_baseid = "%s:%s" % (t['user']['id'],t.get('retweeted_status',t)['id'])
    b.redis.zadd('retweets',t['id'],uid_baseid)

def addTweet(t):
    if b.redis.exists("tweet:%s"%t['id']):
        return
    if t['user']['id'] in follow_set:
        addRetweet(t)
    if 'retweeted_status' in t:
        addTweet(t['retweeted_status'])
        return
    if 'quoted_status_id' in t:
        if 'quoted_status' in t:
            addTweet(t['quoted_status'])
            del t['quoted_status']
        elif not b.redis.exists("tweet:%s"%t['quoted_status_id']):
            # print("fetching quoted status")
            try:
                addTweet(b.twitter.statuses.show(_id=t['quoted_status_id']))
                # print("succeeded")
            except (twitter.api.TwitterHTTPError,urllib.error.URLError):
                # print("failed")
                pass
    for u in t['entities']['urls']:
        if 'quoted_status_id' in t and u['expanded_url'].endswith(str(t['quoted_status_id'])):
            u['is_quote'] = True
        else:
            b.redis.rpush("expand_queue",u['expanded_url'])
    b.redis.set("tweet:%s"%t['id'],json.dumps(t),b.oneyear)

def markDeleted(tid):
    t = b.getTweet(tid)
    if t is not None:
        t['deleted'] = True
        b.redis.set("tweet:%s"%tid,json.dumps(t),b.oneyear)

def getFollowList():
    follow_tree = b.getFollowGraph()
    impact = collections.Counter()
    for fuids in follow_tree.values():
        impact.update(fuids)
    return [x[0] for x in impact.most_common()]

follow_list = getFollowList()
follow_set = set(follow_list)


def mainloop():
    follow_stream = b.twitterstream.statuses.filter(follow=','.join(map(str,follow_list[:5000])))
    for tweet in follow_stream:
        if 'text' in tweet:
            addTweet(tweet)
        elif 'delete' in tweet:
            markDeleted(tweet['delete']['status']['id'])
    else:
        print(tweet)

baleen.loopForever(mainloop)