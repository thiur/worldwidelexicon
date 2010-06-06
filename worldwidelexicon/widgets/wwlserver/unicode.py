"""
Unicode Test Module
Brian McConnell

Accepts input in any encoding and returns UTF-8 encoded text.

"""

# import standard Python libraries
import codecs
import urllib
import string
import md5
import datetime
import pydoc
# import Google App Engine modules
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.api.labs import taskqueue

import chardet
from transcoder import transcoder

def clean(text):
    return transcoder.clean(text)

class UnicodeTest(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        t = clean(self.request.get('t'))
        if len(t) > 0:
            result = chardet.detect(t)
            self.response.out.write(str(result))
        else:
            self.response.out.write('<form action=/unicode method=get>')
            self.response.out.write('<input type=text name=t>')
            self.response.out.write('<input type=submit value=OK>')
            self.response.out.write('</form>')

application = webapp.WSGIApplication([('/unicode', UnicodeTest)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
