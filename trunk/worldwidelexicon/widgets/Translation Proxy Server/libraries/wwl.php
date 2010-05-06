<?php
/**
 *  WWLphp: a simple PHP wrapper library for the World Wide Lexicon 
 *  This library enables PHP based applications to easily interact with the servers of the World Wide Lexicon.
 *
 *	@package		wwlphp
 *  @author 		Cesar Gonzalez (icesar@gmail.com)
 *  @version 		1.0
 *  @license		BSD
 *
 *
 *	NOTES:
 *	============
 *	+ Make sure to set this at the top of any scripts using WWLphp.
 *		mb_internal_encoding('UTF-8');
 *		mb_http_output('UTF-8');
 *
 */


/**
 *	This class encapsulates the functionality of the WWL (the World Wide Lexicon) for automatically
 *	translating content on the web between languages.
 *	@package		wwlphp
 */
class Wwl {
    
 	public $targetLanguage = "";
	public $sourceLanguage =  "";
	
	var $wwl_servers = array('www.worldwidelexicon.org');
	var $secure_wwl_servers = array('worldwidelexicon.appspot.com');

	var $memcache_enabled = true;
	var $memcache_address = 'localhost';
	var $memcache_port = 11211;
	var $memcache_ttl = 86400;

	// For gettext() support
	var $gettext_app_domain = "mydomain";
	var $gettext_base_path = "/www/htdocs/myapp.com/locale";
	
	var $cacher = null; // assign an object implementing "get" and "set" methods to use external caching
	
	function __construct($sl = '', $tl = '') {

		$this->targetLanguage = $tl;
		$this->sourceLanguage = $sl;
		
		// Get setting from the configuation file
		$this->memcache_enabled 	= MEMCACHE_ENABLED;
		$this->memcache_address 	= MEMCACHE_ADDRESS;
		$this->memcache_port 		= MEMCACHE_PORT;
		$this->memcache_ttl 		= MEMCACHE_TTL;

        log_message('debug', "WWL class initialized - source: $sl, target: $tl");
	}			
		
	function wwl($sl = '', $tl = '') {
		$this->__construct($sl, $tl);		
	}
	
	/**
	 *	Return the gettext() translation of a given string for a given pair of languages.
	 *
	 *  @param string $st string to be translated
	 */
	function gt( $st ) {
		
		// Make sure all arguments are not empty strings.
		if ( function_exists('gettext') && 
			 strlen($this->sourceLanguage) > 0 && 
			 strlen($this->targetLanguage) > 0 && 
			 strlen($st) > 0 && 
			 strlen( $this->gettext_base_path ) > 0 ) 
		{		
			// Set the environment for gettext() and see if there is a translation there.
			bindtextdomain( $this->gettext_app_domain, $this->gettext_base_path . '/' . $this->targetLanguage );
			textdomain( $this->gettext_app_domain );
			$tt = gettext( $st );
			
			if ( $tt != $st ) {
				
				// If we have a gettext() translation, store it and return it.
				$this->setcache( $st, $tt );
				return $tt;
			}
		}
		return '';
	}


	/**
	 *	Use this to authenticate a username and password pair, or session key.  Returns an MD5
	 *	hash key (session ID) if successful, an empty string if not.
	 *
	 *	@param string $username
	 *	@param string $password
	 *	@param string $session
	 *  @return string MD5 has key or empty string if fail.
	 */
	function auth( $username='', $password='', $session='' ) {
	
		if ( strlen($username) > 0 && strlen($password) > 0 || strlen($session) > 0 ) {
			
			$url = $this->server(true) . "/users/auth";
			$request = array();

			if ( strlen( $session ) > 0 ) {			
				$request['session'] = $session;
			} else {
				$request['username'] = $username;
				$request['pw'] = $password;
			}
			
			$response = $this->sendRequest($url, $request);
			return $reponse;
		} else {
			return '';
		}
	}


