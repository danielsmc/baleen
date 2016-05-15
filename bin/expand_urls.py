import baleen
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

def expand(short_url):
    # print("starting with",short_url)
    if b.redis.exists("url:%s"%short_url):
        return
    try:
        url = short_url
        req = requests.head(url,allow_redirects=True,timeout=30)
        url = req.url
        try:
            if req.headers.get('content-type','').startswith("text/html"):
                tree = html.fromstring(requests.get(url,timeout=30).content)
                canonical = tree.find(".//link[@rel='canonical']")
                if canonical is not None:
                    url = parse.urljoin(url,canonical.get('href'))
                else:
                    ogurl = tree.find(".//meta[@property='og:url']")
                    if ogurl is not None:
                        url = parse.urljoin(url,ogurl.get('content'))
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as err:
            print("expanding %s, %s (phase 2)"%(short_url,err))
        b.redis.set("url:%s"%short_url,strip_tracking_tags(url),b.oneyear)
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as err:
        print("expanding %s, %s (phase 1)"%(short_url,err))


def mainloop():
    expand(b.redis.blpop("expand_queue")[1].decode('utf-8'))

baleen.loopForever(mainloop)