<?php

/**
 *	This class interacts with the Google Translate API.
 *
 * 	@author 		Cesar Gonzalez
 * 	@created 		17 March 2010
 *
 */

class GoogleTranslate {

    private $api_key = "ABQIAAAA6rShtqbXewD5F5b8nIKlSxQufwSbGmlFUuNf5dMqgv18WVB-KBRt6LVPNQP3jhIzmpvqHi6PNB_cPQ";
	private $api_url = "http://ajax.googleapis.com/ajax/services/language/translate";
	private $api_version = "1.0";
	private $api_encoding = "UTF8";
	private $api_referer = "http://proxy.worldwidelexicon.org/";
	private $user_ip = "";
	    
	public $sourceLanguage;
	public $targetLanguage;

	const BASE_REQUEST_LENGTH = 199;    
	const API_MAX_CHARS = 5000;
	const API_MAX_BATCH = 50;

	function __construct($sl, $tl, $key) {

		$this->user_ip = $_SERVER['REMOTE_ADDR'];
		$this->targetLanguage = $tl;
		$this->sourceLanguage = $sl;
		if (!empty($key)) { $this->api_key = $key; }


        log_message('debug', "GoogleTranslate class initialized - source: $sl, target: $tl");
	}
	
	function GoogleTranslate($sl = '', $tl = '', $key = '') {
		$this->__construct($sl, $tl, $key);
	}

 
    /* =================================================================================
     * KISS.
     * ================================================================================= */

	function get($st) {
	
		// Check that all required pieces are available.
		if ( !function_exists('curl_init') || empty($this->sourceLanguage) || empty($this->targetLanguage) || empty($st) ) { 
			log_message('debug', "GoogleTranslate class failed - source: $sl, target: $tl, string: $st");
			return ""; 
		}

		$response 		= $this->sendRequest("q=$st");
		$json 			= new Services_JSON(SERVICES_JSON_LOOSE_TYPE);
		$json_decoded 	= $json->decode($response);

		if ($json_decoded["responseStatus"] == "200") {
			return $json_decoded["responseData"]["translatedText"];
		}
		else {
			return "";
		}
		
	}


	function getmultiple($starray) {
	
		// Check that all required pieces are available.
		if ( !function_exists('curl_init') || empty($this->sourceLanguage) || empty($this->targetLanguage) || empty($starray) ) {
			log_message('debug', "GoogleTranslate class failed - source: $sl, target: $tl, strings: $starray");
			return ""; 
		}
		
		$compliant_requests 	= array();
		$request 				= "";
		$len 					= self::BASE_REQUEST_LENGTH;
		$batch					= 0;

		// Add each string to be translated as a separate q, split into multiple requests of less than 5000 characters each.
		foreach ( $starray as $st ) { 
		
			// echo "|".urlencode($st)."|<br />";
					
			$nq 	= "&q=" . urlencode( $st );
			$len   += strlen( $nq );
			$batch++;
			
			if ($len < self::API_MAX_CHARS && $batch < self::API_MAX_BATCH) 
			{
				$request .= $nq;
			}
			else
			{
				$compliant_requests[] 	= $request;
				$request				= $nq;
				$len					= self::BASE_REQUEST_LENGTH + strlen( $nq );
				$batch					= 0;
			}
		}
		
		// Don't forget to add the last querystring we were building to the compliant_requests...
		$compliant_requests[] = $request;

		// We're going to some JSON into a simple return array.
		$json = new Services_JSON(SERVICES_JSON_LOOSE_TYPE);		
		$ret  = array();
		
		// Now we have an array of compliant requests, let's send them one by one to google.
		foreach ( $compliant_requests as $req ) {
		
			$response 		= $this->sendRequest( $req );
			$json_decoded 	= $json->decode($response);
	
			// Decipher the JSON response and build a clean translations array;
			if ($json_decoded["responseStatus"] == "200") {
				foreach ( $json_decoded["responseData"] as $trans ) {
					if ($trans["responseStatus"] == "200") {
						$ret[] = $trans["responseData"]["translatedText"];
					}
					else {
						log_message("debug", "Google Translate: " . $json_decoded["responseStatus"] . " ".$json_decoded["responseDetails"]);
						$ret[] = "";
					}
				}
			} 
			else 
			{
				log_message("debug", "Google Translate: " . $json_decoded["responseStatus"] . " ".$json_decoded["responseDetails"]);		
			}						
		}


		// This is where we fix the spacing issue caused when Google Translate strips leading and trailing spaces.
		// Go through the source texts, and if the source text had leading or trailing spaces, then add them to
		// the resulting translations as well.
		foreach ( $ret as $i => $tt ) {
			$st = $starray[$i];
			if ($st[0] == " ") { $ret[$i] = " " . $ret[$i]; }
			if ($st[(strlen($st)-1)] == " ") { $ret[$i] = $ret[$i] . " "; }
		}
		
		//echo "<hr>";
		//foreach ($ret as $r) { echo "|".$r."|<br />"; }
		//die();
		
		return $ret;

	}
	
	
	// Do all the cURL busywork in one place.  I know, I should really use the cURL class..
	private function sendRequest($querystring) {
			
		$request['langpair'] 	= $this->sourceLanguage . "|" . $this->targetLanguage;
		$request['v']			= $this->api_version;
		$request['ie']			= $this->api_encoding;
		
		if (!empty($this->api_key)) { $request['key']		= $this->api_key; }
		if (!empty($this->user_ip)) { $request['userip']	= $this->user_ip; }

		$querystring = http_build_query($request) . $querystring;
	
		$curl_handle = curl_init();

		curl_setopt($curl_handle, CURLOPT_URL, $this->api_url);							// where are we requesting?
		curl_setopt($curl_handle, CURLOPT_HEADER, false); 					 			// don't output the returned HTTP headers
		curl_setopt($curl_handle, CURLOPT_RETURNTRANSFER, true);						// return output as string
		curl_setopt($curl_handle, CURLOPT_REFERER, $this->api_referer);					// Google API requires setting the referer
	 	curl_setopt($curl_handle, CURLOPT_POST, true);									// use a POST request
		curl_setopt($curl_handle, CURLOPT_POSTFIELDS, $querystring);					// variable to post
        curl_setopt($curl_handle, CURLOPT_TIMEOUT, 10);									// set the timeout

		$response = curl_exec($curl_handle);
		curl_close($curl_handle);
		
		return $response;
	}
	
}
