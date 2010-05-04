<?php

/**
 *  The World Wide Lexicon Proxy -- AJAX Submission
 *  ================================================
 *
 *  @author 		Cesar Gonzalez (icesar@gmail.com)
 *  @version 		1.0
 *  @license		BSD
 *
 */

// Try not to output anything.
ini_set('display_errors', 0); 
//error_reporting(E_ALL);

// Start by loading the stuff we need.
require('../../includes/config.php');
require( PROXY_HOME_PATH . 'includes/functions.php');
require( PROXY_HOME_PATH . 'libraries/wwl.php');
require( PROXY_HOME_PATH . 'libraries/curl.php');
require( PROXY_HOME_PATH . 'libraries/wwlproxy.php');

$slang		= $_POST["slang"];
$tlang		= $_POST["tlang"];
$stext		= $_POST["stext"];
$ttext		= $_POST["ttext"];

$wwl = new Wwl();

$wwl->sourceLanguage = $slang;
$wwl->targetLanguage = $tlang;


// Let's get the ball rolling 
log_message('debug', 'AJAX: sending inline translation: ' . $stext . ' -> ' . $ttext);

// Min requirements for anonymous translations.  Next step, implement acccounts.
$ret = $wwl->submit( $stext, $ttext );

if ($ret)   { log_message('debug', 'AJAX: submission successful.'); echo 1; }
else 		{ log_message('error', 'AJAX: submission failed.'); echo 0; }

?>