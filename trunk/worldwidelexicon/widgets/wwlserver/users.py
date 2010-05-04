# -*- coding: utf-8 -*-
"""

Worldwide Lexicon
User Management Module (users.py)
Brian S McConnell <brian@worldwidelexicon.org>

This module encapsulates classes that are used to access user information,
such as login credentials and extended user profile information and meta data.
The module assumes that WWL maintains a list of users, their profiles and access
rights. This module can be extended or modified to proxy user related queries
through to other systems (e.g. an existing user authentication and account
management system). 

NOTE: this documentation is generated automatically via PyDoc (Python's built
in documentation engine). Because of the way Google App Engine works, the
hyperlinks within these documents, do not work properly. We recommend printing
the module documentation for offline review.

Copyright (c) 1998-2009, Worldwide Lexicon Inc.
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
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import urlfetch
from google.appengine.api import memcache
import demjson
import urllib
import string
import md5
import datetime
import pydoc
from webappcookie import Cookies
from www import www
from geo import geo
from transcoder import transcoder
from database import Users

#
# Define Callback URLs for User Validation Success or Failure
#
validate_success_url = '/'
validate_failure_url = '/'

def clean(text):
    return transcoder.clean(text)

#
# Define Simple User Access Rights
#

# Type of user service in use: can be simple, wwl, google or proxy
user_service = 'wwl'

class wwwAuth(webapp.RequestHandler):
    """
    
    <h3>/users/auth</h3>
    
    This request handler implements the /users/auth
    request handler. It expects the following parameters:<p>
    
    <ul><li>session (cookie) : md5hash key for current session</li>
    <li>username : WWL or external username</li>
    <li>pw : WWL or external password</li></ul>
    
    It responds in plain text (text/plain) with either
    a session key (valid login or session key) or
    an empty string if credentials are invalid or expired<p>
    
    This request handler can also be run in proxy server mode, where
    it calls an external URL to authenticate the user. In this case,
    you should supply the following additional parameters.

    <ul><li>proxyurl : URL for the external authentication service</li>
    <li>username_field : field for username</li>
    <li>pw_field : field for password or key</li>
    <li>success_msg : string to look for in successful login response</li>
    <li>error_msg : string to look for in failed login</li>
    </ul><p>

    <blockquote>When using /users/auth in proxy mode, WWL will not store
    user credentials. If the user is authenticated, WWL will assign a random
    session key that expires after about one hour.</blockquote>
    """
    def get(self):
        """ Processes HTTP GET calls."""
        self.requesthandler()
    def post(self):
        """ Processes HTTP POST calls."""
        self.requesthandler()
    def requesthandler(self):
        """ Combined GET and POST request handler."""
        doc = self.request.get('doc')
        if user_service == 'google':
            if doc =='y':
                www.serve(self,self.__doc__, title = '/users/auth')
            else:
                user = users.get_current_user()
                if user is None:
                    self.redirect(users.create_login_url(self.request.uri))
                else:
                    self.redirect('/')
        else:
            cookies = Cookies(self,max_age=3600)
            try:
                session = cookies['session']
            except:
                session = self.request.get('session')
            username = clean(self.request.get('username'))
            pw = self.request.get('pw')
            callback = self.request.get('callback')
            remote_addr = self.request.remote_addr
            proxyurl = self.request.get('proxyurl')
            username_field = self.request.get('username_field')
            pw_field = self.request.get('pw_field')
            success_msg = self.request.get('success_msg')
            error_msg = self.request.get('error_msg')
            location = geo.get(remote_addr)
            city = location.get('city','')
            state = location.get('state', '')
            country = location.get('country', '')
            try:
                latitude = location['latitude']
                longitude = location['longitude']
            except:
                latitude = None
                longitude = None
            if len(username) > 2 or len(session) > 2:
                if len(proxyurl) > 0 and len(username_field) > 0 and len(pw_field) > 0:
                    form=dict()
                    form[username_field]=username
                    form[pw_field]=pw
                    form['user_ip']=remote_addr
                    form_data = urllib.urlencode(form)
                    result = urlfetch.fetch(url=proxyurl,
                              payload=form_data,
                              method=urlfetch.POST,
                              headers={'Content-Type' : 'application/x-www-form-urlencoded','Accept-Charset' : 'utf-8'})
                    if result.status_code == 200:
                        text = clean(result.content)
                        if string.count(text,success_msg) > 0:
                            m = md5.new()
                            m.update(username)
                            m.update(str(datetime.datetime.now()))
                            session = str(m.hexdigest())
                            sessioninfo = dict()
                            sessioninfo['username'] = username
                            sessioninfo['session'] = session
                            memcache.set('sessions|' + session, sessioninfo, 1800) 
                        else:
                            session = None
                    else:
                        session=None
                else:
                    sessioninfo = Users.auth(username, pw, session, remote_addr, city=city, state=state, country=country, latitude=latitude, longitude=longitude)
                if sessioninfo is not None:
                    cookies['session'] = sessioninfo.get('session','')
                self.response.headers['Content-Type']='text/plain'
                if len(callback) > 0:
                    self.redirect(callback)
                else:
                    if type(sessioninfo) is dict:
                        self.response.out.write(sessioninfo.get('session',''))
                    else:
                        self.response.out.write('')
            else:
                t = '<form action=/users/auth method=post accept-charset=utf-8>'
                t = t + '<table><tr><td>Username</td><td><input type=text name=username></td></tr>'
                t = t + '<tr><td>Password</td><td><input type=password name=pw></td></tr>'
                t = t + '<tr><td>Proxy URL (External Auth Server)</td><td><input type=text name=proxyurl value=http://www.worldwidelexicon.org/users/proxy></td></tr>'
                t = t + '<tr><td>Username Field</td><td><input type=text name=username_field value=username></td></tr>'
                t = t + '<tr><td>Password Field</td><td><input type=text name=pw_field value=pw></td></tr>'
                t = t + '<tr><td>Success Message / String</td><td><input type=text name=success_msg value=welcome></td></tr>'
                t = t + '<tr><td>Error Message / String</td><td><input type=text name=error_msg value=invalid></td></tr>'
                t = t + '<tr><td colspan=2><input type=submit value=LOGIN></td></tr>'
                t = t + '</table></form>'
                www.serve(self,t, sidebar = self.__doc__, title = '/users/auth')

class wwwCheckUser(webapp.RequestHandler):
    """
    <h3>/users/check</h3>
    
    This web service tells you if the username is available for registration.
    
    It expects the parameter username={username}<p>
    
    It responds with in plain text as follows:<p>
    y (username available)<p>
    n (username taken)<p>
    
    """
    def get(self):
        """ Processes HTTP GET calls."""
        username = self.request.get('username')
        doc = self.request.get('doc')
        if len(username) > 5:
            self.response.headers['Content-Type']='text/plain'
            udb = db.Query(Users)
            udb.filter('username = ', username)
            item = udb.get()
            if item is None:
                self.response.out.write('y')
            else:
                self.response.out.write('n')
        else:
            t = '<table><form action=/users/check method=get accept-charset=utf-8>'
            t = t + '<tr><td>Username</td><td><input type=text name=username></td></tr>'
            t = t + '<tr><td colspan=2><input type=submit value="Check Username"></td></tr></table></form>'
            www.serve(self,t, sidebar = self.__doc__, title = '/users/check')
            
class wwwCount(webapp.RequestHandler):
    """
    <h3>/users/count</h3>
    
    This web service returns the edit and word counts for translations
    posted by a user. The request handler expects the following parameters:<p>
    
    <ul><li>username : WWL or external username</li></ul><p>

    If username is blank, the request handler will serve an HTML form for generating test queries.
    and returns the number of edits and number of words submitted as
    a comma separated list in a plain text response (e.g. 2, 10)
    
    """
    def get(self):
        """ Processes HTTP GET calls."""
        username = self.request.get('username')
        d = self.request.get('doc')
        if len(username) > 7:
            self.response.headers['Content-Type']='text/plain'
            count = Users.count(username)
            self.response.out.write(str(count['edits']) + ',' + str(count['words']))
        else:
            t = '<table><form action=/users/count method=get accept-charset=utf-8>'
            t = t + '<tr><td>Username</td><td><input type=text name=username><input type=submit value=OK></td></tr>'
            t = t + '<tr><td colspan=2><input type=submit value=OK></td></tr></table></form>'
            www.serve(self,t, sidebar = self.__doc__, title = '/users/count')

class wwwCurrentUser(webapp.RequestHandler):
    """
    <h3>/users/currentuser</h3>
    
    This web service returns the username associated with the
    current session key (session cookie). It responds to
    /users/currentuser with a plain text document with the
    current username or an empty string if there is no valid
    session associated with this key
    
    """
    def get(self):
        """ Processes HTTP GET calls"""
        doc = self.request.get('doc')
        if user_service != 'google':
            cookies = Cookies(self,max_age=3600)
            username = ''
            try:
                session = cookies['session']
            except:
                session = ''        
            if len(session) > 0:
                username = memcache.get('sessions|' + session)
                if username is None:
                    username = ''
        else:
            username = GoogleUsers.getuser('')
        if doc == 'y':
            www.serve(self,self.__doc__, title = '/users/currentuser')
        else:
            self.response.headers['Content-Type']='text/plain'
            self.response.out.write(username)

class wwwNewUser(webapp.RequestHandler):
    """
    <h3>/users/new</h3>
    
    This request handler creates a new user account and issues
    a session key. It assumes that the user creation script
    will generate and send a welcome email to the user.
    (You can implement an email delivery script in App Engine
    if desired). It expects the following parameters:<p>
    
    <ul><li>username : selected username</li>
    <li>email : email address</li>
    <li>pw : selected password</li></ul>
    
    And the following optional parameters:<p>
    
    <ul><li>firstname</li>
    <li>lastname</li>
    <li>description</li>
    <li>skype</li>
    <li>facebook</li>
    <li>linkedin</li>
    <li>www</li>
    <li>tags</li>
    <li>city</li>
    <li>state</li>
    <li>country</li></ul>
    
    The script will create the new user, issue a validation key
    which will be returned in plain text. It will return an
    empty string if user creation failed because the username
    was already selected or the password was shorted than 8 chars.<p>
    
    """
    def get(self):
        """ Processes HTTP GET calls"""
        self.requesthandler()
    def post(self):
        """ Processes HTTP POST calls"""
        self.requesthandler()
    def requesthandler(self):
        """ Combined GET and POST request handler"""
        username = clean(self.request.get('username'))
        email = clean(self.request.get('email'))
        remote_addr = self.request.remote_addr
        pw = clean(self.request.get('pw'))
        doc = self.request.get('doc')
        firstname = clean(self.request.get('firstname'))
        lastname = clean(self.request.get('lastname'))
        description = clean(self.request.get('description'))
        skype = self.request.get('skype')
        facebook = self.request.get('facebook')
        linkedin = self.request.get('linkedin')
        tags = clean(self.request.get('tags'))
        city = self.request.get('city')
        state = self.request.get('state')
        country = self.request.get('country')
        if len(city) < 1:
            location = geo.get(remote_addr)
        else:
            location['city']=city
            location['state']=state
            location['country']=country
        if type(location) is dict:
            city = location.get('city', '')
            state = location.get('state','')
            country = location.get('country', '')
            try:
                latitude = location['latitude']
                longitude = location['longitude']
            except:
                latitude = None
                longitide = None
        else:
            city = ''
            state = ''
            country = ''
            latitude = None
            longitude = None
        callback = self.request.get('callback')
        if len(username) > 5 and len(pw) > 5 and user_service != 'google':
            self.response.headers['Content-Type']='text/plain'
            result = Users.new(username, email, pw, remote_addr, firstname=firstname, lastname=lastname, description=description, skype=skype, facebook=facebook, linkedin=linkedin, city=city, state=state, country=country, latitude=latitude, longitude=longitude)
            if len(callback) > 0:
                self.redirect(callback)
            elif result:
                self.response.out.write('ok')
            else:
                self.response.out.write('error')
        else:
            t = '<form action=/users/new method=post accept-charset=utf-8><table>'
            t = t + '<tr><td>Username</td><td><input type=text name=username></td></tr>'
            t = t + '<tr><td>Email</td><td><input type=text name=email></td></tr>'
            t = t + '<tr><td>Password</td><td><input type=password name=pw></td></tr>'
            t = t + '<tr><td colspan=2><input type=submit value="Create Account"></td></tr>'
            t = t + '</form></table>'
            www.serve(self,t, sidebar=self.__doc__, title = '/users/new')
            
class wwwSetLanguage(webapp.RequestHandler):
    """
    <h3>/users/setlanguage</h3>
    (also /users/setoptions)
    
    This request handler is used to set user preferences such as language settings,
    and preferences for filtering translations in search results. This request handler
    expects any combination of the following parameters<p>
    
    <ul><li>language1 = (ISO language code} : user's first preferred language</li>
    <li>language2 = {ISO language code} : user's second preferred language</li>
    <li>language3 = {ISO language code} : user's third preferred language</li>
    <li>allow_anonymous = y/n : allow/hide anonymous translations</li>
    <li>allow_machine = y/n : allow/hide machine translations</li>
    <li>allow_unscored = y/n : allow/hide unscored translations</li>
    <li>minimum_score = 0..5 : require minimum quality score for translations</li>
    <li>callback = URL to redirect to after saving settings</li></ul>
    
    The request handler will memorize these settings by placing cookies on the user's
    browser (the cookies have the same names as the CGI parameters). It also checks to see
    if the session cookie is present, and if it is a valid session, will also memorize these
    settings in the user's permanent user profile (User data store).<p>
    
    The request handler returns an empty HTML document, and sets browser cookies as needed.
    If the callback parameter is present, it will instead redirect to the URL given in the
    callback parameter.<p>
    
    """
    def get(self):
        """ Processes HTTP GET calls"""
        self.requesthandler()
    def post(self):
        """ Processes HTTP POST calls"""
        self.requesthandler()
    def requesthandler(self):
        """ Combined GET and POST request handler"""
        doc = self.request.get('doc')
        language1 = self.request.get('language1')
        language2 = self.request.get('language2')
        language3 = self.request.get('language3')
        tl = self.request.get('tl')
        allow_anonymous = self.request.get('allow_anonymous')
        allow_machine = self.request.get('allow_machine')
        allow_unscored = self.request.get('allow_unscored')
        minimum_score = self.request.get('minimum_score')
        callback = self.request.get('callback')
        remote_addr = self.request.remote_addr
        if len(tl) < 1 and len(language1) < 1 and len(language2) < 1 and len(language3) < 1 and len(allow_unscored) < 1 and len(allow_anonymous) < 1 and len(allow_machine) < 1 and len(minimum_score) < 1 and len(callback) < 1:
                t = '<table><form action=/users/setoptions method=get accept-charset=utf-8>'
                t = t + '<tr><td>Language #1 (ISO Code)</td><td><input type=text name=language1 maxlength=3></td></tr>'
                t = t + '<tr><td>Language #2 (ISO Code)</td><td><input type=text name=language2 maxlength=3></td></tr>'
                t = t + '<tr><td>Language #3 (ISO Code)</td><td><input type=text name=language3 maxlength=3></td></tr>'
                t = t + '<tr><td>Allow Anonymous Translations (y/n)</td><td><input type=text name=allow_anonymous maxlength=1></td></tr>'
                t = t + '<tr><td>Allow Machine Translations (y/n)</td><td><input type=text name=allow_machine maxlength=1></td></tr>'
                t = t + '<tr><td>Allow Unscored Translations (y/n)</td><td><input type=text name=allow_unscored maxlength=1></td></tr>'
                t = t + '<tr><td>Minimum Score</td><td><select name=minimum_score><option selected value=''></option'
                t = t + '<option value=1>1</option><option value=2>2</option><option value=3>3</option>'
                t = t + '<option value=4>4</option><option value=5>5</option></select></td></tr>'
                t = t + '<tr><td colspan=2><input type=submit value=OK></td></tr></table></form'
                www.serve(self,t, sidebar= self.__doc__, title = '/users/setoptions')        
        else:
            cookies = Cookies(self,max_age=36000)
            try:
                session = cookies['session']
            except:
                session = ''
            if len(tl) > 0:
                cookies['tl'] = tl
            if len(language1) > 0:
                cookies['language1'] = language1
            if len(language2) > 0:
                cookies['language2'] = language2
            if len(language3) > 0:
                cookies['language3'] = language3
            if len(allow_anonymous) > 0:
                cookies['allow_anonymous'] = allow_anonymous
            if len(allow_machine) > 0:
                cookies['allow_machine'] = allow_machine
            if len(allow_unscored) > 0:
                cookies['allow_unscored'] = allow_unscored
            if len(minimum_score) > 0:
                cookies['minimum_score'] = minimum_score
            if len(session) > 0:
                username = Users.getuser(session)
                if username is not None:
                    udb = db.Query(User)
                    udb.filter('username = ', username)
                    item = udb.get()
                    if item is not None:
                        item.language1 = language1
                        item.language2 = language2
                        item.language3 = language3
                        item.allow_anonymous = allow_anonymous
                        item.allow_machine = allow_machine
                        item.allow_unscored = allow_unscored
                        item.minimum_score = minimum_score
                        item.put()
                    elif user_service == 'google' or user_service == 'proxy':
                        item = User()
                        item.username = username
                        item.language1 = language1
                        item.language2 = language2
                        item.language3 = language3
                        item.allow_anonymous = allow_anonymous
                        item.allow_machine = allow_machine
                        item.allow_unscored = allow_unscored
                        item.minimum_score = minimum_score
                        item.put()
            self.response.headers['Content-Type']='text/html'
            if len(callback) > 0:
                self.redirect(callback)
            else:
                self.response.out.write('')

class wwwLogout(webapp.RequestHandler):
    """
    <h3>/users/logout</h3>
    
    This request handler deletes the session cookie if present, and clears the internal session register to
    log the user out. Returns ok or error in plain text document. You can also submit the form parameter
    session = session_id to force it to clear a session manually.
    """
    def get(self):
        """ Processes HTTP GET calls"""
        self.requesthandler()
    def post(self):
        """ Processes HTTP POST calls""" 
        self.requesthandler()
    def requesthandler(self):
        """ Combined GET and POST requesthandler."""
        doc = self.request.get('doc')
        if user_service == 'google':
            if doc =='y':
                www.serve(self,self.__doc__,title = '/users/logout')
            else:
                user = users.get_current_user()
                if user is not None:
                    self.redirect(users.create_logout_url(self.request.uri))
                else:
                    self.redirect('/')
        else:
            success = False
            cookies = Cookies(self,max_age=3600)
            t = '<table><form action=/users/logout method=post>'
            t = t + '<tr><td>Session ID</td><td><input type=text name=session></td></tr>'
            t = t + '<tr><td colspan=2><input type=submit value=Logout></td></tr></table></form>'
            if doc == 'y':
                www.serve(self,t, sidebar = self.__doc__, title = '/users/logout')
            else:
                try:
                    session = cookies['session']
                except:
                    session = self.request.get('session')
                if len(session) > 0:
                    success = Users.logout(session=session)
                    cookies['session']=''
                    self.response.headers['Content-Type']='text/plain'
                    if success:
                        self.response.out.write('ok')
                    else:
                        self.response.out.write('error')
                else:
                    www.serve(self,t, sidebar=self.__doc__, title = '/users/logout')

class wwwUpdate(webapp.RequestHandler):
    """
    <h3>/users/update</h3>

    This web service allows you to update basic user profile information.
    It expects the following required parameters:<p>
    
    <ul><li>username : username</li>
    <li>pw : password</li></ul>
    
    And the following optional parameters<p>
    
    <ul><li>firstname : First Name</li>
    <li>lastname : Last Name</li>
    <li>description : profile text</li>
    <li>skype : Skype handle</li>
    <li>facebook : Facebook profile URL</li>
    <li>linkedin : Linked in profile URL</li>
    <li>proz : ProZ username</li>
    <li>www : website or blog</li></ul>
    
    It responds with a simple 'ok' or 'error' message if the login is not valid
    
    """
    def get(self):
        """Implements HTTP GET calls to this service."""
        self.requesthandler()
    def post(self):
        """Implements HTTP POST calls to this service."""
        self.requesthandler()
    def requesthandler(self):
        """Combined GET and POST request handler."""
        username = self.request.get('username')
        callback = self.request.get('callback')
        pw = self.request.get('pw')
        if len(username) > 0 and len(pw) > 0:
            m = md5.new()
            m.update(pw)
            pwhash = string(m.hexdigest())
            udb = db.Query(Users)
            udb.filter('username = ', username)
            udb.filter('pwhash = ', pwhash)
            item = udb.get()
            if item is not None:
                firstname = self.request.get('firstname')
                lastname = self.request.get('lastname')
                description = self.request.get('description')
                skype = self.request.get('skype')
                facebook = self.request.get('facebook')
                linkedin = self.request.get('linkedin')
                proz = self.request.get('proz')
                wwwurl = self.request.get('www')
                if len(firstname) > 0:
                    item.firstname = firstname
                if len(lastname) > 0:
                    item.lastname = lastname
                if len(description) > 0:
                    item.description = description
                if len(skype) > 0:
                    item.skype = skype
                if len(facebook) > 0:
                    item.facebook = facebook
                if len(linkedin) > 0:
                    item.linkedin = linkedin
                if len(proz) > 0:
                    item.proz = proz
                if len(www) > 0:
                    item.www = wwwurl
                item.put
                if len(callback) > 0:
                    self.redirect(callback)
                else:
                    self.response.headers['Content-Type']='text/plain'
                    self.response.out.response('ok')
            else:
                if len(callback) > 0:
                    self.redirect(callback)
                else:
                    self.response.headers['Content-Type']='text/plain'
                    self.response.out.write('error')
        else:
            www.serve(self, self.__doc__, title='/users/update')
                
class wwwValidate(webapp.RequestHandler):
    """

    <h3>/users/validate</h3>

    This web service is a simple callback URL handler that prompts the user to click on a link in an email to validate a newly
    created account. If the link is valid, the user account is marked as validated, and is redirected to a page for successful
    activations (you can set the redirect URLs for success and failure in the header of this file).<p>

    This request handler expects the parameter k={validation key}, in the form:<p>
    
    /users/validate?k={key}
    
    """
    def get(self):
        """Implements HTTP GET calls to this service"""
        k=self.request.get('key')
        doc=self.request.get('doc')
        if len(k) > 0:
            if Users.validate(k):
                self.redirect('/search')
            else:
                self.redirect('/search')
        else:
            t = '<table><form action=/users/validate method=get>'
            t = t + '<tr><td>Validation key</td><td><input type=text name=k size=32>'
            t = t + '<tr><td colspan=2><input type=submit value=OK></td></tr></table></form>'
            www.serve(self,t, sidebar=self.__doc__, title = '/users/validate')

class wwwSetParm(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        username = self.request.get('username')
        pw = self.request.get('pw')
        parm = self.request.get('parm')
        value = self.request.get('value')
        remote_addr = self.request.remote_addr
        result = Users.setparm(username, pw, parm, value)
        if result:
            self.response.out.write('ok')
        else:
            self.response.out.write('error')
            
class wwwGetParm(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        username = self.request.get('username')
        parm = self.request.get('parm')
        value = Users.getparm(username, parm)
        self.response.headers['Content-Type']='text/plain'
        if type(value) is int:
            txt = str(value)
        elif type(value) is list:
            txt = ''
            for v in value:
                txt = txt + ',' + v
        else:
            txt = str(value)
        self.response.out.write(txt)

class wwwProxyUserTest(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        username = self.request.get('username')
        pw = self.request.get('pw')
        self.response.headers['Content-Type']='text/html'
        if username == 'fubar' and pw == 'fubar':
            self.response.out.write('Hello, welcome to WWL')
        else:
            self.response.out.write('Invalid username or password.')

application = webapp.WSGIApplication([('/users/auth', wwwAuth),
                                      ('/users/check', wwwCheckUser),
                                      ('/users/currentuser', wwwCurrentUser),
                                      ('/users/login', wwwAuth),
                                      ('/users/logout',wwwLogout),
                                      ('/users/new', wwwNewUser),
                                      ('/users/proxy', wwwProxyUserTest),
                                      ('/users/get', wwwGetParm),
                                      ('/users/set', wwwSetParm),
                                      ('/users/setlanguage',wwwSetLanguage),
                                      ('/users/setoptions',wwwSetLanguage),
                                      ('/users/update', wwwUpdate),
                                      ('/users/validate', wwwValidate)],
                                     debug=True)


def main():
    run_wsgi_app(application)


if __name__ == "__main__":
    main()
