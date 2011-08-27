from urllib2 import urlopen
from urllib import urlencode
import re

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

    result = urlopen(url)
    page = result.read()
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
    page = viewtext('http://www.f-secure.com/weblog/archives/00002226.html')
    print page['content']