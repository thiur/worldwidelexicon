"""
This is a simple script to automatically extract excerpts from articles. It
requires BeautifulSoup.

Usage:
from excerpt_extractor import get_summary
url = "http://someurl.com/goes/here"
(title,description) = get_summary(url)

==========================================

Some examples, discussion, and comparison with the Facebook article extractor
are at http://blog.davidziegler.net/post/122176962/a-python-script-to-automatically-extract-excerpts-from

copyright: Copyright 2009 by David Ziegler
license: MIT License
website: http://github.com/dziegler/excerpt_extractor/tree/master
"""
from BeautifulSoup import *
import urllib2
import cookielib
import re

def cleanSoup(soup):
    # get rid of javascript, noscript and css
    [[tree.extract() for tree in soup(elem)] for elem in ('script','noscript','style')]
    # get rid of doctype
    subtree = soup.findAll(text=re.compile("DOCTYPE"))
    [tree.extract() for tree in subtree]
    # get rid of comments
    comments = soup.findAll(text=lambda text:isinstance(text,Comment))
    [comment.extract() for comment in comments]
    return soup

def removeHeaders(soup):
    [[tree.extract() for tree in soup(elem)] for elem in ('h1','h2','h3','h4','h5','h6')]
    return soup

def get_summary(url):
    cj = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    doc = opener.open(url).read()
    soup = cleanSoup(BeautifulSoup(doc,parseOnlyThese=SoupStrainer('head')))
    
    if not soup:
        raise ValueError, "Invalid output: %s" % url
    
    try:
        title = soup.head.title.string
    except:
        title = None
    
    description = ''
    for meta in soup.findAll('meta'):
        if 'description' == meta.get('name', '').lower():
            description = meta['content']
            break
        
    if not description:
        soup = removeHeaders(cleanSoup(BeautifulSoup(doc,parseOnlyThese=SoupStrainer('body'))))
        text = ''.join(soup.findAll(text=True)).split('\n')
#        description = ''
        description = max((len(i.strip()),i) for i in text)[1].strip()[0:255]
    
    metadata = dict(
        title = title,
        description = description,
    )
    return metadata

if __name__ == "__main__":
    urllist=("http://www.sfgate.com/cgi-bin/article.cgi?f=/c/a/2009/06/04/DD7V1806SV.DTL&type=performance",
              "http://www.chloeveltman.com/blog/2009/05/two-very-different-symphonies.html#links",
              "http://www.lemonde.fr",
              "http://www.elpais.es",
              "http://www.chloeveltman.com/blog/2009/06/child-prodigy-at-peabody-essex-museum.html#links")
    for u in urllist:
        metadata = get_summary(u)
        print metadata.get('title','') + '\n'
        print metadata.get('description', '') + '\n'
    
