import baleen
import collections
import datetime
import os
import pystache
import stat
import sys
import tempfile
import urllib

WINDOW_SIZE = 5000
TARGET_COUNT = 20

b = baleen.Baleen()

def snowflake2datetime(sf):
    return datetime.datetime.utcfromtimestamp(((int(sf) >> 22) + 1288834974657) / 1000.0)

def scoreLocus(uids,follower_index):
    return (len(set().union(*[follower_index[uid] for uid in uids])),
            sum([len(follower_index[uid]) for uid in uids]))

def addTweetLoci(tid,uid,loci,child_tweets):
    loci[('tweet',tid)].add(uid)
    t = b.getTweet(tid)
    if t is None:
        return
    if 'quoted_status_id' in t:
        child_tweets[('tweet',t['quoted_status_id'])].add(('tweet',tid))
        addTweetLoci(t['quoted_status_id'],uid,loci,child_tweets)
    for u in t['urls']:
        url = b.getUrl(u) or u
        child_tweets[('url',url)].add(('tweet',tid))
        loci[('url',url)].add(uid)

def getOrderedChildren(targ,child_tweets,loci_scores):
    return sorted(child_tweets[targ],key=lambda x:loci_scores[x],reverse=True)

def buildChildTree(targ,tweets_in_use,child_tweets,loci_scores):
    if targ in tweets_in_use:
        return
    tweets_in_use.add(targ)
    return {'tweet':tweetForDisplay(targ[1]),'children':[x for x in [buildChildTree(y,tweets_in_use,child_tweets,loci_scores) for y in getOrderedChildren(targ,child_tweets,loci_scores)] if x is not None]}

def get_domain(in_url):
    hn = urllib.parse.urlparse(in_url).hostname
    if hn.startswith("www."):
        hn = hn[4:]
    return hn

def tweetForDisplay(tid):
    t = b.getTweet(tid)
    if t is None:
        return
    t['created_at'] = snowflake2datetime(t['id']).isoformat()[:19]+"Z"
    text = t['text']
    for u in t['urls']:
        real_url = b.getUrl(u) or u
        link_text = '<a href="%s">%s</a>'%(real_url,get_domain(real_url))
        text = text.replace(u,link_text)
    text = text.replace('\n','<br>')
    t['expanded_text'] = text
    return t

def generateTop(windowsize,targetcount):
    follower_index = collections.defaultdict(set)
    for friend,followers in b.getFollowGraph().items():
        for follower in followers:
            follower_index[follower].add(friend)

    retweets = [(tuple(map(int,x[0].split(b":"))),snowflake2datetime(x[1])) for x in b.redis.zrevrange('retweets',0,WINDOW_SIZE,withscores=True)]

    freshest_tweet = retweets[0][1]
    window_minutes = int((retweets[0][1]-retweets[-1][1]).total_seconds()/60)

    child_tweets = collections.defaultdict(set)
    loci = collections.defaultdict(set)

    for rt in retweets:
        addTweetLoci(rt[0][1],rt[0][0],loci,child_tweets)

    loci_scores = {k:(scoreLocus(v,follower_index),k[0]) for k,v in loci.items()}

    tweets_in_use = set()

    top = []
    targets = sorted(loci.keys(),key=lambda x:loci_scores[x],reverse=True)
    for targ in targets:
        if targ[0]=='url':
            targ_tree = buildChildTree(targ,tweets_in_use,child_tweets,loci_scores)['children']
            if len(targ_tree):
                top.append({'tweets':targ_tree})
        else:
            targ_tree = buildChildTree(targ,tweets_in_use,child_tweets,loci_scores)
            if targ_tree is not None:
                top.append({'tweets':[targ_tree]})

        if len(top) == TARGET_COUNT:
            break
    for t in top:
        t['tweets'][0]['lede']=True
    return (top,window_minutes,freshest_tweet)

if len(sys.argv) < 2:
    print("pass an output filepath")
else:
    top,window_minutes,freshest_tweet = generateTop(5000,20)
    b.redis.zremrangebyrank('retweets',0,-10*WINDOW_SIZE)

    out = { 'top': top,
            'meta':{ 'last_updated':freshest_tweet.isoformat()[:19]+"Z",
                     "window_minutes":window_minutes,
                     'expand_queue':b.redis.llen("expand_queue")}}

    stache = pystache.Renderer(search_dirs="templates",file_extension='mustache')

    temp_fd,temp_path = tempfile.mkstemp()
    with os.fdopen(temp_fd,'w') as fh:
        fh.write(stache.render_name('top_page',out))

    os.chmod(temp_path,stat.S_IWUSR | stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    os.rename(temp_path,sys.argv[1])





