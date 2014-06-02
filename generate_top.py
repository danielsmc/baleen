#!/usr/bin/python

import datetime
import json
import MySQLdb
import MySQLdb.cursors

def generate_top(window_tweets = 3000,headlines_count = 20):
    with open("config.json") as fh:
        config = json.load(fh)

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

    cur.execute("""select url, url_hash, sum(impact) as total_impact, timestampdiff(minute,min(max_created_at),now()) as window from
        (select url_hash, user_id, max(created_at) as max_created_at from retweets join tweet_urls using(tweet_id) GROUP BY url_hash,user_id order by max_created_at desc limit %s) as a
        join users using(user_id) join urls using(url_hash) group by url_hash order by total_impact desc LIMIT %s""",(window_tweets,headlines_count))

    window_minutes = 0
    out = []
    for url_row in cur.fetchall():
        window_minutes = max(window_minutes,int(url_row['window']))
        cur.execute("""select tweet_id, expanded_text, screen_name, profile_image_url, media_url, total_impact, created_at from
            (SELECT tweet_id, sum(impact) as total_impact FROM tweet_urls JOIN retweets USING(tweet_id) JOIN users USING(user_id)
                WHERE url_hash = %s
                group by tweet_id order by total_impact desc) as a
            join tweets using(tweet_id) join users using(user_id)""",(url_row['url_hash'],))
        all_tweets = cur.fetchall()
        for t in all_tweets:
            t['total_impact'] = int(t['total_impact'])
            t['created_at'] = t['created_at'].isoformat()+"Z"
        out.append({'url':url_row['url'],'top_tweet':all_tweets[0],'more_tweets':all_tweets[1:]})
    return {'top':out,'meta':{'last_updated':datetime.datetime.utcnow().isoformat()[:19]+"Z","window_minutes":window_minutes}}

if __name__ == "__main__":
    print json.dumps(generate_top())