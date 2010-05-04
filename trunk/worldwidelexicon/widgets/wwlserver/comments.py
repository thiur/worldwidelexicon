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
import md5
import urllib
import string
import datetime
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
     
    <ul><li>md5hash : the md5hash generated from the source text, required</li>
    <li>guid : the globally unique identifier for a specific edit to the translation, optional</li>
    <li>domain : the parent website's domain or API key, optional</li>
    <li>tl : the translation language (ISO language code), required</li>
    <li>cl : the language the comment is written in (ISO language code), optional (defaults to same as tl if omitted)</li>
    <li>comment : the text of the comment itself (Unicode, UTF 8 encoding)</li>
    <li>session : session key (cookie)</li></ul>
    """
    def requesthandler(self):
        remote_addr = self.request.remote_addr
        username = self.request.get('username')
        callback = self.request.get('callback')
        pw = self.request.get('pw')
        cookies = Cookies(self,max_age=3600)
        doc = self.request.get('doc')
        fields = dict()
        domain=self.request.get('domain')
        fields['domain'] = domain
        url=self.request.get('url')
        fields['url'] = url
        tl=self.request.get('tl')
        fields['tl'] = tl
        cl=self.request.get('cl')
        if len(cl) > 1:
            fields['cl'] = cl
        else:
            fields['cl'] = tl
        guid=self.request.get('guid')
        fields['guid'] = guid
        md5hash = self.request.get('md5hash')
        fields['md5hash'] = md5hash
        comment=clean(self.request.get('comment'))
        fields['comment'] = comment
        try:
            session = cookies['session']
        except:
            session = ''
        fields['session'] = session
        if username is None:
            sessinfo = Users.auth(username, pw, '', remote_addr)
            if type(sessinfo) is dict:
                username = sessinfo['username']
                cookies['session'] = sessinfo['session']
                fields['username'] = username
            else:
                fields['username']=''
        remote_addr=self.request.remote_addr
        fields['remote_addr'] = remote_addr
        output=self.request.get('output')
        fields['spam']=False
        location = geo.get(remote_addr)
        if type(location) is dict:
            try:
                fields['city'] = location['city']
                fields['state']= location['state']
                fields['country']= location['country']
            except:
                pass
            try:
                fields['latitude']=location['latitude']
                fields['longitude']=location['longitude']
            except:
                pass
        if len(comment) > 5 and (len(guid) > 7 or len(url) > 0):
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
                    fields['spam']=True
                else:
                    fields['spam']=False
                fields['spamchecked']=True
            else:
                fields['spam']=False
                fields['spamchecked']=False
            result = Comment.save(guid,fields, url=url)
            self.response.headers['Content-Type']='text/plain'
            if len(callback) > 0:
                self.redirect(callback)
            else:
                if result:
                    self.response.out.write('ok')
                else:
                    self.response.out.write('error : invalid user')
        else:
            t = '<table><form action=/comments/submit method=post accept-charset=utf-8>'
            t = t + '<tr><td>MD5 Hash of Original Text</td><td><input type=text name=md5hash></td></tr>'
            t = t + '<tr><td>GUID of Translation</td><td><input type=text name=guid></td></tr>'
            t = t + '<tr><td>URL of source document (for general comments)</td><td><input type=text name=url></td></tr>'
            t = t + '<tr><td>Translation Language</td><td><input type=text name=tl></td></tr>'
            t = t + '<tr><td>Comment Language</td><td><input type=text name=cl></td></tr>'
            t = t + '<tr><td>Comment</td<td><textarea name=comment cols=40 rows=4></textarea></td></tr>'
            t = t + '<tr><td colspan=2><input type=submit value=SUBMIT></td></tr></table></form>'
            www.serve(self,t,sidebar=self.__doc__, title = '/comments/submit')
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
            
application = webapp.WSGIApplication([('/comments/get', GetComments),
                                      ('/comments/submit', SubmitComment)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
