# -*- coding: utf-8 -*-
"""
Worldwide Lexicon Project
Analytics Module (analytics.py)
by Brian S McConnell <brian@worldwidelexicon.org>

This module implements web services for language analytics. 

NOTE: this documentation is generated automatically, and directly from the current
version of the WWL source code, via the PyDoc service. Because of the way App
Engine works, the hyperlinks in these files will not work, so your best option
is to print the documentation for offline review.

Copyright (c) 1998-2010, Worldwide Lexicon Inc, Brian S McConnell.
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
#
# import Google App Engine modules
#
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import urlfetch
from google.appengine.api import memcache
from google.appengine.api.labs import taskqueue
#
# import standard Python modules
#
import demjson
import urllib
import string
import md5
import datetime
import time
import pydoc
import codecs
import types
# insert import statements here
from geo import geo
from transcoder import transcoder
# insert declarations here

def clean(text):
    return transcoder.clean(text)

maxmind_api = '...foo...'
maxmind_url = ''
maxmind_enabled = False

class AnalyticsCustomers(db.Model):
    customerid = db.StringProperty(default='')
    domains = db.ListProperty(str)
    company = db.StringProperty(default='')
    email = db.StringProperty(default='')
    validated = db.BooleanProperty(default=False)
    datecreated = db.DateTimeProperty(auto_now_add=True)
    @staticmethod
    def new(company, email, domains=None):
        if len(company) > 0 and len(email) > 0:
            m = md5.new()
            m.update(str(datetime.datetime.now()))
            m.update(company)
            m.update(email)
            customerid = str(m.hexdigest())
            adb = db.Query(AnalyticsCustomers)
            adb.filter('company = ', company)
            adb.filter('email = ', email)
            item = adb.get()
            if item is None:
                item = AnalyticsCustomers()
                item.customerid = customerid
                item.company = company
                item.email = email
                item.validated = True
                item.put()
                return True
        return False

class AnalyticsLog(db.Model):
    """
    This is the primary data store for the analytics service and functions as a raw log file for the language
    analytics service. Other data stores are used to store rolled up data for display in customer reports.
    """
    guid = db.StringProperty(default='')
    timestamp = db.DateTimeProperty(auto_now_add=True)
    indexed = db.BooleanProperty(default=False)
    valid = db.BooleanProperty(default=False)
    customerid = db.StringProperty(default='')
    domain = db.StringProperty(default='')
    url = db.StringProperty(default='')
    locales = db.StringProperty(default='')
    user_agent = db.StringProperty(default='')
    userip = db.StringProperty(default='')
    @staticmethod
    def log(customerid, userip, url='', locales='', user_agent=''):
        if len(customerid) > 0 and len(userip) > 0:
            m = md5.new()
            m.update(str(datetime.datetime.now()))
            m.update(customerid)
            m.update(url)
            guid = str(m.hexdigest())
            item = AnalyticsLog()
            item.guid = guid
            item.customerid = customerid
            if len(url) > 0:
                url = string.replace(url, 'https://', '')
                url = string.replace(url, 'http://', '')
                urls = string.split(url, '/')
                if len(urls) > 1:
                    domain = urls[0]
                else:
                    domain = url
                item.url = url
                item.domain = domain
            item.locales = locales
            item.user_agent = user_agent
            item.userip = userip
            item.put()
            return True
        return False

class AnalyticsGeo(db.Model):
    customerid = db.StringProperty(default='')
    domain = db.StringProperty(default='')
    year = db.StringProperty(default='')
    month = db.StringProperty(default='')
    day = db.StringProperty(default='')
    country = db.StringProperty(default='')
    city = db.StringProperty(default='')
    requests = db.IntegerProperty(default=0)
    @staticmethod
    def inc(customerid, domain, country='', city=''):
        country = string.lower(country)
        city = string.lower(clean(city))
        if len(customerid) > 0 and len(country) > 0:
            try:
                gdb = db.Query(AnalyticsGeo)
                gdb.filter('customerid = ', customerid)
                gdb.filter('domain = ', domain)
                gdb.filter('country = ', country)
                gdb.filter('city = ', 'all')
                timestamp = datetime.datetime.now()
                year = str(timestamp.year)
                month = str(timestamp.month)
                day = str(timestamp.day)
                gdb.filter('year = ', year)
                gdb.filter('month = ', month)
                gdb.filter('day = ', day)
                item = gdb.get()
                if item is None:
                    item = AnalyticsGeo()
                    item.customerid = customerid
                    item.domain = domain
                    item.city = 'all'
                    item.year = year
                    item.month = month
                    item.day = day
                    item.requests = 1
                else:
                    item.requests = item.requests + 1
                item.put()
            except:
                pass
            if len(city) > 0:
                try:
                    gdb = db.Query(AnalyticsGeo)
                    gdb.filter('customerid = ', customerid)
                    gdb.filter('domain = ', domain)
                    gdb.filter('country = ', country)
                    gdb.filter('city = ', city)
                    timestamp = datetime.datetime.now()
                    year = str(timestamp.year)
                    month = str(timestamp.month)
                    day = str(timestamp.day)
                    gdb.filter('year = ', year)
                    gdb.filter('month = ', month)
                    gdb.filter('day = ', day)
                    item = gdb.get()
                    if item is None:
                        item = AnalyticsGeo()
                        item.customerid = customerid
                        item.domain = domain
                        item.country = country
                        item.city = city
                        item.year = year
                        item.month = month
                        item.day = day
                        item.requests = 1
                    else:
                        item.requests = item.requests + 1
                    item.put()
                except:
                    pass

class AnalyticsReports(db.Model):
    customerid = db.StringProperty(default='')
    dategenerated = db.DateTimeProperty(auto_now_add = True)
    text = db.TextProperty(default='')
    @staticmethod
    def find(customerid):
        if len(customerid) > 0:
            rdb = db.Query(AnalyticsReports)
            rdb.filter('customerid = ', customerid)
            rdb.get()
            if item is not None:
                return item.text
            else:
                return 'No report found'
        else:
            return 'No Report Found'

class AnalyticsLanguages(db.Model):
    """
    This data store contains rolled up data about language and locale preferences across a customer's website(s), and is indexed
    by year, month, day, domain and customer ID.
    """
    customerid = db.StringProperty(default='')
    domain = db.StringProperty(default='')
    year = db.StringProperty(default='')
    month = db.StringProperty(default='')
    day = db.StringProperty(default='')
    language = db.StringProperty(default='')
    locale = db.StringProperty(default='')
    requests = db.IntegerProperty(default=0)
    countries = db.ListProperty(str)
    lastrequest = db.DateTimeProperty(auto_now_add=True)
    @staticmethod
    def inc(customerid, domain, language='', locale='', country=''):
        timestamp = datetime.datetime.now()
        year = str(timestamp.year)
        month = str(timestamp.month)
        day = str(timestamp.day)
        if len(customerid) > 0 and len(locale) > 0:
            ldb = db.Query(AnalyticsLanguages)
            ldb.filter('customerid = ', customerid)
            ldb.filter('domain = ', domain)
            ldb.filter('year = ', year)
            ldb.filter('month = ', month)
            ldb.filter('day = ', day)
            if len(language) > 0:
                ldb.filter('language = ', language)
            if len(locale) > 0:
                ldb.filter('locale = ', locale)
            item = ldb.get()
            if item is None:
                item = AnalyticsLanguages()
                item.customerid = customerid
                item.domain = domain
                item.year = year
                item.month = month
                item.day = day
                item.language = language
                item.locale = locale
                item.requests = 1
                if len(country) > 0:
                    countries = list()
                    countries.append(country)
                    item.countries = countries
            else:
                item.requests = item.requests + 1
                item.lastrequest = datetime.datetime.now()
                if len(country) > 0:
                    if country not in item.countries:
                        countries = item.countries
                        countries.append(country)
                        item.countries = countries
            item.put()
            return True
        return False

class AnalyticsURLs(db.Model):
    """
    This data store contains a list of URLs requested by users and tracks which languages those URLs are being requested in.
    This in turn is used to display ranked lists of the most popular URLs by language. 
    """
    customerid = db.StringProperty(default='')
    url = db.StringProperty(default='')
    year = db.StringProperty(default='')
    month = db.StringProperty(default='')
    day = db.StringProperty(default='')
    locale = db.StringProperty(default='')
    requests = db.IntegerProperty(default=0)
    @staticmethod
    def inc(customerid, url, locale):
        timestamp = datetime.datetime.now()
        year = str(timestamp.year)
        month = str(timestamp.month)
        day = str(timestamp.day)
        if len(customerid) > 0 and len(url) > 0 and len(locale) > 0:
            url = string.replace(url, 'https://', '')
            url = string.replace(url, 'http://', '')
            if len(locale) > 0:
                udb = db.Query(AnalyticsURLs)
                udb.filter('customerid = ', customerid)
                udb.filter('url = ', url)
                udb.filter('locale = ', locale)
                udb.filter('year = ', year)
                udb.filter('month = ', month)
                udb.filter('day = ', day)
                item = udb.get()
                if item is None:
                    item = AnalyticsURLs()
                    item.customerid = customerid
                    item.url = url
                    item.locale = locale
                    item.requests = 1
                    item.year = year
                    item.month = month
                    item.day = day
                    item.requests = 1
                else:
                    item.requests = item.requests + 1
                item.put()
                return True
        return False

class AnalyticsVisitors(db.Model):
    """
    This data store contains a list of user IP addresses and functions as a counter that tracks the number of times
    a given IP address has interacted with a customer's website.
    """
    customerid = db.StringProperty(default='')
    domain = db.StringProperty(default='')
    userip = db.StringProperty(default='')
    year = db.StringProperty(default='2010')
    month = db.StringProperty(default='all')
    day = db.StringProperty(default='all')
    country = db.StringProperty(default='')
    city = db.StringProperty(default='')
    languages = db.ListProperty(str)
    locales = db.ListProperty(str)
    bilingual = db.BooleanProperty(default=False)
    multilingual = db.BooleanProperty(default=False)
    urls = db.ListProperty(str)
    requests = db.IntegerProperty(default=0)
    @staticmethod
    def inc(customerid, userip, domain='', url='', country='', city='', locales=None):
        if len(customerid) > 0 and len(userip) > 0:
            timestamp = datetime.datetime.now()
            year = str(timestamp.year)
            month = str(timestamp.month)
            day = str(timestamp.day)
            vdb = db.Query(AnalyticsVisitors)
            vdb.filter('customerid = ', customerid)
            vdb.filter('userip = ', userip)
            vdb.filter('domain = ', domain)
            vdb.filter('year = ', year)
            vdb.filter('month = ', month)
            vdb.filter('day = ', day)
            item = vdb.get()
            if type(locales) is not list:
                if locales is not None:
                    locales = string.split(locales,',')
            if item is None:
                item = AnalyticsVisitors()
                item.customerid = customerid
                item.userip = userip
                item.domain = domain
                item.year = year
                item.month = month
                item.day = day
                item.country = country
                item.city = city
                if type(locales) is list:
                    item.locales = locales
            if len(locales) > 1:
                item.bilingual = True
            if len(locales) > 2:
                item.multilingual = True
            urls = item.urls
            if url not in urls:
                urls.append(url)
            item.urls = urls
            item.requests = item.requests + 1
            item.put()
            return True
        return False
    @staticmethod
    def find(userip, customerid='', domain=''):
        if len(userip) > 0:
            vdb = db.Query(AnalyticsVisitors)
            vdb.filter('userip = ', userip)
            if len(customerid) > 0:
                vdb.filter('customerid = ', customerid)
            if len(domain) > 0:
                vdb.filter('domain = ', domain)
            item = vdb.get()
            if item is not None:
                return True
        return False
    
class AnalyticsHandler(webapp.RequestHandler):
    def get(self, customer):
        # serve 1 pixel image
        text = memcache.get('http://www.worldwidelexicon.org/image/1x1.gif')
        if text is None:
            response = urlfetch.fetch(url = 'http://www.worldwidelexicon.org/image/1x1.gif')
            if response.status_code == 200:
                text = response.content
                memcache.set('http://www.worldwidelexicon.org/image/1x1.gif', text, 300)
        if text is not None:
            self.response.headers['Content-Type']='image/gif'
        #self.response.headers['Content-Length']='43'
        #self.response.out.write('GIF89a.............!.......,...........D..;')
            self.response.out.write(text)
        # capture browser information, headers
        try:
            url = self.request.headers['Referer']
        except:
            url = ''
        try:
            locales = string.lower(self.request.headers['Accept-Language'])
        except:
            locales = ''
        try:
            user_agent = self.request.headers['User-Agent']
        except:
            user_agent = 'Unknown'
        userip = self.request.remote_addr
        # log data
        AnalyticsLog.log(customer, userip, url=url , locales=locales, user_agent=user_agent)
        # schedule counter tasks
        p = dict()
        p['customerid']=customer
        p['url']=url
        p['locales']=locales
        p['user_agent']=user_agent
        p['userip']=userip
        taskqueue.add(url='/analytics/visitors', params=p)

class AnalyticsWorkerVisitors(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        # get parameters
        customerid = self.request.get('customerid')
        url = self.request.get('url')
        url = string.replace(url, 'https://', '')
        url = string.replace(url, 'http://', '')
        urls = string.split(url, '/')
        if len(urls) > 1:
            domain = urls[0]
        else:
            domain = url
        locales = self.request.get('locales')
        user_agent = self.request.get('user_agent')
        userip = self.request.get('userip')
        # geolocate IP address
        location = geo.get(userip)
        country = string.lower(location.get('country', ''))
        city = string.lower(clean(location.get('city','')))
        latitude = location.get('latitude', '')
        longitude = location.get('longitude', '')
        # schedule child tasks to count languages, URLs
        p = dict()
        p['customerid']=customerid
        p['url']=url
        p['locales']=locales
        p['user_agent']=user_agent
        p['userip']=userip
        p['country']=country
        p['city']=city
        p['latitude']=str(latitude)
        p['longitude']=str(longitude)
        AnalyticsGeo.inc(customerid, domain, country=country, city=city)
        taskqueue.add(url='/analytics/languages',params=p)
        taskqueue.add(url='/analytics/urls', params=p)
        # update visitors data stores
        AnalyticsVisitors.inc(customerid, userip, domain=domain, url=url, country=country, city=city, locales=locales)
        # generate response
        self.response.out.write('ok')

class AnalyticsWorkerLanguages(webapp.RequestHandler):
    """
    This task queue worker tabulates visits/requests by locale code, and is used to provide the website owner
    with a synopsis of website traffic by language-locale code, and thus to track the top languages used by website
    visitors. 
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        customerid = self.request.get('customerid')
        url = self.request.get('url')
        locales = self.request.get('locales')
        user_agent = self.request.get('user_agent')
        country = self.request.get('country')
        url = string.replace(url, 'https://', '')
        url = string.replace(url, 'http://', '')
        urls = string.split(url, '/')
        if len(urls) > 1:
            domain = urls[0]
        else:
            domain = url
        locales = string.split(locales, ',')
        for l in locales:
            if string.count(l, '-') > 0:
                lx = l[0:5]
            else:
                lx = l[0:2]
            AnalyticsLanguages.inc(customerid, domain, locale=lx, country=country)        
        self.response.out.write('ok')

