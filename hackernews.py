#!/usr/bin/env python

import re, logging
from itertools import izip

from xml.sax.saxutils import unescape

from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

from viewtext import viewtext

HTML_CHAR_MATCH = re.compile(r'&#(\d+)(;|(?=\s))')
FAVICON_URL = 'http://ycombinator.com/favicon.ico'

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

def extract_p(html):
    pattern = re.compile(r'(<p>.*</p>)', re.DOTALL)
    results = re.findall(pattern, html)
    return ''.join(results)

class HackerNewsHandler(webapp.RequestHandler):

    HTML_LINK_MATCH = re.compile('<link>(.+?)</link>')
    HTML_DESCRIPTION_MATCH = re.compile('<description>(.+?)</description>')
    article_cache = {}
    url_queue = []
    queue_length = 30

    def get(self):

        try:
            page = urlfetch.fetch('http://feeds.feedburner.com/newsyc50?format=xml', method=urlfetch.GET, deadline=10).content
        except urlfetch.DownloadError:
            return

        # convert from latin-1 encoding to utf-8
        page = unicode(page, 'ISO-8859-1')
        # chop off the useless feedburner header stylesheets
        page = page[page.find('<rss'):]

        links = re.findall(HackerNewsHandler.HTML_LINK_MATCH, page)[1:]
        descriptions = re.findall(HackerNewsHandler.HTML_DESCRIPTION_MATCH, page)[1:]

        for url, description in izip(links, descriptions):
            pretty_page = self.article_cache.get(url)
            if pretty_page is None:

                try:
                    response = viewtext(url)
                except urlfetch.DownloadError:
                    continue

                if not response:
                    continue

                pretty_page = response['content']

                if pretty_page:
                    pretty_page = extract_p(pretty_page)

                self.article_cache[url] = pretty_page
                self.url_queue.insert(0, url)

                if len(self.url_queue) > self.queue_length:
                    old_url = self.url_queue.pop()
                    self.article_cache.pop(old_url)
                    logging.debug('Popped %s' % old_url)

            new_description = unescape(description)

            if pretty_page is not None:
                new_description += '<br /><br />' + pretty_page

            page = page.replace(description, '<![CDATA[%s]]>' % new_description)

        # the original feed was ISO-8859-1, UTF-8 is better
        self.response.out.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
        self.response.out.write(page)

class HackerNewsRSSHandler(HackerNewsHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/rss+xml'
        HackerNewsHandler.get(self)

class HackerNewsXMLHandler(HackerNewsHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/xml'
        HackerNewsHandler.get(self)

class FaviconHandler(webapp.RequestHandler):
    def get(self):
        self.redirect(FAVICON_URL, permanent=True)

def main():
    urls = [('/?', HackerNewsRSSHandler),
            ('/xml', HackerNewsXMLHandler),
            ('/favicon.ico', FaviconHandler)
            ]

    application = webapp.WSGIApplication(urls, debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
