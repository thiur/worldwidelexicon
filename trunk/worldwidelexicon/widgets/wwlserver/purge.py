import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from geo import geo
from database import Search
from database import Stats

class Purge(webapp.RequestHandler):
    def get(self, name=''):
        if name == 'search':
            result = Search.purge()
        elif name == 'geodb':
            result = geo.purge(name='geodb')
        elif name == 'stats':
            result = Stats.purge()
        else:
            result = geo.purge()
        self.response.out.write('ok')

application = webapp.WSGIApplication([('/purge', Purge),
                                      ('/heartbeat', Purge),
                                      (r'/purge/(.*)', Purge)],
                                     debug=True)

def main():
    run_wsgi_app(application)
    
if __name__ == "__main__":
    main()
