import codecs
import datetime
import md5
import string
# import Google App Engine modules
import wsgiref.handlers
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.api.labs import taskqueue
from lsp import LSP
from database import Settings

class TextObjects(db.Model):
    label = db.StringProperty(default='')
    text = db.TextProperty(default='')
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    blog = db.BooleanProperty(default=False)
    language = db.StringProperty(default='en')
    results = None
    def load():
        self.results = TextObjects.getall()
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
        text = memcache.get('/ui/text/' + label)
        if text is not None:
            return text
        tdb = db.Query(TextObjects)
        tdb.filter('label = ', label)
        item = tdb.get()
        if item is not None:
            memcache.set('/ui/text/' + label, text, 3600)
            return item.text
        else:
            return ''
    @staticmethod
    def getall(mode = '', language=''):
        texts = memcache.get('/ui/texts/' + mode)
        if texts is not None:
            return texts
        else:
            tdb = db.Query(TextObjects)
            tdb.order('label')
            results = tdb.fetch(250)
            if mode == '':
                memcache.set('/ui/texts/' + mode, texts, 60)
                return results
            elif mode == 'dict':
                texts = dict()
                for r in results:
                    texts[r.label]=r.text
                memcache.set('/ui/texts/' + mode, texts, 60)
                return texts
            else:
                return
    @staticmethod
    def getblog():
        tdb = db.Query(TextObjects)
        tdb.filter('blog = ', True)
        tdb.order('-createdon')
        results = tdb.fetch(30)
        return results
    
class TextTranslations(db.Model):
    label = db.StringProperty(default='')
    text = db.TextProperty(default='')
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    blog = db.BooleanProperty(default=False)
    language = db.StringProperty(default='')
    @staticmethod
    def translate(label, language):
        text = TextTranslations.g(label, language)
        if len(text) < 1:
            text = TextObjects.g(label)
        return text
    @staticmethod
    def g(label, language):
        if len(label) > 0 and len(language) > 0:
            text = memcache.get('/ui/text/' + label + '/' + language)
            if text is not None:
                return text
            else:
                tdb = db.Query(TextTranslations)
                tdb.filter('label = ', label)
                tdb.filter('language = ', language)
                item = tdb.get()
                if item is None:
                    return ''
                memcache.set('/ui/text/' + label + '/' + language, text, 3600)
                return item.text
        else:
            return ''
    @staticmethod
    def getall(language, mode='', cache=True):
        if cache:
            results = memcache.get('/ui/texts/' + language + '/' + mode)
        else:
            results = None
        if results is None:
            tdb = db.Query(TextTranslations)
            tdb.filter('language = ', language)
            results = tdb.fetch(250)
            if mode == 'dict':
                texts = dict()
                for r in results:
                    texts[r.label]=r.text
                memcache.set('/ui/texts/' + language + '/' + mode, texts, 3600)
                return texts
            else:
                memcache.set('/ui/texts/' + language + '/' + mode, texts, 3600)
                return results
        else:
            return results
    @staticmethod
    def save(label, text, title='', language='en', blog=False):
        tdb = db.Query(TextTranslations)
        tdb.filter('label = ', label)
        tdb.filter('language = ', language)
        item = tdb.get()
        if item is None:
            item = TextTranslations()
            item.label = label
            item.language = language
        item.text = text
        item.language = language
        item.blog = blog
        item.put()
        return True
    @staticmethod
    def update(language):
        results = TextObjects.getall()
        for r in results:
            translation = LSP.get(sl='en', tl=language, st=r.text, lsp='speaklike',\
                                  lspusername = Settings.get('speaklike_username'),\
                                  lsppw = Settings.get('speaklike_pw'), worker=True)
            if type(translation) is dict:
                tt = translation.get('tt', '')
            elif type(translation) is str:
                tt = translation
            else:
                tt = ''
            if len(tt) > 0:
                TextTranslations.save(r.label, tt, language=language, blog=r.blog)
        return True
    
class LocalizeHandler(webapp.RequestHandler):
    def get(self):
        """
        /wwl/localize cron job
        """
        langs = ['ar','fa','de','es','fr','it','ja', 'pt','ru', 'zh']
        for l in langs:
            p = dict()
            p['language']=l
            taskqueue.add(url = '/wwl/localize', params=p, queue_name = 'translations')
    def post(self):
        """
        /wwl/localize worker task
        """
        language = self.request.get('language')
        TextTranslations.update(language)
        self.response.out.write('ok')
        

def main():
    util.run_wsgi_app(webapp.WSGIApplication([("/wwl/localize", LocalizeHandler)], debug=True))

if __name__ == "__main__":
    main()