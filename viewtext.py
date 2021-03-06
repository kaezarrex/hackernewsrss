from urllib import urlencode
import re

import requests

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

    result = requests.get(url)

    if result.status_code != 200:
        return None

    page = result.text
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