	/**
	 *	Create a new user account.  Returns True or False, and if successful, sends a welcome
	 *	email to the user asking to click on a link to validate their account.
	 *
	 *	@param string $username WWL username, required
	 *	@param string $pw WWL password, required
	 *	@param string $email the user's email address, required
	 *	@param string $firstname
	 *	@param string $lastname
	 *	@param string $city
	 *	@param string $state
	 *	@param string $country
	 *	@param string $description
	 *	@return boolean
	 */
	function newuser( $username, $pw, $email, $firstname='', $lastname='', $city='', $state='', $country='', $description='' ) {
	
		// There is a 6 character minimum on the username and  8 characters on the password
		if ( strlen($username) > 5 && strlen($pw) > 7 ) {
			
			// Use the secure server for new user submit
			$url = $this->server(true) . "/users/new";
			
			// Set up the submit
			$request['username'] = $username;
			$request['pw'] = $pw;
			$request['email'] = $email;
			$request['firstname'] = $firstname;
			$request['lastname'] = $lastname;
			$request['city'] = $city;
			$request['state'] = $state;
			$request['country'] = $country;
			$request['description'] = $description;
		
			$response = $this->sendRequest($url, $request);
			return ($response == 'ok');	
		} else {
			// Username or password is too short.
			return false;
		}
	}
	
	
	/**
	 *	Gets a parameter corresponding to a user. Expects the username and param name.
	 *	Returns a string with the stored param value.
	 *
	 *	@param string $username
	 *	@param string $parm
	 *	@return string
	 *
	 */
	function getparm( $username, $parm ) {
		
		$url = $this->server() . "/users/get";
		$request['username'] = $username;
		$request['parm'] = $parm;
		
		$response = $this->sendRequest($url, $request);
		return $response;
	}
	
	
	/**
	 *	Set a parameter for a given user to a given value.
	 *
	 *	@param string $username
	 *	@param string $pw
	 *	@param string $parm
	 *	@param string $value
	 *	@return boolean
	 *
	 */
	function setparm() {
		
		$url = $this->server(true) . "/users/set";
		$request['username'] = $username;
		$request['pw'] = $pw;
		$request['parm'] = $parm;
		$request['value'] = $value;
		
		$response = $this->sendRequest($url, $request);
		return ($response == 'ok');
	}
	
	
	/**
	 *	Returns the WWL server corresponding to $idx, which is secure if the $secure flag is set.
	 *  Both $secure and $idx have defaults, so the function can be called without arguments.
	 *
	 *	@param boolean $secure
	 *	@param integer $idx
	 *  @return string
	 */
	function server ( $secure=false, $idx=0 ) {

		try {
			if ( $secure ) { 
				$url = 'https://' . $this->secure_wwl_servers[$idx]; 
			} else { 
				$url = 'http://' . $this->wwl_servers[$idx]; 
			}

		} catch (Exception $e) {
			$url = '';
		}
		
		return $url;
	}


	/**
	 *  Checks if the requested translation is stored in the local memcache and if so return it, otherwise
	 *	return an empty string.
	 *
	 *  @param string $st string to be translated
	 *  @return string
	 */
	function getcache( $st ) {
		
		// If memcache is enabled, make sure all arguments are not empty strings.
		if ( class_exists("Memcache") && $this->memcache_enabled && strlen($this->memcache_address) > 0 && strlen($this->sourceLanguage) > 0 && 
			strlen($this->targetLanguage) > 0 && strlen($st) > 0 ) {
				
			$memcache = new Memcache;
			if ( $memcache->connect( $this->memcache_address, $this->memcache_port) ) {

				// Check if there is a memcached result, if so return it.
				$result = $memcache->get( MD5($this->sourceLanguage . $this->targetLanguage . $st) );				
				return $result;
			}
			
		}
		return '';
	}


	/**
	 *	Add a translated text to the local memcache.  Return true on success false on failure.
	 *
	 *  @param string $st string to be translated
	 *  @param string $tt string holding translation of $st
	 */
	function setcache( $st, $tt ) {

		// If memcache is enabled, also make sure all arguments are not empty strings.
		if (class_exists("Memcache") && $this->memcache_enabled && strlen($this->memcache_address) > 0 && strlen($this->sourceLanguage) > 0 && 
			strlen($this->targetLanguage) > 0 && strlen($st) > 0 && strlen($tt) > 0 ) {
		
			$memcache = new Memcache;
			if ( $memcache->connect( $this->memcache_address, $this->memcache_port) ) {
				if ( $memcache->set( MD5($this->sourceLanguage . $this->targetLanguage . $st), $tt, false, $this->memcache_ttl) ) { 
					return true;
				} 
			}
		}
		return false;
	}
	
	function get_ext_cache ( $st ) {
		if (!$st || !$this->cacher || !method_exists($this->cacher, "get")) {
			return "";
		}
		return $this->cacher->get(md5($this->sourceLanguage . $this->targetLanguage . $st));
	}
	
	function set_ext_cache ( $st, $tt) {
		if (!$st || !$this->cacher || !method_exists($this->cacher, "set")) {
			return false;
		}
		return $this->cacher->set(md5($this->sourceLanguage . $this->targetLanguage . $st), $tt);
	}
	
