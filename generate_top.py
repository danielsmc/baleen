#!/usr/bin/python

import datetime
import json
import MySQLdb
import MySQLdb.cursors

def generate_top(window_minutes = 2*60,headlines_count = 10):
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

    cur.execute("""select url, url_hash, sum(impact) as total_impact from
        (select url_hash, user_id from retweets join tweet_urls using(tweet_id) where created_at > DATE_SUB(NOW(),INTERVAL %s MINUTE) GROUP BY url_hash,user_id) as a
        join users using(user_id) join urls using(url_hash) group by url_hash order by total_impact desc LIMIT %s""",(window_minutes,headlines_count))

    out = []
    for url_row in cur.fetchall():
        cur.execute("""select tweet_id, expanded_text, screen_name, profile_image_url from
            (SELECT tweet_id, sum(impact) as total_impact FROM tweet_urls JOIN retweets USING(tweet_id) JOIN users USING(user_id)
                WHERE created_at > DATE_SUB(NOW(),INTERVAL %s MINUTE) and url_hash = %s
                group by tweet_id order by total_impact desc) as a
            join tweets using(tweet_id) join users using(user_id)""",(window_minutes,url_row['url_hash']))
        all_tweets = cur.fetchall()
        out.append({'url':url_row['url'],'top_tweet':all_tweets[0],'more_tweets':all_tweets[1:]})
    return {'top':out,'meta':{'last_updated':datetime.datetime.utcnow().isoformat()[:19]+"Z"}}

if __name__ == "__main__":
    print json.dumps(generate_top())