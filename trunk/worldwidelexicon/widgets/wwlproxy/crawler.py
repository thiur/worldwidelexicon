import facebook
import os.path
import wsgiref.handlers
import string
import md5
import datetime
import urllib
import codecs
import logging
from google.appengine.api import mail
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.api.labs import taskqueue

class Crawler(webapp.RequestHandler):
    def get(self):
        """
        Starts crawler worker tasks for main pages
        """
        pages = ['http://www.dermundo.com']
        langs = ['de','es','fr','pt']
        for p in pages:
            for l in langs:
                params = dict(
                    url = p,
                    language = l,
                )
                taskqueue.add(url='/wwl/crawler')
    def post(self):
        """
        Crawls pages scheduled by /wwl/crawler
        """
        url = self.request.get('url')
        language = self.request.get('language')
        #try:
        headers=dict()
        headers['Accept-Language']=language
        result = urlfetch.fetch(url=url,
                          headers=headers)
    #    except:
    #        logging.error('Crawler failed to open page')
def main():
    util.run_wsgi_app(webapp.WSGIApplication([("/wwl/crawler", Crawler)], debug=True))

if __name__ == "__main__":
    main()