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

def slimTweet(t):
    out = {
        'id': t['id'],
        'screen_name': t['user']['screen_name'],
        'avatar': t['user']['profile_image_url_https']
    }
    if len(t['entities'].get('media',[])) > 0:
        out['media_url'] = t['entities']['media'][0]['media_url_https']
    text = t['text']
    if 'quoted_status_id' in t:
        out['quoted_status_id'] = t['quoted_status_id']
    out['urls'] = []
    for u in t['entities']['urls']:
        if u.get('is_quote'):
            text = text.replace(u['url'],"")
        else:
            out['urls'].append(u['expanded_url'])
            text = text.replace(u['url'],u['expanded_url'])
    for m in t['entities'].get('media',[]):
        text = text.replace(m['url'],"")
    out['text'] = text
    return out

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
        elif not b.redis.exists("tweet:%s"%t['quoted_status_id']):
            # print("fetching quoted status")
            try:
                addTweet(b.twitter.statuses.show(_id=t['quoted_status_id'],tweet_mode='extended'))
                # print("succeeded")
            except (twitter.api.TwitterHTTPError,urllib.error.URLError):
                # print("failed")
                pass
    if 'extended_tweet' in t:
        t.update(t['extended_tweet'])
    if 'full_text' in t:
        t['text'] = t['full_text']
    for u in t['entities']['urls']:
        if 'quoted_status_id' in t and u['expanded_url'].endswith(str(t['quoted_status_id'])):
            u['is_quote'] = True
        else:
            b.redis.rpush("expand_queue",u['expanded_url'])
    slimmed = slimTweet(t)
    b.redis.set("tweet:%s"%t['id'],json.dumps(slimmed),b.oneyear)

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
