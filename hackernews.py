#!/usr/bin/env python

from urllib2 import urlopen, URLError
import re

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

class HackerNewsHandler(webapp.RequestHandler):

    HTML_LINK_MATCH = re.compile('<link>(.+?)</link>')
    HTML_DESCRIPTION_MATCH = re.compile('<description>(.+?)</description>')

    def get(self):
    
        try:
            page = urlopen('http://feeds.feedburner.com/newsyc50?format=xml').read()
        except URLError, e:
            return
        
        links = re.findall(HackerNewsHandler.HTML_LINK_MATCH, page)[1:]
        descriptions = re.findall(HackerNewsHandler.HTML_DESCRIPTION_MATCH, page)[1:]

        for i in range(len(links)):

            try:
                pretty_page = urlopen('http://viewtext.org/article?url=' + links[i]).read()
            except URLError, e:
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
