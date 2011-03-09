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

email_body = """
Welcome to Der Mundo,\n
\n
Thank you for joining the Der Mundo beta test. We have made some updates to the system and are 
ready to do another round of testing.\n
\n
Der Mundo is easy to use. To translate a page, simply link to www.dermundo.com/www.example.com/example\n
You can also go to www.dermundo.com and enter a URL, or follow links that other users have posted.\n
\n
In this release, we have added several new features, including:\n\n
* If no human translation is available for a text, it inserts a machine translation into the translation
editor, which you can edit or replace entirely.\n
* You can now create groups on Der Mundo, for example, to organize people to translate a particular
website or topic of interest.\n
* Facebook login is now only required to edit translations, but not to view translated pages.\n
* We will also be releasing a major update to our social translator for Firefox, which enables users to
crowd translate any page with the Firefox browser. This will be available in a few days.\n\n

The service now works with most websites, but if you have a problem with a specific website or domain,
please email brian@dermundo.com to report the problem. We will be updating the translation tool
continuously in the upcoming weeks, both to fix layout problems with specific websites, and to add new
features such asprofessional translation by SpeakLike.
\n\n

Please invite others to join the beta and to start sharing the translations they create.

\n\n
Thank you for your support,

\n\n
Brian McConnell, Founder\n
Worldwide Lexicon
"""

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
                        body = TextObjects.g('email_newsletter')
                        mail.send_mail(sender_address, user_address, subject, body)
        self.response.out.write(str(counter) + ' emails sent.')
def main():
    util.run_wsgi_app(webapp.WSGIApplication([("/wwl/email", EmailSendHandler)], debug=True))

if __name__ == "__main__":
    main()