#!/usr/bin/env python

import re
import urllib2

from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

from viewtext import viewtext

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

        for i, url in enumerate(links):
            pretty_page = self.article_cache.get(url)
            if pretty_page is None:
                
                try:
                    response = viewtext(url)
                except urllib2.HTTPError:
                    continue
                    
                pretty_page = response['content']
                
                self.article_cache[url] = pretty_page
            
            if pretty_page is not None:
                page = page.replace(descriptions[i], "<![CDATA[" + pretty_page + "]]>")


        self.response.headers['Content-Type'] = 'application/rss+xml'
        self.response.out.write(page)


def main():
    application = webapp.WSGIApplication([('/?', HackerNewsHandler)], debug=False)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
