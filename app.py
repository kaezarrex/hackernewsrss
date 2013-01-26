from itertools import izip
import os
import re
from xml.sax.saxutils import unescape

from flask import Flask, Response
import requests

from viewtext import viewtext


HTML_CHAR_MATCH = re.compile(r'&#(\d+)(;|(?=\s))')
FAVICON_URL = 'http://ycombinator.com/favicon.ico'

app = Flask(__name__)


def memorize(func):

    cache = dict()

    def wrapper(*args):

        if args not in cache:
            cache[args] = func(*args)

        return cache[args]

    return wrapper


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


#class Article(db.Model):
#    url = db.StringProperty(required=True)
#    content = db.TextProperty(required=True)


HTML_LINK_MATCH = re.compile('<link>(.+?)</link>')
HTML_DESCRIPTION_MATCH = re.compile('<description>(.+?)</description>')


@app.route('/')
def index():

    return main()


@app.route('/xml')
def xml():

    return Response(main(), mimetype='text/xml')


def main():

    page = get_feed('http://feeds.feedburner.com/newsyc50?format=xml')

    if not page:
        return

    links = re.findall(HTML_LINK_MATCH, page)[1:]
    descriptions = re.findall(HTML_DESCRIPTION_MATCH, page)[1:]

    for url, description in izip(links, descriptions):
        new_description = unescape(description)
        pretty_page = get_article(url)

        if pretty_page:
            new_description += '<br /><br />' + pretty_page

        page = page.replace(description, '<![CDATA[%s]]>' % new_description)

    # the original feed was ISO-8859-1, UTF-8 is better
    return '<?xml version="1.0" encoding="UTF-8" ?>\n' + page

@memorize
def get_feed(url):

    page = requests.get(url).text

    # convert from latin-1 encoding to utf-8
    #page = unicode(page, 'ISO-8859-1')
    # chop off the useless feedburner header stylesheets
    page = page[page.find('<rss'):]

    return page

@memorize
def get_article(url):

    response = viewtext(url)
    if response is None or response['content'] is None:
        return ''
    pretty_page = extract_p(response['content'])
    return pretty_page

    #query = db.Query(Article)
    #query = query.filter('url = ', url)
    #article = query.get()

    #if article is None:

    #    try:
    #        response = viewtext(url)
    #    except urlfetch.DownloadError:
    #        return None

    #    if not response:
    #        return None

    #    pretty_page = response['content']

    #    if pretty_page:
    #        pretty_page = extract_p(pretty_page)

    #    if not pretty_page:
    #        return None

    #    article = Article(url=url, content=pretty_page)
    #    article.put()

    #return article.content


#class HackerNewsRSSHandler(HackerNewsHandler):
#    def get(self):
#        self.response.headers['Content-Type'] = 'application/rss+xml'
#        HackerNewsHandler.get(self)
#
#
#class HackerNewsXMLHandler(HackerNewsHandler):
#    def get(self):
#        self.response.headers['Content-Type'] = 'application/xml'
#        HackerNewsHandler.get(self)
#
#
#class FaviconHandler(webapp.RequestHandler):
#    def get(self):
#        self.redirect(FAVICON_URL, permanent=True)


@app.route('/hello')
def hello():
    return 'Hello World!'


if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.debug = True
    app.run(host='0.0.0.0', port=port)
