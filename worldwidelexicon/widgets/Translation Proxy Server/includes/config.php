<?php

	/**
	 *  The World Wide Lexicon Proxy Configuration File
	 *  =================================================
	 *  Configure the basics.
	 *
	 */

	define("PROXY_IP", "72.51.37.41");
	define("PROXY_URL", "http://72.51.37.41/");
	define("PROXY_HOME_PATH", "/var/www/html/");
	
	define("LOG_PATH", "/var/www/html/logs/");
	define("LOG_MESSAGES", "ALL");						// NONE or ERRORS_ONLY or ALL
	
	define("FILE_CACHE_ENABLED", false);
	define("CACHE_PATH", "/var/www/html/cache/");
	define("CACHE_TTL", 3600);							// 86400 is 24 hours


	/* ALLOWED SITES:  This is how we're limiting access for the time being. Please separate domains with a single space. */
	define("PROXY_WHITELIST", "oreilly.com economist.com nytimes.com foreignpolicy.com atlasobscura.com briansbook.org techsoup.org fleethecube.com");
	
?>