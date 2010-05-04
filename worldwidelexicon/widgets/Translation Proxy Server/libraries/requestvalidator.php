<?php

	/**
	 *	class RequestValidator - This class decides whether a given request to serve a page is valid and allowed.  It's intented to
	 *							cut down on requests that are malicious, spam, or simply not whitelisted.
	 *		
	 *	@author		Cesar Gonzalez (icesar@gmail.com)
	 *	@version	0.1
	 *	@license	BSD
	 */

	// Let's display all errors for now.
	ini_set('display_errors', 1); 
	error_reporting(E_ALL);

	class RequestValidator {
	
		private $requested_url;
		private $remote_ip;
		private $refer;
		private $message;
		
		private $request_is_valid;
	
	
		function __construct() {
		
			// We will use the $_REQUEST global var to figure out whether this is a valid request.
			$url_obj = new Url();
	
			$this->requested_url 		= $url_obj->toString();
			$this->remote_ip 			= !empty($_SERVER['REMOTE_ADDR']) ? $_SERVER['REMOTE_ADDR'] : '';
			$this->referer				= !empty($_SERVER['HTTP_REFERER']) ? $_SERVER['HTTP_REFERER'] : '';
			$this->request_is_valid 	= false;
	
			// Check all three conditions necessary to allow this request
			if ( $this->isWhiteListed() && $this->isRefererValid() && $this->isWithinLimit() ) { $this->request_is_valid = true; }
		}
	
		function RequestValidator() {
			$this->__construct();
		}
	
	
		// The point of this class.  To decide whether a given request is allowed.
		public function isAllowed() {
			return $this->request_is_valid;	
		}
		
		public function getMessage() {
			if ($this->request_is_valid) {
				$this->message = "Valid request for " . $this->requested_url . " from " . $_SERVER['REMOTE_ADDR'];
			} else {
				$this->message = "WWL Proxy denied service to request for " . $this->requested_url . " from " . $_SERVER['REMOTE_ADDR'];
			}
			return $this->message;
		}
		
		
		
		/** Private Functions ********************************************************************/
		
		// Is the URL being requested part of our Whitelist?
		private function isWhiteListed( $url = '' ) {

			$whitelist	= explode(" ", PROXY_WHITELIST);
			$allowed	= false;

			if ( $url == '' ) { $url = $this->requested_url; }	
							
			foreach ($whitelist as $domain) {
	
				// remove extension from whitelist domain, in order to match these: domain.wwl.org
				$domain = preg_replace('/\....$/', '', $domain);
				if ( preg_match("/$domain/", $url) ) { $allowed = true; }	
			}
			
			return $allowed;
		}
		
	
		//  When a request is routed through the WWL, we have to verify that it was validly referred from one of our whitelisted URLs
		private function isRefererValid() {
	
			/*
			
			// This code only makes sense for requests routed through the WWL
			if ( !preg_match("/proxy\.worldwidelexicon\.org/", $this->requested_url) ) { return true; }

			// Check if the referring URL exists, and if so, if it is whitelisted
			elseif ( empty( $this->referer ) ) { return false; }
			elseif ( !($this->isWhiteListed( $this->referer )) ) { return false; }
			
			else { return true; }
			
			*/
			
			return true;
		}
	
	
		// The plan is to rate-limit the number or requests any user can make to the WWL Proxy to 1 per second for now
		private function isWithinLimit() {
	
			/*
				+ There are two good ways to implement this;
				+ by saving requests to the database
				+ by using memcached to track IP addresses (google this again)
			*/
			
			return true;
		}
	
	}
	
?>