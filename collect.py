#!/usr/bin/python

import collections
import datetime
import dateutil.parser
import hashlib
import json
from lxml import etree
import math
import MySQLdb
import MySQLdb.cursors
import os
import requests
import sys
import time
import twitter
import urlparse
from urllib import urlencode

def strip_tracking_tags(in_url):
    def isntTrackTag(s):
        if s[0] in ['camp', 'SREF', 'dlvrit', 's_campaign', 'rssfeed', 'rss_id','smid','partner','_r']:
            return False
        if s[0].startswith('utm_'):
            return False
        return True
    exploded = list(urlparse.urlparse(in_url))
    exploded[4] = urlencode(filter(isntTrackTag,urlparse.parse_qsl(exploded[4])))
    return urlparse.urlunparse(exploded)

def get_domain(in_url):
    hn = urlparse.urlparse(in_url).hostname
    if hn.startswith("www."):
        hn = hn[4:]
    return hn

class UrlResolver:
    def __init__(self):
        self.cache = {}
    def resolve(self,short_url):
        if short_url not in self.cache:
            try:
                req = requests.get(short_url,allow_redirects=True,timeout=2)
                final_url = req.url
                if 'content-type' in req.headers:
                    if req.headers['content-type'].startswith("text/html"):
                        canonical = etree.HTML(req.text).find("head/link[@rel='canonical']")
                        final_url = urlparse.urljoin(req.url,canonical.get('href') if canonical is not None else None)
                    else:
                        print req.headers['content-type'], final_url
                self.cache[short_url] = strip_tracking_tags(final_url)
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                print short_url, sys.exc_info()[:2]
                return None
        return self.cache[short_url]

def parse_created_at(tweet):
    created_at=dateutil.parser.parse(tweet['created_at'])
    if created_at.utcoffset().total_seconds()<1.0:
        created_at = created_at.replace(tzinfo=None)  # MySQL doesn't know about timezones, so we're doing this so it doesn't show a warning
    else:
        raise ValueError('Tweet created_at is not in UTC.')
    return created_at

def insert_user(user):
    user_id = user['id']
    screen_name = user['screen_name']
    profile_image_url = user['profile_image_url']
    cur.execute("INSERT INTO users (user_id,screen_name,profile_image_url) VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE screen_name=%s, profile_image_url=%s",
        (user_id,screen_name,profile_image_url,screen_name,profile_image_url))

def insert_retweet(tweet):
    if 'retweeted_status' in tweet:
        tweet_id = tweet['retweeted_status']['id']
    else:
        tweet_id = tweet['id']
    cur.execute("INSERT IGNORE INTO retweets (user_id,tweet_id,created_at) VALUES (%s,%s,%s)",(tweet['user']['id'],tweet_id,parse_created_at(tweet)))

def expand_text(tweet):
    expanded_text = tweet['text']
    for url in tweet['entities']['urls']:
        link_text = '<a href="%s">%s</a>'%(url['expanded_url'],url['display_url'])
        expanded_text=expanded_text.replace(url['url'],link_text)
    return expanded_text

def insert_tweet(tweet):
    tweet_id = tweet['id']
    text = tweet['text']
    expanded_text = expand_text(tweet)
    created_at = parse_created_at(tweet)
    user_id = tweet['user']['id']
    cur.execute("INSERT IGNORE INTO tweets (tweet_id,text,created_at,user_id,expanded_text) VALUES (%s,%s,%s,%s,%s)", (tweet_id,text,created_at,user_id,expanded_text))

def insert_links(tweet):
    for url in tweet['entities']['urls']:
        resolved_url = resolver.resolve(url['url'])
        if resolved_url is not None:
            url_hash = hashlib.sha1(resolved_url.encode('utf-8')).hexdigest()
            cur.execute("INSERT IGNORE INTO urls (url,url_hash) VALUES (%s,%s)", (resolved_url,url_hash))
            cur.execute("INSERT IGNORE INTO tweet_urls (tweet_id,url_hash) VALUES (%s,%s)", (tweet['id'],url_hash))


with open("config.json") as fh:
    config = json.load(fh)

conn = MySQLdb.connect(
    host=config['mysql']['host'],
    user=config['mysql']['user'],
    passwd=config['mysql']['passwd'],
    db=config['mysql']['database'],
    use_unicode=True,
    charset="utf8mb4",
    cursorclass = MySQLdb.cursors.DictCursor)
conn.autocommit(True)
cur = conn.cursor()
cur.execute("SET time_zone='+0:00'")


auth=twitter.OAuth(config['twitter']['access_token'],
                   config['twitter']['access_token_secret'],
                   config['twitter']['consumer_key'],
                   config['twitter']['consumer_secret'])

t = twitter.Twitter(auth=auth)
ts = twitter.TwitterStream(auth=auth)

cur.execute("select user_id from users where impact > 0 order by impact desc")
followed_ids = [x['user_id'] for x in cur.fetchall()]
follow_stream = ts.statuses.filter(follow=",".join(map(str,followed_ids[:5000])))

resolver = UrlResolver()

def do_tweet(tweet):
    if 'text' in tweet:
        if len(tweet['entities']['urls']) > 0 and tweet['user']['id'] in followed_ids:
            insert_user(tweet['user'])
            if 'retweeted_status' in tweet:
                do_tweet(tweet['retweeted_status'])
            else:
                insert_tweet(tweet)
                insert_links(tweet)
            insert_retweet(tweet)
    else:
        print tweet


for tweet in follow_stream:
    do_tweet(tweet)
