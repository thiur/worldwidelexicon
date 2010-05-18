<?php
/**
 *  WWLAPI: a simple PHP wrapper library for the World Wide Lexicon API
 *  This library enables PHP based applications to easily interact with the servers of the World Wide Lexicon.
 *
 *	@package		wwlphp
 *  @author 		Cesar Gonzalez (icesar@gmail.com)
 * 					Alexey Gavrilov
 *  @version 		1.0
 *  @license		BSD
 *
 */

/**
 *	This class encapsulates the functionality of the WWL (the World Wide Lexicon) for automatically
 *	translating content on the web between languages.
 *	@package		wwlphp
 */
class WWLAPI extends BaseTranslator {
	
	var $wwl_servers = array('www.worldwidelexicon.org'); //array('3.latest.worldwidelexicon.appspot.com');
	var $secure_wwl_servers = array('worldwidelexicon.appspot.com');
	

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
		if ( $secure ) { 
			$url = 'https://' . $this->secure_wwl_servers[$idx]; 
		} else { 
			$url = 'http://' . $this->wwl_servers[$idx]; 
		}

		return $url;
	}

	
	/**
	 *	This function is used to get the best available translation from a WWL server.
	 *	
	 *  @param string $sl source language (ISO code)
	 *  @param string $tl target language (ISO code)
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
				  $ip_filter='', $lsp='', $lspusername='', $lsppw='', $mtengine='' ) {
	
		// Make sure vital arguments are not empty strings.
		if ( strlen($this->sourceLanguage) > 0 && strlen($this->targetLanguage) > 0 && strlen($st) > 0 ) {
			
			// No on both counts? Then let's request a translation from the WWL server
			$request['sl'] = $this->sourceLanguage;
			$request['tl'] = $this->targetLanguage;
			$request['st'] = $st;//str_replace("&", "%26", $st); // hack, must be removed once service is fixed
			//$request['domain'] = $domain;
			$request['hostname'] = $_SERVER['HTTP_HOST'];
			$request['lucky'] = 'y';
			$request['allow_machine'] = $allow_machine;
			$request['allow_anonymous'] = $allow_anonymous;
			$request['require_professional'] = $require_professional;
			$request['ip'] = $ip_filter;
			$request['lsp'] = $lsp;
			$request['lspusername'] = $lspusername;
			$request['lsppw'] = $lsppw;
			$request['mtengine'] = $mtengine;
			$request['output'] = 'json';
			
			$url = $this->server() . "/t"; //was /q
			$response = $this->sendRequest($url, $request);	
			if ($response) {
				$response = $this->jsonDecode($response);
				if ($response && $response["records"] && $response["records"][0] && $response["records"][0]["tx"]){
					
					$this->meta["mtengine"] = $response["records"][0]["tx"]["mtengine"];
					$this->meta["username"] = $response["records"][0]["tx"]["username"];
					if (!$this->meta["username"] && $response["records"][0]["tx"]["tt"]) {
						$this->meta["username"] = "unknown";
					}
					// Empty translated text -> metadata may not be correct so reset them
					if (!$response["records"][0]["tx"]["tt"]) {
						$this->meta = array("mtengine" => "", "username" => "");
					}
					return $response["records"][0]["tx"]["tt"];
				}
				$this->error = "Can't parse server response";
			}
			
		}
		$this->meta = array("mtengine" => "", "username" => "");
		return ''; 
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
		
		// And now submit the translation to the WWL server
		$request['sl'] = $this->sourceLanguage;
		$request['tl'] = $this->targetLanguage;
		$request['st'] = $st;
		$request['tt'] = $tt;
		$request['domain'] = $domain;
		$request['url'] = $url;
		$request['username'] = $username;
		$request['pw'] = $pw;
		$request['ip'] = $_SERVER["REMOTE_ADDR"];
		$request['proxy'] = 'y';
		
		// Build the URL for the REST submission
		$url = $this->server() . "/submit";
		$response = $this->sendRequest($url, $request);
		return $response;
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
	 *	@return bool
	 */
	function score( $st, $tt, $score=0, $username='', $pw='') {

		$guid = MD5( $this->sourceLanguage . $this->targetLanguage . $st . $tt );
		
		// Score a translation and save it to the WWL server
		$request['guid'] = $guid;
		$request['score'] = $score;
		$request['username'] = $username;
		$request['pw'] = $pw;
		$request['ip'] = $_SERVER["REMOTE_ADDR"];
		$request['proxy'] = 'y';
		
		// Build the URL used in submitting this score.  Get the secure server.
		$url = $this->server(true) . '/scores/vote';
		$response = $this->sendRequest($url, $request);
		return $response;		
	}

} /* end Class wwl */

