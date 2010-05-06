
******************************************************************************************
*
*	Proxy Server for the World Wide Lexicon
*
*	@author 		Cesar Gonzalez (icesar@gmail.com)
*	@version 		1.0
*	@license		BSD
*	
******************************************************************************************


DESCRIPTION
==========================================================================================
This web application implements a transparent proxy interface to the World Wide Lexicon (WWL) API, which an online translation memory. The idea behind the WWL is that ...

The idea behind the proxy is to give the webmaster a simple interface to implement translations of their website into any desired language, simply by pointing a language code subdomain (eg. http://es.mywebsite.com/) at a server where this proxy code is running.  There are several distinct advantages to using this method to translate your website:

+ Simplicity. Install the proxy (or use ours), change one A-record, tweak some setting, and presto!

+ Standard URL structure. For any page on your site, you know exactly how to access that page in any available language.

+ SEO & indexability.  Many translation tools are javascript-based, which means the search engines will not index your content in other languages.  Using the WWL proxy, you have the option of making your content searchable in other languages.



REQUIREMENTS
==========================================================================================
+ PHP 5  						(Tested on PHP 5.1.6)
+ cURL   						(libcurl/7.15.5)
+ Memcache *recommended*		(v 2.2.3)



INSTALLATION (PROXY SERVER)
==========================================================================================
+ Unzip the archive and FTP all the files into the base web directory on your server.
+ Open includes/config.php in your favorite editor and:
	+ Define your server IP, home directory path, and log path
	+ If you have memcache, define the address, port, etc.
	+ Define which domains to translate in the whitelist / blacklist section
+ Create /logs and /cache directories (if enabled) and set them editable by the server.



SETUP (WEBSITE TO TRANSLATE)
==========================================================================================

+ Go to your domain registrar and create an A-record pointing to the IP address of the Proxy:
	+ Set up one A-record using a wildcard (eg. *.mywebsite.com)
	+ OR set up multiple A-records, each with a 2-letter language code (ISO 639-1) as a subdomain	
+ That's it!  Now you should be able to access http://**.mywebsite.com/ and see it another language


+ You can fine-tune setting using META tags:
  Usage:  <meta name="{setting_name}" content="{setting_value}" />

		allow_machine  (y/n)
		allow_anonymous  (y/n)
		allow_edit  (y/n)
		require_professional (y/n)
		languages  (string, comma-separated list)
		machine_translation_languages  (string, comma-separated list)
		community_translation_languages  (string, comma-separated list)
		professional_translation_languages  (string, comma-separated list)
		lsp  (string)
		lspusername (string)
		lsppw  (string -- more secure way?)
		
		Examples:
		<meta name="languages" content="es, fr, br, ar, de" />
		<meta name="allow_edit" content="n" />

+ You can fine-tune whether a give section of the page can be translated / edited using CSS:
  Usage: <{tag} class="{setting}"> </{tag}

		allow_edit
		disallow_edit
		
		Examples:
		<div class="header disallow_edit"> . . . . </div>
		<p id="callout" class="highlight allow_edit"> . . . . </div>


+ You can insert a language-switching widget using a comment tag like so:

		<h3>Switch Languages</h3>
		<!-- wwl_language_selector -->
		<br />



DEVELOPER GUIDE
==========================================================================================


/.htaccess							- rewrite rules send all requests to index.php
/index.php							- script starts here - loads all libraries, determines languages, instantiates the proxy.
/readme.txt							- this file!
/robots.txt							- decide whether to allow search engines to index proxied sites in other languages.

/includes/config.php				- main settings file, fill this out when installing the proxy.
/includes/functions.php				- holds the simple, app-wide error logging function.

/libraries/curl.php					- cURL is used extensively, to get HTML of site to be translated, and to access the WWL, etc.
/libraries/googletranslate.php		- google's machine translation API is accessed directly, instead of thru the WWL.
/libraries/languagehelper.php		- language detection, language code definitions, etc.
/libraries/requestvalidator.php		- uses white / black list and referer sniffing to decide whether to fill translation requests.
/libraries/services_json.php		- google API returns JSON, this makes it easy to work with it.
/libraries/url.php					- app works extensively with URLs, this class encapsulates them.
/libraries/wwl.php					- this class encapsulates translations and submissions to the WWL memory
/libraries/wwlproxy.php				- this class extends the WWL class and implements the bulk of the proxy functionality
/libraries/wwlsettings.php			- encapsulates the proxy settings available to client site through meta tags, comment tags, and CSS classes

/wwlassets/*						- this world-readable folder holds the CSS / JS added to the client site in order to enable user-edits, etc.

