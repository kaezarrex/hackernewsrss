from urllib2 import urlopen
from urllib import urlencode
import re, logging

from google.appengine.api import urlfetch

try:
    import simplejson as json
except:
    import json

def viewtext(url, redirect_links=False, mld=8):
    '''Runs a URL through viewtext

    :param: mld: Remove HTML nodes with a link density greater than or equal to value.
    '''
    args = dict(url=url,
                callback='c',
                rl=str(redirect_links).lower(),
                mld=mld
                )
    url = 'http://viewtext.org/api/text?%s' % urlencode(args)

    result = urlfetch.fetch(url, method=urlfetch.GET, deadline=10)
    if result.status_code != 200:
        logging.warn('[%s] %s' % (result.status_code, url))
        return None
    page = result.content
    page = page[2:-1] # chop off the callback bit

    data = json.loads(page)
    del data['callback']

    content = data['content']
    if content is not None:
        if len(content):
            content = re.sub(r'\s+', ' ', content)
        if content is not None and len(content):
            content = re.sub(r'>\s+</', '></', content)

        data['content'] = content

    return data

if __name__ == '__main__':
    page = viewtext('http://www.economist.com/node/21526782')
    print page['content']