	/**
	 *	This function is used to get the best available translation from a WWL server.
	 *	
	 *  @param string $st string to be translated
	 *  @param string $domain filter results to domain=foo.com
	 *  @param string $allow_machine y/n to allow or hide machine translations
	 *  @param string $allow_anonymous y/n to allow or hide translations from unregistered users
	 *  @param string $require_professional y/n to require professional translations
	 *  @param string $ip_filter limit results to submissions from trusted IP address or pattern
	 *  @param string $lsp language service provider name, if pro translations are desired
	 *  @param string $lspusername username with LSP
	 *  @param string $lsppw password or API key for LSP
	 *  @param string $mtengine force selection of specific machine translation engine (eg. google, apertium, moses, worldlingo)
	 */
	function get($st, $domain='', $allow_machine='y', $allow_anonymous='y', $require_professional='n', 
				  $ip_filter='', $lsp='', $lspusername='', $lspw='', $mtengine='' ) {
	
		// Make sure vital arguments are not empty strings.
		if ( strlen($this->sourceLanguage) > 0 && strlen($this->targetLanguage) > 0 && strlen($st) > 0 ) {
		
			// First, try to get a cached translation (returns empty if not running)
			$tt = $this->getcache($st);			
			if ( strlen( $tt ) > 0 ) { return $tt; }
			
			$tt = $this->get_ext_cache($st);			
			if ( strlen( $tt ) > 0 ) { return $tt; }
			
			// Next, check if gettext() knows the translation (returns empty if not present)
			$tt = $this->gt($st);
			if ( strlen( $tt ) > 0 ) { return $tt; }
			
			// No on both counts? Then let's request a translation from the WWL server
			$request['sl'] = $this->sourceLanguage;
			$request['tl'] = $this->targetLanguage;
			$request['st'] = $st;
			$request['domain'] = $domain;
			$request['allow_machine'] = $allow_machine;
			$request['allow_anonymous'] = $allow_anonymous;
			$request['require_professional'] = $require_professional;
			$request['ip'] = $ip_filter;
			$request['lsp'] = $lsp;
			$request['lspusername'] = $lspusername;
			$request['lsppw'] = $lsppw;
			$request['mtengine'] = $mtengine;
			$request['output'] = 'text';
			$request['limit'] = $limit;
			
			// Build the URL for the REST query
			$url = $this->server() . "/t?" . http_build_query($request);
			$response = $this->sendRequest($url, $request);	
			if (strlen( $response ) > 0) {
				$this->setcache($st, $response);
				$this->set_ext_cache($st, $response);
			}
			return $response;
		}
		return ''; 
	}



