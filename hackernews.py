#!/usr/bin/env python

import re
import urllib, urllib2

from xml.sax.saxutils import unescape

from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

from viewtext import viewtext

HTML_CHAR_MATCH = re.compile(r'&#(\d+)(;|(?=\s))')

def unescape_html(s):
    '''A simple function to unescape html
    Converts numeric character references (&#160;) to unicode charactrs
    This will not work for entities such as &nbsp;    
    '''

    def _callback(matches):
        id = matches.group(1)
        try:
            return unichr(int(id))
        except:
            return id
    
    return HTML_CHAR_MATCH.sub(_callback, s)

class HackerNewsHandler(webapp.RequestHandler):

    HTML_LINK_MATCH = re.compile('<link>(.+?)</link>')
    HTML_DESCRIPTION_MATCH = re.compile('<description>(.+?)</description>')
    article_cache = {}

    def get(self):

        try:
            page = urlfetch.fetch('http://feeds.feedburner.com/newsyc50?format=xml', method=urlfetch.GET, deadline=10).content
        except urlfetch.DownloadError:
            return
        
        links = re.findall(HackerNewsHandler.HTML_LINK_MATCH, page)[1:]
        descriptions = re.findall(HackerNewsHandler.HTML_DESCRIPTION_MATCH, page)[1:]

        items = zip(links, descriptions)

        for url, description in items:
            pretty_page = self.article_cache.get(url)
            if pretty_page is None:
                
                try:
                    response = viewtext(url)
                except urllib2.HTTPError:
                    continue
                    
                pretty_page = response['content']
                
                self.article_cache[url] = pretty_page

            new_description = unescape(description) 
            
            if pretty_page is not None:
                pretty_page = pretty_page.encode('ascii', 'xmlcharrefreplace')
                new_description += '<br /><br />' + pretty_page
            
            page = page.replace(description, u'<![CDATA[%s]]>' % new_description)

        self.response.out.write(page)

class HackerNewsRSSHandler(HackerNewsHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/rss+xml'
        HackerNewsHandler.get(self)

class HackerNewsXMLHandler(HackerNewsHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/xml'
        HackerNewsHandler.get(self)
        
def main():
    urls = [('/?', HackerNewsRSSHandler),
            ('/xml', HackerNewsXMLHandler)
            ]
    
    application = webapp.WSGIApplication(urls, debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
