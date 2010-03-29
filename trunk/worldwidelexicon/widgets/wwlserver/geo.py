"""
Geolocation Module
geo.py
by Brian S McConnell

This module encapsulates calls to geolocation services and maintains
a local cache of geolocated IP addresses, as well as an optional log
to record actions by location. The module calls the Maxmind
geolocation service.
"""

# import Google App Engine modules
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import urlfetch
from google.appengine.api import memcache
from google.appengine.api.labs import taskqueue
# import standard Python libraries
import cgi
import urllib
import string
import datetime
# import WWL libraries
from database import Websites
from database import Settings

def clean(text):
    try:
        utext = text.encode('utf-8')
    except:
        try:
            utext = text.encode('iso-8859-1')
        except:
            utext = text
    text = utext.decode('utf-8')
    return text

class GeoDB(db.Model):
    remote_addr = db.StringProperty(default = '')
    website = db.StringProperty(default = '')
    country = db.StringProperty(default = '')
    state = db.StringProperty(default = '')
    city = db.StringProperty(default = '')
    latitude = db.FloatProperty()
    longitude = db.FloatProperty()
    lastupdated = db.DateTimeProperty(auto_now_add = True)

class GeoLog(db.Model):
    date = db.DateTimeProperty(auto_now_add = True)
    remote_addr = db.StringProperty(default = '')
    website = db.StringProperty(default = '')
    country = db.StringProperty(default = '')
    state = db.StringProperty(default = '')
    city = db.StringProperty(default = '')
    latitude = db.FloatProperty()
    longitude = db.FloatProperty()
    action = db.StringProperty(default = '')
    username = db.StringProperty(default = '')
    sl = db.StringProperty(default = '')
    tl = db.StringProperty(default = '')

class geo():
    @staticmethod
    def log(remote_addr, city, state, country, latitude, longitude, action='', username='', sl ='', tl = '', website=''):
        return True
    @staticmethod
    def countries():
        clist = dict()
        return clist
    @staticmethod
    def purge(name=''):
        now = datetime.datetime.now()
        td = datetime.timedelta(days = -60)
        lastdate = now + td
        if name == 'geodb':
            gdb = db.Query(GeoDB)
            gdb.filter('country = ', '')
            results = gdb.fetch(limit=250)
            if len(results) > 0:
                db.delete(results)
                return True
            else:
                return False
        else:
            gdb = db.Query(GeoLog)
            gdb.filter('date < ', lastdate)
            results = gdb.fetch(limit=250)
            if len(results) > 0:
                db.delete(results)
                return True
            else:
                return False
    @staticmethod
    def query(remote_addr, website=''):
        license_key=Settings.get('maxmind')
        location = dict()
        geolist=list()
        location['country']=''
        location['state']=''
        location['city']=''
        location['latitude']=None
        location['longitude']=None
        if len(remote_addr) > 4 and license_key is not None:
            url = 'http://geoip1.maxmind.com/b?l=' + license_key + '&i=' + remote_addr
            try:
                result=urlfetch.fetch(url)
                if result.status_code == 200:
                    geo = result.content
            except:
                geo = ''
        else:
            geo = ''
        if len(geo) > 1:
            geolist = string.split(geo,',')
        if len(geolist) > 0:
            ctr=0
            for i in geolist:
                if ctr==0:
                    location['country']=i
                elif ctr==1:
                    location['state']=i
                elif ctr==2:
                    location['city']=i
                elif ctr==3:
                    if len(i) > 0:
                        location['latitude']=float(i)
                elif ctr==4:
                    if len(i) > 0:
                        location['longitude']=float(i)
                ctr=ctr+1
        return location
    @staticmethod
    def get(remote_addr, action='', username='', sl = '', tl = '', website = ''):
        username = clean(username)
        website = clean(website)
        location = memcache.get('geo|' + remote_addr)
        location = None
        if location is not None:
            return location
        else:
            gdb = db.Query(GeoDB)
            gdb.filter('remote_addr = ', remote_addr)
            item = gdb.get()
            location = dict()
            if item is not None:
                if len(location.get('country', '')) > 1:
                    location['city'] = clean(item.city)
                    location['state'] = clean(item.state)
                    location['country'] = clean(item.country)
                    location['latitude'] = item.latitude
                    location['longitude'] = item.longitude
                    memcache.set('geo|' + remote_addr, location, 1800)
                    geo.log(remote_addr, location['city'], location['state'], location['country'], location['latitude'], location['longitude'], action, username, sl, tl)
                    return location
            if len(location.get('country', '')) < 2:
                location = geo.query(remote_addr, website=website)
                if len(location.get('country','')) > 1:
                    gdb = db.Query(GeoDB)
                    gdb.filter('remote_addr = ', remote_addr)
                    item = gdb.get()
                    if item is None:
                        item = GeoDB()
                    try:
                        item.remote_addr = remote_addr
                        item.city = location['city']
                        item.state = location['state']
                        item.country = location['country']
                    except:
                        pass
                    try:
                        item.latitude = location['latitude']
                        item.longitude = location['longitude']
                    except:
                        pass
                    item.lastupdated = datetime.datetime.now()
                    item.website = website
                    try:
                        item.put()
                    except:
                        pass
                    memcache.set('geo|' + remote_addr, location, 1800)
                return location