	/**
	 *	This function is used to get multiple translation from the WWL server in parallel.
	 *	
	 *  @param array  $starray array of strings to be translated
	 *  @param string $domain filter results to domain=foo.com
	 *  @param string $allow_machine y/n to allow or hide machine translations
	 *  @param string $allow_anonymous y/n to allow or hide translations from unregistered users
	 *  @param string $require_professional y/n to require professional translations
	 *  @param string $ip_filter limit results to submissions from trusted IP address or pattern
	 *  @param string $lsp language service provider name, if pro translations are desired
	 *  @param string $lspusername username with LSP
	 *  @param string $lsppw password or API key for LSP
	 *  @param string $mtengine force selection of specific machine translation engine (eg. google, apertium, moses, worldlingo)
	 *
	 *  @return array an associate array with the md5 of the source string as key and the translation as value.
	 */
	function multiget( $starray, $domain='', $allow_machine='y', $allow_anonymous='y', $require_professional='n', $ip_filter='', $lsp='', $lspusername='', $lsppw='', $mtengine='' ) {
		
		// Make sure vital arguments are not empty strings.
		if ( strlen($this->sourceLanguage) == 0 || strlen($this->targetLanguage) == 0 || sizeof($starray) == 0 ) {
			return array(); 
		}
			
		// Initialize two arrays -- one for translation results, and one for uncached snippets (our translation_queue).
		$translation_results = array();
		$translation_queue = array();
		
		// For each source text, first of all see if we can retrieve from the many cache options.
		foreach( $starray as $st ) {
			$tt1 = $this->getcache( $st );
			$tt2 = $this->gt( $st );
			$tt3 = $this->get_ext_cache( $st );
			
			// First, try to get the cached translation (returns empty if nothing is found)
			if ( $tt1 != "" ) { $translation_results[md5($st)] = $tt1; }

			// Next check if gettext() knows how to translate this.
			elseif ( $tt2 != "" ) { $translation_results[md5($st)] = $tt2; }
			
			// Next see if there is an entry in the external cache (eg. File Cache)
			elseif ( $tt3 != "" ) { $translation_results[md5($st)] = $tt3; }

			// Lastly, if we didn't find a cached translation, add it to our pending queue
			else { $translation_queue[] = $st; }
			
		}
		
		log_message("debug", "Size: " . sizeof($translation_results) . " snippets found in caches, " . sizeof($translation_queue) . " remain in queue.");
		
		
		/* Here we are left will all un-cached snippets in translation_queue[].  These are handled like so:
		 *    1. Get any human translations from the WWL.
		 *    2. If mtengine is set & is NOT google, request MTs through WWL.
		 *    3. Else, request MTs directly from Google, to save some bandwidth.
		 */
		
		// Let's request a translation for each none-cached source snippet.
		$request['sl'] = $this->sourceLanguage;
		$request['tl'] = $this->targetLanguage;
		$request['domain'] = $domain;
		$request['allow_anonymous'] = $allow_anonymous;
		$request['require_professional'] = $require_professional;
		$request['ip'] = $ip_filter;
		$request['lsp'] = $lsp;
		$request['lspusername'] = $lspusername;
		$request['lsppw'] = $lsppw;
		$request['mtengine'] = $mtengine;
		$request['output'] = 'text';

		// First, get only human translations from the WWL
		$request['allow_machine'] = 'n';
		log_message("debug", "Size: " . sizeof($translation_queue) . " snippets sent to WWL, no machine translations.");
		$this->_getMultiWWLTranslations($translation_queue, $translation_results, $request);
		log_message("debug", "Size: " . sizeof($translation_results) . " snippets returned by WWL.");

		// Then get machine translations through WWL (for non-google MT) or directly from Google
		if (sizeof($translation_queue) > 0 && $allow_machine == 'y' && $mtengine != "google" && $mtengine != "") 
		{
			$request['allow_machine'] = 'y';
			log_message("debug", "Size: " . sizeof($translation_queue) . " snippets sent to WWL, with machine translations allowed.");
			$this->_getMultiWWLTranslations($translation_queue, $translation_results, $request);
			log_message("debug", "Size: " . sizeof($translation_results) . " snippets returned (in 2 steps) by WWL.");
		}
		elseif ( sizeof($translation_queue) > 0 && $allow_machine == 'y' && ($mtengine == "google" || $mtengine == ""))
		{
			log_message("debug", "Size: " . sizeof($translation_queue) . " snippets sent to Google.");
			$this->_getMultiGoogleTranslations($translation_queue, $translation_results);
		}

		return $translation_results;
	}

	/* Helper function carries out multiget access to the WWL.  It manipulates two arrays passed in by reference, the queue and the results. */
	function _getMultiWWLTranslations(&$translation_queue, &$translation_results, $request) {

		// Let's set up multiple CURL handles and an array index, and the URL
		$multi_handle = curl_multi_init();
		$curl_handles = array();
		$remaining_translation_queue = array();
		$url = $this->server() . "/t";
		$i = 0;

		foreach( $translation_queue as $st ) {
			
			// ONLY after checking the cache, get the translation from WWL
			$request['st'] = $st;
			$curl_handles[$i] = curl_init();

			curl_setopt($curl_handles[$i], CURLOPT_URL, $url);									// where are we requesting?
			curl_setopt($curl_handles[$i], CURLOPT_HEADER, false); 					 			// don't output the returned HTTP headers
			curl_setopt($curl_handles[$i], CURLOPT_RETURNTRANSFER, true);						// return output as string
		 	curl_setopt($curl_handles[$i], CURLOPT_POST, true);									// use a POST request
			curl_setopt($curl_handles[$i], CURLOPT_POSTFIELDS, http_build_query($request));		// variable to post
	        curl_setopt($curl_handles[$i], CURLOPT_TIMEOUT, 90);								// set the timeout for each individual handle @ 90 seconds ** not working.

			// Now add this particular handle to the multi_handle.
			curl_multi_add_handle( $multi_handle, $curl_handles[$i] );
		
			// And increment our index.
			$i++;
		}

		
		// Execute the handles in parallel, get the translated texts
		$running = null;
		do { 
			curl_multi_exec( $multi_handle, $running ); // *** timing out sometimes...
		} while( $running > 0 );
		
		// Now, get the results for each executed cURL call and close the handles
		$j = 0;
		
		// Add to the the associative array with md5(source) -> translation.
		foreach( $translation_queue as $st ) {

			$tt = curl_multi_getcontent( $curl_handles[$j] );

			// Save non-empty translations, and update the different caches
			if (strlen( $tt ) > 0) {
				$translation_results[md5($st)] = $tt;
				$this->setcache($st, $tt);
				$this->set_ext_cache($st, $tt);
			} else {
				$remaining_translation_queue[] = $st;
			}

			// Remove the cURL handle
			curl_multi_remove_handle( $multi_handle, $curl_handles[$j] );
			
			// And increment our index.
			$j++;
		}

		//print_r("Total time: " . curl_getinfo($curl, CURLINFO_TOTAL_TIME) . "<br><br>");
		
		// Any results have been added to the translation_results array.  Let's close the curl handlers and update the queue.
		curl_multi_close( $multi_handle );
		$translation_queue = $remaining_translation_queue;

	}


