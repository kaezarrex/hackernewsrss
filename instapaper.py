from urllib import urlencode
import re, logging

from google.appengine.api import urlfetch

try:
    import simplejson as json
except:
    import json

def instapaper(url):
    '''Runs a URL through Instapaper
    '''
    args = dict(u=url)
    url = 'http://www.instapaper.com/text?%s' % urlencode(args)

    result = urlfetch.fetch(url, method=urlfetch.GET, deadline=10)
    if result.status_code != 200:
        logging.warn('[%s] %s' % (result.status_code, url))
        return None
    page = result.content
    return page

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
