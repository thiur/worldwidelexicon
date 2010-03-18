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
from database import Users
from database import Presence

#
# Define Callback URLs for User Validation Success or Failure
#
validate_success_url = '/'
validate_failure_url = '/'

def clean(text):
    if text is not None:
        try:
            utext = text.encode('utf-8')
        except:
            try:
                utext = text.encode('iso-8859-1')
            except:
                utext = text
        text = utext.decode('utf-8')
        return text
    else:
        return ''

#
# Define Simple User Access Rights
#

# Type of user service in use: can be simple, wwl, google or proxy
user_service = 'wwl'

class wwwAuth(webapp.RequestHandler):
    """
    
    wwwAuth()
    /users/auth
    
    This request handler implements the /users/auth
    request handler. It expects the following parameters:
    
    session (cookie) : md5hash key for current session
    username : WWL or external username
    pw : WWL or external password
    
    It responds in plain text (text/plain) with either
    a session key (valid login or session key) or
    an empty string if credentials are invalid or expired
    
    If the module is configured to use Google's user
    management system, it will redirect calls to
    /users/auth to a Google login screen. Note that we
    generally do not recommend using Google's user management
    system if you will be running WWL as an embedded
    service.
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
            if len(username) > 4 or len(session) > 4:
                session = Users.auth(username, pw, session, remote_addr, city=city, state=state, country=country, latitude=latitude, longitude=longitude)
                if session is not None:
                    cookies['session'] = session
                    if user_service != 'simple':
                        udb = db.Query(Users)
                        udb.filter('username = ', 'username')
                        item = udb.get()
                        if item is not None:
                            try:
                                if len(item.allow_anonymous) > 0:
                                    cookies['allow_anonymous']=allow_anonymous
                                if len(item.allow_machine) > 0:
                                    cookies['allow_machine']=allow_machine
                                if len(item.allow_unscored) > 0:
                                    cookies['allow_unscored']=allow_unscored
                                if len(item.minimum_score) > 0:
                                    cookies['minimum_score']=minimum_score
                            except:
                                pass
                self.response.headers['Content-Type']='text/plain'
                if len(callback) > 0:
                    self.redirect(callback)
                else:
                    if type(session) is dict:
                        self.response.out.write(session.get('session',''))
                    else:
                        self.response.out.write('')
            else:
                www.serve(self,self.__doc__, title = '/users/auth')
                self.response.out.write('<h3>Test Form</h3>')
                self.response.out.write('<form action=/users/auth method=post accept-charset=utf-8>')
                self.response.out.write('<table><tr><td wwlapi="tr">Username</td><td><input type=text name=username></td></tr>')
                self.response.out.write('<tr><td wwlapi="tr">Password</td><td><input type=password name=pw></td></tr>')
                self.response.out.write('<tr><td colspan=2><input type=submit value=LOGIN></td></tr>')
                self.response.out.write('</table></form>')

class wwwCheckUser(webapp.RequestHandler):
    """
    
    wwwCheckUser()
    /users/check
    
    This web service tells you if the username is available for registration
    
    It expects the parameter username={username}
    
    It responds with in plain text as follows:
    y (username available)
    n (username taken)
    
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
            www.serve(self,self.__doc__, title = '/users/check')
            self.response.out.write('<h3>Test Form</h3>')
            self.response.out.write('<form action=/users/check method=get accept-charset=utf-8>')
            self.response.out.write('Username: <input type=text name=username><input type=submit value=OK></form>')

