<?php

	/**
	 *  The World Wide Lexicon Proxy
	 *  =================================
	 *	The WWL Proxy takes the content from the URL that calls it, and translates it into the requested language.
	 *  You request a Proxy translation by pointing your domain at the Proxy like so: **.mydomain.com --> Proxy IP.
	 *
	 *  @author 		Cesar Gonzalez (icesar@gmail.com)
	 *  @version 		1.0
	 *  @license		BSD
	 *
	 */
	
	// Start by loading all the stuff we need.
	require('includes/config.php');
	require('includes/functions.php');
	require('libraries/filecache.php');
	require('libraries/wwl.php');
	require('libraries/url.php');
	require('libraries/curl.php');
	require('libraries/services_json.php');
	require('libraries/languagehelper.php');
	require('libraries/wwlproxy.php');
	require('libraries/wwlsettings.php');
	require('libraries/googletranslate.php');
	require('libraries/requestvalidator.php');
	
	
	// Ensure this is a valid, non-spam request.
	$request = new RequestValidator();
	if ( !$request->isAllowed() ) {
		log_message('error', $request->getMessage());
		//die($request->getMessage());
	}
		
	// Get the full URL from the current visitor's request.
	$full_url = new URL();
	$full_url_string = $full_url->toString();

	// Let's get the ball rolling 
	log_message('debug', "Welcome to the WWL PROXY! Request by " . $full_url_string . " from " . $_SERVER['REMOTE_ADDR']);

	// We'll need a language helper to deal with language detection, language codes, etc.
	$lang_helper = new LanguageHelper();

	// We'll need a few variable to initialize a proxy object below.  This is until all the language selection etc. 
	// is appropriately encapsulated.  Probably in the LanguageHelper object.
	$routeAllLinks = false;
	$sourceLanguage = "";
	$targetLanguage = "";
	$targetURL = "";
	
	// Next, we extract the source language, target language, and the target URL to be translated.
	// There are two special cases where the URL is routed through worldwidelexicion.org, handle those first.

	// (0) The base case:  Are we translating the actual WWL website?  This one we know.
	if ( preg_match('%http://..\.worldwidelexicon.org%', $full_url_string) )
	{
		$sourceLanguage = "en";
		$targetLanguage = $lang_helper->detectTargetLanguage();
		$targetUrl 		= new URL( preg_replace('%http://..\.%', 'http://www.', $full_url_string) );
		
	}
	// (1) For testing purposes, anyone can access x.y.worldwidelexicon.org/path where x->lang & y->domain
	elseif ( preg_match('%worldwidelexicon\.org%', $full_url_string) && !preg_match('%http://proxy\.worldwidelexicon\.org%', $full_url_string))
	{
		// Remove http:// and separate the URL at the .'s.  Then figure out source / target language & URL.
		$segments = explode( '.', preg_replace('%http://%', '', $full_url_string) );

		// Get the path (everything after the domain), so we can serve the correct page
		$path = $full_url->getPath();

		// Because we're using the worldwidelexicon.org address, route all subsequent links through the proxy
		$routeAllLinks = true;

		// Are both the source and target langauges specified, as in http://en_fr.blabla..?
		if ( strlen($segments[0]) == 5 && preg_match('/.._../', $segments[0]) )
		{
			// If this is 5 letters, in contains 2 language codes like so:
			$langs = explode( '_', $segments[0] );
			$sourceLanguage = $langs[0];
			$targetLanguage = $langs[1];

			// Now decipher the target domain
			if ( preg_match('/_/', $segments[1] ) ) { $targetUrl = new URL('http://' . preg_replace( '/_/', '.', $segments[1] ) . $path); } 
			else 									{ $targetUrl = new URL('http://www.' . $segments[0] . '.com' . $path); }
		}
		elseif ( strlen($segments[0]) == 2 ) 
		{ 
			// Is this only a 2-letter language code? That means implicit source lang is EN.
			$sourceLanguage = "en"; 
			$targetLanguage = $segments[0];

			// Now decipher the target domain
			if ( preg_match('/_/', $segments[1] ) ) { $targetUrl = new URL('http://' . preg_replace( '/_/', '.', $segments[1] ) . $path); } 
			else 									{ $targetUrl = new URL('http://www.' . $segments[1] . '.com' . $path); }
		}
		elseif ( preg_match( '/worldwidelexicon/', $segments[1]) )
		{
			// Is this is in the form domain.worldwidelexicon.org? Then assume the source lang is EN and auto-detect the target language.
			$sourceLanguage = "en";
			$targetLanguage = $lang_helper->detectTargetLanguage();

			// Now decipher the target domain
			if ( preg_match('/_/', $segments[0] ) ) { $targetUrl = new URL('http://' . preg_replace( '/_/', '.', $segments[0] ) . $path); } 
			else 									{ $targetUrl = new URL('http://www.' . $segments[0] . '.com' . $path); }
		}

	} 

	// (2) The second special case is an external link which has been routed through the WWL Proxy
	elseif ( preg_match('%http://proxy\.worldwidelexicon\.org%', $full_url_string))
	{
		//preg_match( '/l=(..)&u=(.+)$/', $full_url_string, $matches );
		//$sourceLanguage = "en";
		//$targetLanguage = $matches[1];
		//$targetUrl = new URL($matches[2]);
		$sourceLanguage = isset($_GET["sl"]) ? $_GET["sl"] : "en";
		$targetLanguage = isset($_GET["l"]) ? $_GET["l"] : $lang_helper->detectTargetLanguage();
		$targetUrl = new URL(isset($_GET["u"]) ? $_GET["u"] : "");
		$routeAllLinks = true;
	}
	
	// (3) Otherwise, this is the standard use of the proxy, via a direct URL like http://sl.domain.com/				
	else
	{
		// Start by looking at the current URL, and extracting the target language
		$sourceLanguage = $lang_helper->detectSourceLanguage();
		$targetLanguage = $lang_helper->detectTargetLanguage();
		$targetUrl 	 = new URL( $lang_helper->removeLanguageCode( $full_url_string ) );
	}
	log_message('debug', "We have {$targetUrl->toString()} from {$sourceLanguage} into {$targetLanguage}");
	// Let's initialize a virgin Proxy object.
	$wwl = new Wwlproxy($sourceLanguage, $targetLanguage, $targetUrl);
	$wwl->setLinkRouting($routeAllLinks);

	// And we're doing what?
	log_message('debug', "Translating {$targetUrl->toString()} from {$sourceLanguage} into {$targetLanguage}");

	// Next, let's ask the WWL to carry out the translation
	$wwl->translate();
	
	// And let's echo it out.
	echo $wwl->output();
	
?>