class AnalyticsWorkerURLs(webapp.RequestHandler):
    """
    This task queue worker updates the counters for URLs, enabling the system to generate reports for the top URLs for
    the top languages on a website for any given day. 
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        customerid = self.request.get('customerid')
        url = self.request.get('url')
        locales = self.request.get('locales')
        locales = string.split(locales, ',')
        user_agent = self.request.get('user_agent')
        country = self.request.get('country')
        city = self.request.get('city')
        url = string.replace(url, 'https://','')
        url = string.replace(url, 'http://', '')
        for l in locales:
            if string.count(l, '-') > 0:
                lx = l[0:5]
            else:
                lx = l[0:2]
            AnalyticsURLs.inc(customerid, url, lx)
        self.response.out.write('ok')

class AnalyticsReport(webapp.RequestHandler):
    """
    This request handler displays a consolidated report for a customer and summarizes website activity by locale,
    location, and top trending URLs.
    """
    def get(self, customerid):
        p = dict()
        p['customerid']=customerid
        taskqueue.add(url = '/analytics/generate', params = p)
        self.response.out.write('Your report is being generated, <a href=/analytics/view/' + customerid + '>click here</a> to view it.')

class AnalyticsView(webapp.RequestHandler):
    def get(self, customerid):
        text = AnalyticsReports.find(customerid)
        self.response.out.write(text)

application = webapp.WSGIApplication([('/analytics/report/(.*)', AnalyticsReport),
                                      ('/analytics/visitors', AnalyticsWorkerVisitors),
                                      ('/analytics/languages', AnalyticsWorkerLanguages),
                                      ('/analytics/urls', AnalyticsWorkerURLs),
                                      ('/analytics/(.*)', AnalyticsHandler)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
