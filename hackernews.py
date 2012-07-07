#!/usr/bin/env python

import re, logging
from itertools import izip

from xml.sax.saxutils import unescape
from lxml import html as lxml_html

from google.appengine.api import urlfetch
from google.appengine.ext import db
from google.appengine.ext.webapp import util
import webapp2

from instapaper import instapaper

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

def extract_story(html):
    root = lxml_html.document_fromstring(html)
    story = root.get_element_by_id('story')
    return lxml_html.tostring(story)

class Article(db.Model):
    url = db.StringProperty(required=True)
    content = db.TextProperty(required=True)


class HackerNewsHandler(webapp2.RequestHandler):

    HTML_LINK_MATCH = re.compile('<link>(.+?)</link>')
    HTML_DESCRIPTION_MATCH = re.compile('<description>(.+?)</description>')
    url_queue = []
    queue_length = 30

    def get(self):

        page = self._get_feed('http://feeds.feedburner.com/newsyc50?format=xml')

        if not page:
            return

        links = re.findall(HackerNewsHandler.HTML_LINK_MATCH, page)[1:]
        descriptions = re.findall(HackerNewsHandler.HTML_DESCRIPTION_MATCH, page)[1:]

        for url, description in izip(links, descriptions):
            new_description = unescape(description)
            pretty_page = self._get_article(url)

            if pretty_page:
                new_description += '<br /><br />' + pretty_page

            page = page.replace(description, '<![CDATA[%s]]>' % new_description)

        # the original feed was ISO-8859-1, UTF-8 is better
        self.response.out.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
        self.response.out.write(page)

    @staticmethod
    def _get_feed(url):
        try:
            page = urlfetch.fetch(url, method=urlfetch.GET, deadline=10).content
        except urlfetch.DownloadError:
            return None

        # convert from latin-1 encoding to utf-8
        page = unicode(page, 'ISO-8859-1')
        # chop off the useless feedburner header stylesheets
        page = page[page.find('<rss'):]

        return page

    @staticmethod
    def _get_article(url):

        query = db.Query(Article)
        query = query.filter('url = ', url)
        article = query.get()

        if article is None:

            try:
                response = instapaper(url)
            except urlfetch.DownloadError:
                return None

            if not response:
                return None

            pretty_page = extract_story(response)

            if not pretty_page:
                return None

            article = Article(url=url, content=pretty_page)
            article.put()

        return article.content


class HackerNewsRSSHandler(HackerNewsHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/rss+xml'
        HackerNewsHandler.get(self)


class HackerNewsXMLHandler(HackerNewsHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/xml'
        HackerNewsHandler.get(self)


class FaviconHandler(webapp2.RequestHandler):
    def get(self):
        self.redirect(FAVICON_URL, permanent=True)



urls = [('/?', HackerNewsRSSHandler),
        ('/xml', HackerNewsXMLHandler),
        ('/favicon.ico', FaviconHandler)
        ]

app = webapp2.WSGIApplication(urls)
