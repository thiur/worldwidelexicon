from google.appengine.ext import db
from google.appengine.api import memcache

class Cache(db.Model):
    """
    Persistent cache, implemented as a layer on top of memcache to
    improve performance. 
    """
    name = db.StringProperty(default='')
    value = db.TextProperty(default='')
    expirationdate = db.DateTimeProperty()
    @staticmethod
    def getitem(parm, ttl=7200):
        """
        fetches an item from memcache, if possible, and then looks in
        the Cache() datastore for the item, and if it is not expired
        returns its contents and refreshes the memcache entry. If the
        item is expired, it deletes it from the data store and returns
        None
        """
        if len(parm) > 250:
            m = md5.new()
            m.update(parm)
            parm = str(m.hexdigest())
        text = memcache.get(parm)
        if text is not None:
            return text
        else:
            cdb = db.Query(Cache)
            cdb.filter('name = ', parm)
            item = cdb.get()
            if item is None:
                return
            else:
                if datetime.datetime.now() > item.expirationdate:
                    item.delete()
                    return
                memcache.set(parm, item.value, ttl)
                return item.value
    @staticmethod
    def setitem(parm, v, ttl=7200):
        """
        Stores an item to memcache and to the datastore. 
        """
        td = datetime.timedelta(seconds=ttl)
        expirationdate = datetime.datetime.now() + td
        if len(parm) > 250:
            m = md5.new()
            m.update(parm)
            parm = str(m.hexdigest())
        memcache.set(parm, v, ttl)
        cdb = db.Query(Cache)
        cdb.filter('name = ', parm)
        item = cdb.get()
        if item is None:
            item = Cache()
            item.name = parm
        item.value = unicode(v, 'utf-8')
        item.expirationdate = expirationdate
        item.put()
        memcache.set(parm, v, ttl)
        return True
    @staticmethod
    def purge():
        """
        Purges expired items from the data store. Build a cron handler that
        calls this method. It returns True if items were deleted, False if
        not. 
        """
        cdb = db.Query(Cache)
        cdb.filter('expirationdate < ', datetime.datetime.now())
        results = cdb.fetch(limit=250)
        if results is not None:
            if len(results) > 0:
                db.delete(results)
                return True
        return False