class wwwCount(webapp.RequestHandler):
    """
    /users/count
    
    This web service returns the edit and word counts for translations
    posted by a user. The request handler expects the following parameters:
    
    username : WWL or external username

    if username is blank, the request handler will serve an HTML form for generating test queries.
    
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
            www.serve(self,self.__doc__, title = '/users/count')
            self.response.out.write('<h3>Test Form</h3>')
            self.response.out.write('<form action=/users/count method=get accept-charset=utf-8>')
            self.response.out.write('Username or IP address: <input type=text name=username><input type=submit value=OK></form>')

class wwwCurrentUser(webapp.RequestHandler):
    """
    
    wwwCurrentUser()
    /users/currentuser
    
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
    
    wwwNewUser(webapp.RequestHandler):
    
    /users/new
    
    This request handler creates a new user account and issues
    a session key. It assumes that the user creation script
    will generate and send a welcome email to the user.
    (You can implement an email delivery script in App Engine
    if desired).
    
    It expects the following parameters:
    
    username : selected username
    email : email address
    pw : selected password
    
    And the following optional parameters:
    
    firstname
    lastname
    description
    skype
    facebook
    linkedin
    www
    tags
    city
    state
    country
    
    The script will create the new user, issue a validation key
    which will be returned in plain text. It will return an
    empty string if user creation failed because the username
    was already selected or the password was shorted than 8 chars.
    
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
            www.serve(self,self.__doc__, title = '/users/new')
            self.response.out.write('<h3>Test Form</h3>')
            self.response.out.write('<form action=/users/new method=post accept-charset=utf-8>')
            self.response.out.write('<table>')
            self.response.out.write('<tr><td>Username</td><td><input type=text name=username></td></tr>')
            self.response.out.write('<tr><td>Email</td><td><input type=text name=email></td></tr>')
            self.response.out.write('<tr><td>Password</td><td><input type=password name=pw></td></tr>')
            self.response.out.write('<tr><td colspan=2><input type=submit value="Create Account"></td></tr>')
            self.response.out.write('</form></table>')
            
class wwwSetLanguage(webapp.RequestHandler):
    """
    
    wwwSetLanguage(webapp.RequestHandler):
    
    /users/setlanguage
    /users/setoptions
    
    This request handler is used to set user preferences such as language settings,
    and preferences for filtering translations in search results. This request handler
    expects any combination of the following parameters
    
    language1 = (ISO language code} : user's first preferred language
    language2 = {ISO language code} : user's second preferred language
    language3 = {ISO language code} : user's third preferred language
    allow_anonymous = y/n : allow/hide anonymous translations
    allow_machine = y/n : allow/hide machine translations
    allow_unscored = y/n : allow/hide unscored translations
    minimum_score = 0..5 : require minimum quality score for translations
    callback = URL to redirect to after saving settings
    
    The request handler will memorize these settings by placing cookies on the user's
    browser (the cookies have the same names as the CGI parameters). It also checks to see
    if the session cookie is present, and if it is a valid session, will also memorize these
    settings in the user's permanent user profile (User data store).
    
    The request handler returns an empty HTML document, and sets browser cookies as needed.
    If the callback parameter is present, it will instead redirect to the URL given in the
    callback parameter.
    
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
                www.serve(self,self.__doc__, title = '/users/setoptions')
                self.response.out.write('<h3>Test Form</h3>')
                self.response.out.write('<form action=/users/setoptions method=get accept-charset=utf-8>')
                self.response.out.write('<table>')
                self.response.out.write('<tr><td>Language #1 (ISO Code)</td><td><input type=text name=language1 maxlength=3></td></tr>')
                self.response.out.write('<tr><td>Language #2 (ISO Code)</td><td><input type=text name=language2 maxlength=3></td></tr>')
                self.response.out.write('<tr><td>Language #3 (ISO Code)</td><td><input type=text name=language3 maxlength=3></td></tr>')
                self.response.out.write('<tr><td>Allow Anonymous Translations (y/n)</td><td><input type=text name=allow_anonymous maxlength=1></td></tr>')
                self.response.out.write('<tr><td>Allow Machine Translations (y/n)</td><td><input type=text name=allow_machine maxlength=1></td></tr>')
                self.response.out.write('<tr><td>Allow Unscored Translations (y/n)</td><td><input type=text name=allow_unscored maxlength=1></td></tr>')
                self.response.out.write('<tr><td>Minimum Score</td><td><select name=minimum_score><option selected value=''></option')
                self.response.out.write('<option value=1>1</option><option value=2>2</option><option value=3>3</option>')
                self.response.out.write('<option value=4>4</option><option value=5>5</option></select></td></tr>')
                self.response.out.write('<tr><td colspan=2><input type=submit value=OK></td></tr></table></form')
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
    #
    # wwwLogout
    # /users/logout
    #
    # This request handler deletes the session cookie if
    # present, and clears the internal session register to
    # log the user out. Returns ok or error in plain text
    # document.
    #
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
            if doc == 'y':
                www.serve(self,self.__doc__, title = '/users/logout')
            else:
                try:
                    session = cookies['session']
                except:
                    session = ''
                if len(session) > 0:
                    success = Users.logout(session=session)
                    cookies['session']=''
                self.response.headers['Content-Type']='text/plain'
                if success:
                    self.response.out.write('ok')
                else:
                    self.response.out.write('error')

class wwwUpdate(webapp.RequestHandler):
    """
    /users/update

    This web service allows you to update basic user profile information.
    It expects the following required parameters:
    
    username : username
    pw : password
    
    And the following optional parameters
    
    firstname : First Name
    lastname : Last Name
    description : profile text
    skype : Skype handle
    facebook : Facebook profile URL
    linkedin : Linked in profile URL
    proz : ProZ username
    www : website or blog
    
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

    /users/validate

    This web service is a simple callback URL handler that prompts the user to click on a link in an email to validate a newly
    created account. If the link is valid, the user account is marked as validated, and is redirected to a page for successful
    activations (you can set the redirect URLs for success and failure in the header of this file).

    This request handler expects the parameter k={validation key}, in the form:
    
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
            www.serve(self,self.__doc__, title = '/users/validate')
            self.response.out.write('<h3>Test Form</h3>')
            self.response.out.write('<form action=/users/validate method=get>')
            self.response.out.write('<div wwlapi="tr">Validation key:</div> <input type=text name=k size=32><input type=submit value=OK></form>')

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
        
