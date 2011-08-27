#!/usr/bin/env python

from google.appengine.api import urlfetch
import re

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

class HackerNewsHandler(webapp.RequestHandler):

    HTML_LINK_MATCH = re.compile('<link>(.+?)</link>')
    HTML_DESCRIPTION_MATCH = re.compile('<description>(.+?)</description>')

    def get(self):

        try:
            page = urlfetch.fetch('http://feeds.feedburner.com/newsyc50?format=xml', method=urlfetch.GET, deadline=10).content
        except urlfetch.DownloadError:
            return
        
        links = re.findall(HackerNewsHandler.HTML_LINK_MATCH, page)[1:]
        descriptions = re.findall(HackerNewsHandler.HTML_DESCRIPTION_MATCH, page)[1:]

        for i in range(len(links)):

            try:
                pretty_page = urlfetch.fetch('http://viewtext.org/article?url=%s' % links[i], method=urlfetch.GET, deadline=10).content
            except urlfetch.DownloadError:
                return

            pretty_page = pretty_page[pretty_page.find('<body>')+6:pretty_page.find('</body>')]

            page = page.replace(descriptions[i], "<![CDATA[" + pretty_page + "]]>")


        self.response.headers['Content-Type'] = 'application/rss+xml'
        self.response.out.write(page)


def main():
    application = webapp.WSGIApplication([('/?', HackerNewsHandler)], debug=False)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
