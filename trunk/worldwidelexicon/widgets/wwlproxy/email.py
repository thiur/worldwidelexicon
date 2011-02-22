import facebook
import os.path
import wsgiref.handlers
import string
import md5
import datetime
import urllib
import codecs
from google.appengine.api import mail
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.api.labs import taskqueue
from ui import TextObjects
from ui import TextTranslations
from home import User

class EmailSendHandler(webapp.RequestHandler):
    def get(self):
        udb = db.Query(User)
        users = udb.fetch(100)
        counter = 0
        for u in users:
            if u.email is not None:
                if len(u.email) > 0:
                    counter = counter + 1
                    user_address = u.email
                    try:
                        langloc = string.split(u.locale,'_')
                        language = langloc[0]
                    except:
                        language = 'en'
                    if not mail.is_email_valid(user_address):
                        pass
                    else:
                        sender_address = 'brian@dermundo.com'
                        subject = "Der Mundo Beta"
                        if string.count(u.locale, 'en') > 0:
                            body = TextObjects.g('email_newsletter')
                        else:
                            body = TextTranslations.g('email_newsletter', language)
                            if len(body) < 1: body = TextObjects.g('email_newsletter')
                        mail.send_mail(sender_address, user_address, subject, body)
        self.response.out.write(counter + ' emails sent.')
def main():
    util.run_wsgi_app(webapp.WSGIApplication([("/wwl/email", EmailSendHandler)], debug=True))

if __name__ == "__main__":
    main()