class presenceFind(webapp.RequestHandler):
    """
    /presence/find
    
    This request handler is used to find IM translators and other real-time
    resources. It expects the following list of parameters:
    
    network = the IM or translation network to query
    status = user status (e.g. 'available', 'busy', 'away', if omitted it
            assumes you are looking for available users)
    languages = comma separated list of language codes
    
    It returns a newline separated list of usernames that match the desired
    state.
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        network = self.request.get('network')
        status = self.request.get('status')
        languages = string.split(self.request.get('languages'), ',')
        if len(network) > 0 and len(status) > 0 and len(languages) > 0:
            self.response.headers['Content-Type']='text/plain'
            records = Presence.find(network,status,languages)
            for r in records:
                self.response.out.write(r + '\n')
        else:
            www.serve(self, self.__doc__)
            self.response.out.write('<form action=/presence/find method=get><table>')
            self.response.out.write('<tr><td>IM or Translation Network</td><td><input type=text name=network></td></tr>')
            self.response.out.write('<tr><td>Status</td><td><input type=text name=status></td></tr>')
            self.response.out.write('<tr><td>Languages (ISO codes, comma separated)</td><td><input type=text name=languages></td></tr>')
            self.response.out.write('<tr><td colspan=2><input type=submit value=OK></td></tr>')
            self.response.out.write('</table></form>')
            
class presenceSet(webapp.RequestHandler):
    """
    /presence/set
    
    Sets the current status of a user on a IM or translation network, used to
    maintain an index of who is available to translate to which languages. You
    should call this with an update at least once every two minutes, as these
    updates have a short time to live (2 - 5 minutes)
    
    It expects the following parameters
    
    wwlusername = WWL username
    pw = WWL password
    username = username on IM network or translation network
    network = IM or translation network (e.g. Skype)
    status = current state
    
    It returns ok or an error message
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        wwlusername = self.request.get('wwlusername')
        username = self.request.get('username')
        pw = self.request.get('pw')
        remote_addr = self.request.remote_addr
        if len(wwlusername) > 0 and len(pw) > 0:
            network = self.request.get('network')
            status = self.request.get('status')
            languages = string.split(self.request.get('languages'), ',')
            self.response.headers['Content-Type']='text/plain'
            if Users.pw(wwlusername, pw):
                result = Presence.set(username, network, status, languages)
                if result:
                    self.response.out.write('ok')
                else:
                    self.response.out.write('error')
            else:
                self.response.out.write('error')
        else:
            www.serve(self, self.__doc__)
            self.response.out.write('<form action=/presence/set method=get>')
            self.response.out.write('<table>')
            self.response.out.write('<tr><td>WWL Username</td><td><input type=text name=wwlusername></td></tr>')
            self.response.out.write('<tr><td>WWL Password</td><td><input type=text name=pw></td></tr>')
            self.response.out.write('<tr><td>Username (On IM Or Translation Network)</td><td><input type=text name=username></td></tr>')
            self.response.out.write('<tr><td>IM or Translation Network</td><td><input type=text name=network></td></tr>')
            self.response.out.write('<tr><td>Status</td><td><input type=text name=status></td></tr>')
            self.response.out.write('<tr><td>Languages (ISO codes, comma separated)</td><td><input type=text name=languages></td></tr>')
            self.response.out.write('<tr><td colspan=2><input type=submit value=OK></td></tr>')
            self.response.out.write('</table></form>')
            
