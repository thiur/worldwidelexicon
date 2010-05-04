<?php

	/**
	 *  The World Wide Lexicon Proxy -- Cache Manager (cron job)
	 *  ===============================================================
	 *	Since we're using file cacheing at the moment, keep it clean!
	 *
	 *  @author 		Cesar Gonzalez (icesar@gmail.com)
	 *  @version 		0.1
	 *  @license		BSD
	 *
	 */
	
	// Let's display all errors for now.
	ini_set('display_errors', 1); 
	error_reporting(E_ALL);

	// Let's load the necessary libraries
	require('../includes/config.php');
	require('../includes/functions.php');
	require('../libraries/filecache.php');

	// Some local variables
	$cacher = null;
	
	// Let's attempt to access the file cache
	if (class_exists("FileCache")) {
		$cacher = new FileCache( CACHE_PATH );
		
		// exit Cache Manager, unless configured properly
		if (!$cacher->verifyCacheDir()) {
			log_message('error', "Cache Manager failed: " . $cacher->error );
			exit;
		} else {
			log_message('debug', "Cache Manager initialized successfully.");
		}
	} else {
		log_message('error', "Cache Manager failed: No FileCache class found.");
		exit;
	}
	
	// Simple enough.  Let's set the time-to-live appropriately, and then clear the expired cache entries.
	$cacher->setTTL( CACHE_TTL );
	$cacher->clearExpired();
	log_message('debug', "Cache Manager done!");
	
?>