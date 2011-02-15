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

class EmailSendHandler(webapp.RequestHandler):
    def get(self):
        user_address = 'bsmcconnell@gmail.com'

        if not mail.is_email_valid(user_address):
            pass
        else:
            sender_address = 'brian@dermundo.com'
            subject = "Confirm your registration"
            body = """
Thank you for creating an account!  Please confirm your email address by
clicking on the link below:

http://www.dermundo.com/email/send
"""
            mail.send_mail(sender_address, user_address, subject, body)
            
def main():
    util.run_wsgi_app(webapp.WSGIApplication([("/wwl/email", EmailSendHandler)], debug=True))

if __name__ == "__main__":
    main()