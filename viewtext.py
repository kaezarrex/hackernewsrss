from urllib2 import urlopen
from urllib import urlencode

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

	result = urlopen(url, timeout=10)
	page = result.read()
	page = page[2:-1] # chop off the callback bit
	
	data = json.loads(page)
	del data['callback']
	return data

def viewtext_clean(url):
	return viewtext(url)


if __name__ == '__main__':
	page = viewtext_clean('http://www.f-secure.com/weblog/archives/00002226.html')
	print page