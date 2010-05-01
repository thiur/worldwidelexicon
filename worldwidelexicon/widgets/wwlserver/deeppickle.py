"""
DeepPickle()
Written by Brian S McConnell <brian@worldwidelexicon.org>

General purpose recordset encoder. Enables you to encode a row/column recordset in a variety
of formats, including xml, json, rss, csv/text, PO/gettext and XLIFF. This is not intended to
pickle complex, nested objects, but rather to render objects, dictionaries and lists of objects
row-column style in popular output formats. If you have suggestions, or improvements, please
contact brian@worldwidelexicon.org This module is maintained and distributed independently and
as part of the Worldwide Lexicon system. 

Typical Use Case:

# instantiate the class
d = DeepPickle()

# pickle a single item or record
print d.pickleItem(d, output_format)

# pickle a row/column recordset (list object consisting of dict or instance objects)
print d.pickleTable(d, output_format)

OUTSTANDING ISSUES / TO-DO LIST

* Replace hand coded generator with template based generator to enable rapid prototyping for
  new output formats
* Improve escape encoding for XML based output formats (most issues have been resolved but there
  are occasional cases of malformed output)
* Improve JSON output to eliminate blank objects
* Implement efficient text based, easy to parse output format (derived from text files) for use
  by client applications doing bulk search/replace operations, and need to do so efficiently
  with minimal parsing overhead, with easy option to locally cache in memory or disk.
* Generally comb through the library to clean things up, add documentation and take a second look
  now that it has been in use for a while. 

Copyright (c) 1998-2010, Brian S McConnell, Worldwide Lexicon Inc.
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
import types
import string
import urllib
import codecs
from xml.sax.saxutils import escape

class record():
    pass

class DeepPickle():
    """
    DeepPickle() contains two publicly accessed methods, pickleItem(), which is used
    to render a single item, object or dictionary, and pickleTable(), which is used
    to render a row-column recordset (a list of classes or dictionaries). 
    """
    title = ''                          # name of document or table
    parent = 'records'                      # name of parent type (parent XML node)
    description = ''                    # description of document or RSS feed
    # default RSS related settings
    rss_title = 'RSS Feed'
    rss_author = 'WWL'
    rss_description = 'WWL RSS Feed'
    rss_item_title = 'st'
    rss_item_description = 'tt'
    rss_item_author = 'username'
    rss_item_link = 'url'
    rss_item_guid = 'refid'
    autoheader = False
    simple_column = 'tt'
    # default PO/gettext settings (columns to map data from)
    po_source = 'st'
    po_target = 'tt'
    # default HTML settings, for HTML output
    html_title = 'Deep Pickle : Automatic Output Generator'
    html_head = 'Deep Pickle : Automatic Output Generator'
    html_intro = 'Here is a table containing the results of the query you submitted.'
    html_headers = '<meta keywords=hello,word>'
    # default mode (row/column table)
    mode = 'table'
    # default output format (xml)
    default_output = 'xml'
    
    def pickleItem(self,obj,output='xml'):
        """
        Converts a class or dict object to a one row recordset in the desired output format.
        It expects the parameter obj, which can be a dictionary (dict) or an instance type
        (user created class). If it is a dict, it will map dictionary keys to column fields.
        If it is a user created class, it will map object properties to column fields. It
        returns a text/unicode(utf-8) string in the desired output format, xml by default.
        """
        self.mode = 'item'
        if len(output) < 1:
            output = self.default_output
        if obj is not None:
            if type(obj) is dict:
                keys = obj.keys()
                r = record()
                for k in keys:
                    if string.count(k,'__') < 1:
                        setattr(r,k,obj[k])
            r = obj
            t = ''
            t = t + self.makeHeader(r,output)
            t = t + self.makeRow(r, output)
            t = t + self.makeFooter(r,output)
            return t
    def pickleTable(self,obj,output='xml'):
        """
        Converts a list of dict or instance (user created class) objects to a row/column
        text, in the selected output format (xml by default). It expects the following
        parameters: obj, which should be a list of dict or instance objects, and output
        format, which can be xml, json, text, po, xliff or rss. It will return a Unicode
        string in the desired format, or an empty string if it is unable to render the
        list of objects.
        """
        t = ''
        if len(output) < 1:
            output = self.default_output
        if obj is not None and type(obj) is types.ListType:
            t = self.makeHeader(obj,output)
            for r in obj:
                    t = t + self.makeRow(r,output)
            t = t + self.makeFooter(obj,output)
        elif obj is not None and type(obj) is types.InstanceType:
            t = self.pickleItem(obj,output)
        elif obj is not None and type(obj) is dict:
            t = self.pickleItem(obj,output)
        else:
            t = ''
        return t
    def makeHeader(self,obj,output):
        """
        Generates the header of the output file (e.g. <?xml version=1.0>... for an XML
        response). You generally do not call this method directly, as it is called within
        the pickleItem() and pickleTable() methods.
        """
        if output=='xml':
            if self.autoheader:
                t = '<?xml version=\"1.0\" encoding="utf-8"?>'
            else:
                t = ''
            if self.mode == 'table':
                return t + '<' + self.parent + '>'
            else:
                return t + '<record>'
        elif output=='xliff':
            if self.autoheader:
                t = '<?xml version=\"1.0\" encoding="utf-8"?>'
            else:
                t = ''
            t = t + '<xliff version=\"1.1\">'
            t = t + '<file>'
            t = t + '<header></header>'
            t = t + '<body>'
            return t
        elif output=='po':
            t = '#. PO File Generated By Worldwide Lexicon Simple Localization Service\n'
            t = t + '#.\n'
            t = t + '\n'
            return t
        elif output=='text':
            t = ''
            if type(obj) is types.ListType:
                if len(obj) > 0:
                    item = obj[0]
                    colnames= dir(item)
                    for c in colnames:
                        if c is not None and c.count('__') == 0:
                            t = t + '\"' + c + '\",'
                    t = t + '\"\"\n'
            elif type(obj) is dict:
                colnames = obj.keys()
                for c in colnames:
                    if c is not None and c.count('__') == 0:
                        t = t + '\"' + c + '\",'
                t = t + '\"\"\n'
            return t
        elif output=='rss':
            t=''
            if self.autoheader:
                t = t + '<?xml version=\"1.0\" encoding="utf-8"?>'
            t = t + '<rss version=\"2.0\"><channel>'
            t = t + '<title>' + escape(self.rss_title) + '</title>'
            t = t + '<description>' + escape(self.rss_description) + '</description>'
            t = t + '<author>' + escape(self.rss_author) + '</author>'
            return t
        elif output=='json':
            itemname = self.parent
            if itemname is not None and self.mode == 'table':
                return '    {\"' + itemname + '\" : [\n'
            else:
                return '    {\"item\" : [\n'
        elif output=='simple':
            return''
        else:
            t=''
            if self.autoheader:
                t = t + '<head><title>' + self.html_title + '</title></head>'
                t = t + self.html_headers
                t = t + '<h1>' + self.html_head + '</h1>'
                t = t + self.html_intro
            t = t + '<table>'
            if type(obj) is types.ListType:
                if len(obj) > 0:
                    r = obj[0]
                    cols = dir(r)
                    t = t + '<tr>'
                    for c in cols:
                        if c.count('__') == 0:
                            t = t + '<td>' + c + '</td>'
                    t = t + '</tr>'
            elif type(obj) is dict:
                cols = obj.keys()
                t = t + '<tr>'
                for c in cols:
                    if c.count('__') == 0:
                        t = t + '<td>' + c + '</td>'
                t = t + '</tr>'
            elif type(obj) is types.InstanceType:
                cols = dir(obj)
                t = t + '<tr>'
                for c in cols:
                    if c.count('__') == 0:
                        t = t + '<td>' + c + '</td>'
                t = t + '</tr>'
            return t
    def makeFooter(self,obj,output):
        """
        Generates a footer for the output string (e.g. closing XML tags, JSON parentheses, etc).
        """
        if output=='xml':
            if self.mode == 'table':
                return '</' + self.parent + '>'
            else:
                return '</record>'
        elif output=='xliff':
            return '</body></file></xliff>'
        elif output=='po':
            return ''
        elif output=='text':
            return ''
        elif output=='rss':
            t = '</channel></rss>'
            return t
        elif output=='json':
            return '    {}]\n}'
        elif output=='simple':
            return ''
        else:
            return '</table>'
    def makeRow(self,obj,output):
        """
        Renders a row from a recordset. Expects the parameters obj and output
        where obj = a instance or dict object, and output is the desired output
        format. This method is called automatically within pickleItem() and
        pickleTable() and is not called directly by user applications.
        """
        if output=='xml':
            return self.makeXML(obj)
        elif output=='rss':
            return self.makeRSS(obj)
        elif output=='xliff':
            return self.makeXLIFF(obj)
        elif output=='json':
            return self.makeJSON(obj) + ','
        elif output=='text':
            return self.makeCSV(obj)
        elif output=='csv':
            return self.makeCSV(obj)
        elif output=='po':
            return self.makePO(obj)
        elif output=='simple':
            return self.makeSimple(obj)
        else:
            return self.makeHTML(obj)
    def makeXML(self,item):
        """ Outputs a row of XML. Called automatically within makeRow()"""
        x = ''
        if type(item) is types.InstanceType:
            itemname = item.__class__.__name__
            colnames = dir(item)
            x = x + '<' + itemname + '>'
            if len(colnames) > 0:
                for c in colnames:
                    if getattr(item, c) is not None and c.count('__') == 0:
                        x = x + '<' + c + '>' + escape(self.convert(getattr(item, c))) + '</' + c + '>'
            x = x + '</' + itemname + '>'
        elif type(item) is dict:
            itemname = item.__class__.__name__
            colnames = item.keys()
            if len(colnames) > 0:
                for c in colnames:
                    if item[c] is not None and c.count('__') == 0:
                        x = x + '<' + c + '>' + escape(self.convert(item[c])) + '</' + c + '>'
        x = string.replace(x, '&amp;amp;','&amp;')
        return x
    def makeXLIFF(self,item):
        "Outputs an XMLIFF record. Called automatically within makeRow()"""
        x = ''
        if type(item) is types.InstanceType:
            colnames = dir(item)
            if hasattr(item,'st') and hasattr(item,'tt') and hasattr(item,'sl') and hasattr(item,'tl'):
                x = x + '<trans-unit'
                if hasattr(item,'refid'):
                    x = x + ' id=\"' + self.convert(getattr(item,'refid')) + '\"'
                else:
                    x = x + ' id=\"' + self.convert(getattr(item,'st')) + '\"'
                if hasattr(item,'token'):
                    x = x + ' resname=\"' + self.convert(getattr(item,'token')) + '\"'
                x = x + '>\n'
                x = x + '<source xml:lang=\"' + getattr(item,'sl') + '\">' + self.convert(getattr(item,'st')) + '</source>\n'
                x = x + '<target xml:lang=\"' + getattr(item,'tl') + '\">' + self.convert(getattr(item,'tt')) + '</target>\n'
                if hasattr(item,'username'):
                    x = x + '<username>' + self.convert(getattr(item,'username')) + '</username>\n'
                if hasattr(item,'remote_addr'):
                    x = x + '<remote_addr>' + self.convert(getattr(item,'remote_addr')) + '</remote_addr>\n'
                x = x + '</trans-unit>\n'
        return x
    def makePO(self,item):
        """Outputs an entry for a PO file. Called automatically within makeRow()"""
        x = ''
        if type(item) is types.InstanceType:
            itemname = item.__class__.__name__
            if hasattr(item,self.po_source) and hasattr(item,self.po_target):
                x = x + '\n'
                if hasattr(item,'refid'):
                    x = x + '#. refid/' + self.convert(getattr(item,'refid')) + '\n'
                if hasattr(item,'token'):
                    x = x + '#. token/' + self.convert(getattr(item,'token')) + '\n'
                if hasattr(item,'username'):
                    x = x + '#. author/' + self.convert(getattr(item,'username')) + '\n'
                if hasattr(item,'remote_addr'):
                    x = x + '#. remote_addr/' + self.convert(getattr(item, 'remote_addr')) +'\n'
                if hasattr(item, 'avgscore'):
                    x = x + '#. avgscore/' + self.convert(getattr(item, 'avgscore')) + '\n'
                if hasattr(item, 'scores'):
                    x = x + '#. scores/' + self.convert(getattr(item, 'scores')) + '\n'
                x = x + 'msgid \"' + self.convert(getattr(item,self.po_source)) + '\"\n'
                x = x + 'msgstr \"' + self.convert(getattr(item,self.po_target)) + '\"\n'
        return x
    def makeSimple(self,item):
        """
        Outputs a row of plain text, one field per line. Called automatically within
        makeRow()
        """
        x = ''
        if type(item) is types.InstanceType:
            if hasattr(item,self.simple_column):
                x = x + self.convert(getattr(item,self.simple_column)) + '\n'
        return x
    def makeJSON(self,item):
        """
        This method generates a JSON object when the output mode is set to json. Called
        automatically within makeRow()
        """
        x = '{ '
        if type(item) is types.InstanceType:
            itemname = item.__class__.__name__
            colnames = dir(item)
            if len(colnames) > 0:
                x = x + '\"' + itemname + '\" : {\n'
                count = len(colnames)
                ctr=0
                for c in colnames:
                    ctr = ctr+1
                    if getattr(item, c) is not None and c.count('__') == 0:
                        txt = getattr(item, c)
                        if type(txt) is str:
                            txt = string.replace(txt, '\"', '%22')
                            txt = string.replace(txt, '\n', '')
                            txt = string.replace(txt, '\r', '')
                        x = x + '   \"' + c + '\" : \"' + self.convert(txt) + '\",\n'
                    if ctr==count:
                        x = x + '   \"ver\" : \"1.0\"\n'
                x = x + '   }\n'
        x = x + ' }'
        return x
    def makeRSS(self,item):
        """
        This method generates an RSS <item> field when the output mode is set to rss.
        """
        x = ''
        if type(item) is types.InstanceType:
            itemname = 'item'
            x = x + '<item>'
            if hasattr(item,self.rss_item_title):
                x = x + '<title>' + escape(self.convert(getattr(item,self.rss_item_title))) + '</title>'
            if hasattr(item,self.rss_item_author):
                x = x + '<author>' + escape(self.convert(getattr(item,self.rss_item_author))) + '</author>'
            if hasattr(item,self.rss_item_description):
                x = x + '<description>' + escape(self.convert(getattr(item,self.rss_item_description))) + '</description>'
            if hasattr(item,self.rss_item_link):
                x = x + '<link>' + escape(self.convert(getattr(item,self.rss_item_link))) + '</link>'
            if hasattr(item,self.rss_item_guid):
                x = x + '<guid>' + escape(self.convert(getattr(item,self.rss_item_guid))) + '</guid>'
            x = x + '</item>'
        x = string.replace(x,'&amp;amp;','&amp;')
        return x
    def makeCSV(self,item):
        """
        This method generates a row of CSV (comma separated value) text when the mode is set to text
        """
        x = ''
        if type(item) is types.InstanceType:
            itemname = item.__class__.__name__
            colnames = dir(item)
            if len(colnames) > 0:
                ctr=0
                count = len(colnames)
                for c in colnames:
                    ctr = ctr + 1
                    if getattr(item, c) is not None and c.count('__') == 0:
                        x = x + '\"' + self.convert(getattr(item,c)) + '\"'
                        if ctr < count:
                            x = x + ','
                    elif c.count('__') == 0:
                        x = x + '\"\",'
                x = x + '\n'
        elif type(item) is dict:
            itemname = item.__class__.__name__
            colnames = item.keys()
            if len(colnames) > 0:
                ctr=0
                count = len(colnames)
                for c in colnames:
                    ctr = ctr + 1
                    if item[c] is not None and string.count(item[c],'__') == 0:
                        x = x + '\"' + self.convert(item[c]) + '\"'
                        if ctr < count:
                            x = x + ','
                    elif c.count('__') == 0:
                        x = x + '\"\",'
                x = x + '\n'
        return x
    def makeHTML(self,item):
        """
        This method generates a row for an HTML table, and is called when the output mode is set to html
        """
        x = ''
        if type(item) is types.InstanceType:
            itemname = item.__class__.__name__
            colnames = dir(item)
            if len(colnames) > 0:
                x = x + '<tr>'
                for c in colnames:
                    if getattr(item, c) is not None and c.count('__') == 0:
                        x = x + '<td>' + self.convert(getattr(item,c)) + '</td>'
                x = x + '</tr>'
        elif type(item) is dict:
            itemname = item.__class__.__name__
            colnames = item.keys()
            if len(colnames) > 0:
                x = x + '<tr>'
                for c in colnames:
                    if item[c] is not None and string.count(item[c],'__') == 0:
                        x = x + '<td>' + self.convert(item[c]) + '</td>'
                x = x + '</tr>'
        return x
    def convert(self,item, mode=''):
        """
        This method converts an item to Unicode/UTF-8 compatible text. It takes care of converting most
        common data types to a string format, for inclusion in the various output formats supported by
        DeepPickle().

        Currently supported data types are:

        int
        boolean
        long
        float
        string
        unicode
        tuple
        list
        dict/dictionary
        instance

        Because this module is designed primarily to convert row/column type recordsets into text formats
        it works best with integer, boolean, long, float, string and unicode fields. It will convert
        other data types to string formats but may not yield good results. This method is called
        automatically, although it can be used as a utility method to check and convert non-string
        data types to a string format.
        
        """
        if item is None:
            item = ''
        if type(item) is types.IntType:
            item = str(item)
        elif type(item) is types.BooleanType:
            if item:
                item = 't'
            else:
                item = 'f'
        elif type(item) is types.LongType:
            item = str(item)
        elif type(item) is types.FloatType:
            item = str(item)
        elif type(item) is types.StringType:
            item = item
        elif type(item) is types.UnicodeType:
            item = item.encode('UTF-8')
        elif type(item) is types.TupleType:
            item = str(item)
        elif type(item) is types.ListType:
            item = str(item)
        elif type(item) is types.DictType:
            item = str(item)
        elif type(item) is types.DictionaryType:
            item = str(item)
        elif type(item) is types.InstanceType:
            pass
        else:
            item = ''
        return item