class presenceGet(webapp.RequestHandler):
    """
    /presence/get
    
    This request handler returns the current status of a user on an IM or
    translation network that is using WWL to track user presence status for
    translation. It expects the following parameters:
    
    username = username on target IM or translation network
    network = IM or translation network (e.g. skype)
    
    It returns an empty string if the user is not available for translation,
    or a comma separated list of language codes if the user is available to
    translate. 
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        username = self.request.get('username')
        network = self.request.get('network')
        self.response.headers['Content-Type']='text/plain'
        if len(username) > 0 and len(network) > 0:
            status = memcache.get('presence|username=' + username + '|network=' + network)
            languages = list()
            if type(status) is list:
                if len(status) > 1:
                    txt = ''
                    for s in status:
                        if s not in languages:
                            txt = txt + s + ','
                            languages.append(s)
                        self.response.out.write(txt)
                elif len(status) > 0:
                    self.response.out.write(status[0])
                else:
                    self.response.out.write('')
        else:
            www.serve(self, self.__doc__)
            self.response.out.write('<form action=/presence/get method=get>')
            self.response.out.write('<table><tr><td>Username</td><td><input type=text name=username></td></tr>')
            self.response.out.write('<tr><td>Network</td><td><input type=text name=network></td></tr>')
            self.response.out.write('<tr><td colspan=2><input type=submit value=OK></td></tr>')
            self.response.out.write('</table></form>')

application = webapp.WSGIApplication([('/users/auth', wwwAuth),
                                      ('/users/check', wwwCheckUser),
                                      ('/users/count', wwwCount),
                                      ('/users/currentuser', wwwCurrentUser),
                                      ('/users/login', wwwAuth),
                                      ('/users/logout',wwwLogout),
                                      ('/users/new', wwwNewUser),
                                      ('/users/get', wwwGetParm),
                                      ('/users/set', wwwSetParm),
                                      ('/users/setlanguage',wwwSetLanguage),
                                      ('/users/setoptions',wwwSetLanguage),
                                      ('/users/update', wwwUpdate),
                                      ('/users/validate', wwwValidate),
                                      ('/presence/find', presenceFind),
                                      ('/presence/get', presenceGet),
                                      ('/presence/set', presenceSet)],
                                     debug=True)


def main():
    run_wsgi_app(application)


if __name__ == "__main__":
    main()
