import baleen
import contextlib
import requests
from lxml import html
from urllib import parse

b = baleen.Baleen()

def strip_tracking_tags(in_url):
    def isntTrackTag(s):
        if s[0] in ['camp', 'SREF', 'dlvrit', 's_campaign', 'rssfeed', 'rss_id','smid','partner','_r','ocid','fsrc']:
            return False
        if s[0].startswith('utm_'):
            return False
        return True
    exploded = list(parse.urlparse(in_url))
    exploded[4] = parse.urlencode([x for x in parse.parse_qsl(exploded[4]) if isntTrackTag(x)])
    exploded[5] = '' # Zap fragments. Nobody uses hashbang urls anymore, right?
    return parse.urlunparse(exploded)

def canonicalFromHtml(url,raw_html):
    tree = html.fromstring(raw_html)
    canonical = tree.find(".//link[@rel='canonical']")
    if canonical is not None:
        return parse.urljoin(url,canonical.get('href'))
    ogurl = tree.find(".//meta[@property='og:url']")
    if ogurl is not None:
        return parse.urljoin(url,ogurl.get('content'))
    return url

ua_string = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/601.5.17 (KHTML, like Gecko) Version/9.1 Safari/601.5.17'

def expand(short_url):
    if b.redis.exists("url:%s"%short_url):
        return
    try:
        with contextlib.closing(requests.get(short_url, stream=True, timeout=30, headers={'User-agent': ua_string})) as res:
            url = res.url
            try:
                if res.headers.get('content-type','').startswith("text/html"):
                    url = canonicalFromHtml(url,res.content)
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception as err:
                print("expanding %s, %s (html parsing)"%(short_url,err))
            b.redis.set("url:%s"%short_url,strip_tracking_tags(url),b.oneyear)
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as err:
        print("expanding %s, %s (fetching)"%(short_url,err))


def mainloop():
    expand(b.redis.blpop("expand_queue")[1].decode('utf-8'))

baleen.loopForever(mainloop)