	/* This helper function carries out multiget translations from Google. 
	 * It manipulates the results array which is passed in by reference. */
	function _getMultiGoogleTranslations(&$translation_queue, &$translation_results) {
		
		$google = new GoogleTranslate($this->sourceLanguage, $this->targetLanguage, null);
		$google_translations = $google->getmultiple($translation_queue);
		$i = 0;

		log_message("debug", "Size: " . sizeof($google_translations) . " snippets returned by Google.");
		
		// Add results to the the associative array with md5(source) -> translation.
		foreach( $translation_queue as $st ) {

			$tt = array_key_exists($i, $google_translations) ? $google_translations[$i] : "";

			// Save non-empty translations, and update the different caches
			if (strlen( $tt ) > 0) {
				$translation_results[md5($st)] = $tt;
				$this->setcache($st, $tt);
				$this->set_ext_cache($st, $tt);
			}
			
			// And increment our index.
			$i++;
		}
	}



	/**
	 *  Submit a translation to the WWL server.
	 *
	 *  @param string $sl source language (ISO code)
	 *  @param string $tl target language (ISO code)
	 *  @param string $st string to be translated (UTF-8)
	 *  @param string $tt translation of $st to submit (UTF-8)
	 *  @param string $domain site domain or API key
	 *  @param string $url parent URL of source document (use full permalink)
	 *  @param string $username WWL or remote username
	 *  @param string $pw WWL or remote password
	 *	@return bool
	 */
	function submit($st, $tt, $domain='', $url='', $username='', $pw='' ) {
		
		// Save this translation to the local memcache
		$this->setcache($st, $tt);
		$this->set_ext_cache($st, $tt);
		
		// And now submit the translation to the WWL server
		$request['sl'] = $this->sourceLanguage;
		$request['tl'] = $this->targetLanguage;
		$request['st'] = $st;
		$request['tt'] = $tt;
		$request['domain'] = $domain;
		$request['url'] = $url;
		$request['username'] = $username;
		$request['pw'] = $pw;
		
		// Build the URL for the REST submission
		$url = $this->server() . "/submit";
		$response = $this->sendRequest($url, $request);
		return ($response == 'ok');
	}

	/**
	 *	Score a given translation from the WWL.  Returns true on success false on not success.
	 *
	 *  @param string $sl source language (ISO code)
	 *  @param string $tl target language (ISO code)
	 *  @param string $st string to be translated (UTF-8)
	 *  @param string $tt translation of $st to submit (UTF-8)
	 *	@param string $votetype 
	 *  @param string $username
	 *  @param string $pw
	 *  @param string $proxy
	 *	@return bool
	 */
	function score( $st, $tt, $votetype='', $username='', $pw='', $proxy='n') {

		$guid = MD5( $this->sourceLanguage . $this->targetLanguage . $st . $tt );
		
		// Score a translation and save it to the WWL server
		$request['guid'] = $guid;
		$request['votetype'] = $votetype;
		$request['username'] = $username;
		$request['pw'] = $pw;
		$request['proxy'] = $proxy;
		
		// Build the URL used in submitting this score.  Get the secure server.
		$url = $this->server(true) . '/scores/vote';
		$response = $this->sendRequest($url, $request);
		return ($response == 'ok');		
	}


	/**
	 *	Send a POST request via cURL
	 *
	 *  @param string $url where the cURL request is going
	 *  @param array $data included in the cURL request
	 *	@return bool
	 */
	function sendRequest($url, $data = array()) {
		if (!function_exists('curl_init')) {
			return '';
		}
		$curl = curl_init();
		curl_setopt($curl, CURLOPT_URL, $url);								
		curl_setopt($curl, CURLOPT_HEADER, false); 	
		curl_setopt($curl, CURLOPT_RETURNTRANSFER, true);
		if ($data) {
		 	curl_setopt($curl, CURLOPT_POST, true);									
			curl_setopt($curl, CURLOPT_POSTFIELDS, http_build_query($data));		
		}
		// Get the response and close the cURL session.
		$response = curl_exec($curl);
		curl_close($curl);
		return $response;
	}

} /* end Class wwl */

