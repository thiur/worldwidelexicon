# -*- coding: utf-8 -*-
"""
Worldwide Lexicon Project
Comments (comments.py)
by Brian S McConnell <brian@worldwidelexicon.org>

OVERVIEW

This module implements web services and database calls to retrieve and save
comments about translations. This module defines two web API services:

/comments/get : to retrieve comments
/comments/submit : to submit a comment
/stats/comments : returns comment statistics (e.g. number of posts, etc)

It also defines the Comment data store as a Google data store. Access to the
data store is done via abstract methods, so it should be straightforward to
port the system to use a different data store, or to read/write comments from
an external system such as an existing web bulletin board.

NEW FEATURES AND UPDATES (April 30, 2010)

* All read/write operations are done via the Comment() class
* Added Akismet spam detection and filtering (spam comments are saved but
  not displayed)
* Most queries are memcached with a 5 minute time to live
* Updated module and class level documentation
* Updated to use improved UTF8 encoding converter and sanitizer

OUTSTANDING ISSUES

* Clean up SubmitComment() function for brevity and clearer documentation
* Additional comments for documentation purposes
* Integrate with system administration tools to allow admin to enable/disable
  comments system
* Add API call for users to vote up/down and flag individual comments
* Build multilingual commenting system/widget around this system (low priority for now)

Copyright (c) 1998-2010, Worldwide Lexicon Inc.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer. Web services
      derived from this software must provide a link to www.worldwidelexicon.org
      with a "translations powered by the Worldwide Lexicon" caption (or
      appropriate translation.
    * Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer in the documentation
      and/or other materials provided with the distribution.
    * Neither the name of the Worldwide Lexicon Inc/Worldwide Lexicon Project
      nor the names of its contributors may be used to endorse or promote
      products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
# import Google App Engine Modules
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import memcache
# import standard Python libraries
import datetime
import md5
import string
import traceback
import urllib
# import WWL and third party modules
from deeppickle import DeepPickle
from www import www
from webappcookie import Cookies
from geo import geo
from transcoder import transcoder
from akismet import Akismet
from database import Users
from database import Comment
from database import Settings
from database import Translation
from database import Users
from language import TestLanguage

def clean(text):
    return transcoder.clean(text)

class GetComments(webapp.RequestHandler):
    """
    
    <h3>/comments/get</h3>
    
    This request handler responds with a recordset of comments about a translation.
    It expects one of the following parameters:<p>
    
    <ul><li>md5hash : MD5 hash key for the original source text being commented on</li>
    <li>guid : the MD5 hash key or guid for the specific translation being commented on</li>
    <li>tl : to request comments about translations to a specific language, tl = {ISO language code}</li>
    <li>cl : limit comments to comments written in this language, cl = {ISO language code}</li>
    <li>city : list comments posted from a certain city</li>
    <li>country : list comments posted from a certain country</li>
    <li>output : output format (xml, json or rss, with xml by default)</li></ul>
    
    """
    def get(self):
        """Processes HTTP GET requestes"""
        self.requesthandler()
    def post(self):
        """Processes HTTP POST requests"""
        self.requesthandler()
    def requesthandler(self):
        """Combined GET and POST processor"""
        md5hash = self.request.get('md5hash')
        guid = self.request.get('guid')
        username = self.request.get('username')
        tl = self.request.get('tl')
        cl = self.request.get('cl')
        city = self.request.get('city')
        country = self.request.get('country')
        output = self.request.get('output')
        doc = self.request.get('doc')
        if len(md5hash) > 0 or len(guid) > 0 or len(username) > 0 or len(tl) > 0 or len(cl) > 0 or len(city) > 0 or len(country) > 0:
            validquery = True
        else:
            validquery = False
        if validquery:
            self.response.headers['Accept-Charset']='utf-8'
            text = Comment.get(md5hash=md5hash,guid=guid,username=username, tl=tl, cl=cl, city=city, country=country, output=output)
            if output == 'xml' or output =='rss':
                self.response.headers['Content-Type']='text/xml'
            elif output ==' json':
                self.response.headers['Content-Type']='text/plain'
            else:
                self.response.headers['Content-Type']='text/html'
            self.response.out.write(text)
        else:
            t = '<table><form action=/comments/get method=get accept-charset=utf-8>'
            t = t + '<tr><td>MD5Hash of Source Text</td><td><input type=text name=md5hash></td></tr>'
            t = t + '<tr><td>GUID of Translation to Request Comments For</td><td><input type=text name=guid></td></tr>'
            t = t + '<tr><td>Comments By Username</td><td><input type=text name=username></td></tr>'
            t = t + '<tr><td>Translation Language</td><td><input type=text name=tl></td></tr>'
            t = t + '<tr><td>Language Comments Are In</td><td><input type=text name=cl></td></tr>'
            t = t + '<tr><td>City</td><td><input type=text name=city></td></tr>'
            t = t + '<tr><td>Country</td><td><input type=text name=country></td></tr>'
            t = t + '<tr><td>Output Format</td><td><input type=text name=output value=xml></td></tr>'
            t = t + '<tr><td colspan=2><input type=submit value=SEARCH></td></tr>'
            t = t + '</table></form>'
            www.serve(self, t, sidebar = self.__doc__, title = '/comments/get')

class SubmitComment(webapp.RequestHandler):
    """
    <h3>/comments/submit</h3>
    
    This API handler processes comments about translations in the WWL
    translation memory. It allows users to submit comments
    about a specific edit to a specific translation, to a translated text
    in general, and to the parent URL the translations.
    Designers should be careful to design comments widgets so that it
    is clear that the comments are intended for discussion
    about the translations, and not the source material. This is
    a place where users can become confused, and of course,
    WWL does not know anything about the content of the comments
    being submitted.<p>
    
    The API handler expects the following parameters<p>
     
    <ul>
    <li>guid : the globally unique identifier for a specific edit to the translation, optional</li>
    <li>cl : the language the comment is written in (ISO language code), optional (defaults to same as tl if omitted)</li>
    <li>comment : the text of the comment itself (Unicode, UTF 8 encoding)</li>
    <li>username : WWL username (optional)</li>
    <li>pw : WWL password (optional)</li>
    <li>session : session key (cookie or form field)</li></ul>
    <li>ip : user's IP address (if in proxy mode)</li></ul>
    """
    def requesthandler(self):
        guid = self.request.get('guid')
        cl = self.request.get('cl')
        comment = clean(self.request.get('comment'))
        if len(cl) < 1 and len(comment) > 4:
            cl = TestLanguage.language(text=comment)
        remote_addr = self.request.remote_addr
        ip = self.request.get('ip')
        if len(ip) > 0:
            remote_addr = ip
        username = self.request.get('username')
        pw = self.request.get('pw')
        session=''
        location = geo.get(remote_addr)
        if type(location) is dict:
            try:
                city = location['city']
                state= location['state']
                country= location['country']
            except:
                city = ''
                state = ''
                country = ''
            try:
                latitude=location['latitude']
                longitude=location['longitude']
            except:
                latitude = None
                longitude = None
        if len(comment) > 5 and len(guid) > 7:
            emptyform=False
        else:
            emptyform=True
        if not emptyform:
            spamchecked = False
            akismetkey = Settings.get('akismet')
            root_url = Settings.get('root_url')
            if len(root_url) > 0 and string.count(root_url, 'http://') < 1:
                root_url = 'http://' + root_url
            a = Akismet()
            a.setAPIKey(akismetkey, blog_url = root_url)
            if a.verify_key():
                data = dict()
                data['user_ip']=remote_addr
                data['user_agent']=self.request.headers['User-Agent']
                if a.comment_check(comment, data):
                    spam=True
                else:
                    spam=False
                spamchecked=True
            else:
                spam=False
                spamchecked=False
            result = False
            if len(username) > 0:
                session = Users.auth(username=username, pw=pw, session='')
                if len(session) < 8:
                    username=''
            if not spam:
                tdb = db.Query(Translation)
                tdb.filter('guid = ', guid)
                item = tdb.get()
                if item is not None:
                    md5hash = item.md5hash
                    sl = item.sl
                    tl = item.tl
                    st = item.st
                    tt = item.tt
                    domain = item.domain
                    url = item.url
                    professional = item.professional
                    author = item.username
                    cdb = db.Query(Comment)
                    cdb.filter('guid = ', guid)
                    cdb.filter('remote_addr = ', remote_addr)
                    item = cdb.get()
                    if item is None:
                        item = Comment()
                        item.guid = guid
                        item.md5hash = md5hash
                        item.tl = tl
                        item.cl = cl
                        item.comment = comment
                        item.username = username
                        item.spamchecked = spamchecked
                        item.spam = spam
                        item.remote_addr = remote_addr
                        timestamp = datetime.datetime.now()
                        item.minute = timestamp.minute
                        item.hour = timestamp.hour
                        item.day = timestamp.day
                        item.month = timestamp.month
                        item.year = timestamp.year
                        item.domain = domain
                        item.url = url
                        item.city = city
                        item.state = state
                        item.country = country
                        try:
                            item.latitude = latitude
                            item.longitude = longitude
                        except:
                            pass
                        item.put()
                        if professional and len(author) > 0:
                            LSP.comment(guid, comment, lsp=author, username=username, remote_addr=remote_addr)
                        result = True
            self.response.headers['Content-Type']='text/plain'
            if result:
                self.response.out.write('ok')
            else:
                self.error(500)
                self.response.out.write('error')
        else:
            tdb = db.Query(Translation)
            tdb.order('-date')
            item = tdb.get()
            if item is not None:
                guid = item.guid
            else:
                guid = ''
            t = '<table><form action=/comments/submit method=post accept-charset=utf-8>'
            t = t + '<tr><td>GUID of Translation (guid)</td><td><input type=text name=guid value="' + guid + '"></td></tr>'
            t = t + '<tr><td>Comment (comment)</td<td><input type=text name=comment></td></tr>'
            t = t + '<tr><td>Username (username, optional)</td><td><input type=text name=username></td></tr>'
            t = t + '<tr><td>Password (pw, optional)</td><td><input type=text name=pw></td></tr>'
            t = t + '<tr><td colspan=2><input type=submit value=SUBMIT></td></tr></table></form>'
            www.serve(self,t,sidebar=self.__doc__, title = '/comments/submit')
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()

class PurgeSpamComments(webapp.RequestHandler):
    """
    <h3>/comments/spam</h3>

    This task is called as a cron job to purge comments marked as spam by Akismet or
    other methods.
    """
    def get(self):
        cdb = db.Query(Comment)
        cdb.filter('spam = ', True)
        results = cdb.fetch(limit=100)
        if len(results) > 0:
            db.delete(results)
        self.response.out.write('ok')

debug_setting = Settings.get('debug')
if debug_setting == 'True':
    debug_setting = True
elif debug_setting == 'False':
    debug_setting = False
else:
    debug_setting = True
            
application = webapp.WSGIApplication([('/comments/get', GetComments),
                                      ('/comments/spam', PurgeSpamComments),
                                      ('/comments/submit', SubmitComment)],
                                     debug=debug_setting)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
