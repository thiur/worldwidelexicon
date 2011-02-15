import codecs
import datetime
import md5
import string
# import Google App Engine modules
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import urlfetch
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.api.labs import taskqueue

class TextObjects(db.Model):
    label = db.StringProperty(default='')
    text = db.TextProperty(default='')
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    blog = db.BooleanProperty(default=False)
    language = db.StringProperty(default='en')
    @staticmethod
    def save(label, text, title='', language='en', blog=False):
        tdb = db.Query(TextObjects)
        tdb.filter('label = ', label)
        item = tdb.get()
        if item is None:
            item = TextObjects()
            item.label = label
        item.text = text
        item.language = language
        item.blog = blog
        item.put()
        return True
    @staticmethod
    def g(label):
        tdb = db.Query(TextObjects)
        tdb.filter('label = ', label)
        item = tdb.get()
        if item is not None:
            return item.text
        else:
            return ''
    @staticmethod
    def getall():
        tdb = db.Query(TextObjects)
        tdb.order('label')
        results = tdb.fetch(250)
        return results
    @staticmethod
    def getblog():
        tdb = db.Query(TextObjects)
        tdb.filter('blog = ', True)
        tdb.order('-createdon')
        results = tdb.fetch(30)
        return results