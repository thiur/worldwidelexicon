<?php

	/**
	 *  The World Wide Lexicon Proxy Configuration File
	 *  =================================================
	 */


	// Set the error-reporting preferences here.
	//ini_set('display_errors', 0); 
	//error_reporting(0);


	// These are self explanatory, where are you setting up the proxy?
	define("PROXY_IP", $_SERVER["SERVER_ADDR"]);
	define("PROXY_URL", "http://".$_SERVER["SERVER_ADDR"]."/");
	define("PROXY_HOME_PATH", "/var/www/html/");
	
	
	// If you enable error-logging, where will those files live?
	// Create a directory and set it writable by the server.
	// The options for logging are: NONE or ERRORS_ONLY or ALL
	define("LOG_PATH", "/var/www/html/logs/");
	define("LOG_MESSAGES", "ALL");
	

	// Memcache : Enable memcache below and set the address and ttl (in seconds).
	define("MEMCACHE_ENABLED", true);
	define("MEMCACHE_ADDRESS", "domU-12-31-38-00-9D-46.compute-1.internal");
	define("MEMCACHE_PORT", 11211);
	define("MEMCACHE_TTL", 86400);
	
	
	// If your server doesn't have Memcache installed, then install it.
	// As a last resort, give file cacheing a try by enabling hit here.
	// CACHE_TTL is defined in seconds.
	define("FILE_CACHE_ENABLED", false);
	define("CACHE_PATH", "/var/www/html/cache/");
	define("CACHE_TTL", 3600);


	// ALLOWED SITES | DISALLOWED SITES.  
	// Separate domains with a single space.
	define("PROXY_WHITELIST", "oreilly.com economist.com nytimes.com foreignpolicy.com atlasobscura.com briansbook.org techsoup.org fleethecube.com worldwidelexicon.org");
	
	define("PROXY_BLACKLIST", "marx.worldwidelexicon.org");

?>