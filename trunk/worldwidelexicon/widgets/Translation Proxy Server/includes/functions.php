<?php

/**
 *  The World Wide Lexicon Proxy, Helper Functions
 *  ===========================================================================================
 *  I tend to dislike functions files, but I'll do my best to keep this one clean and relevant.
 */


/**  Logging functions
 *   ==========================================================================================
 */

// Add a message to today's log
function log_message($type, $message_text)
{
	// Log files are created daily.
	$log_filename = LOG_PATH . date("Y-m-d") . ".txt";
	$entry = "";
	
	// Currently there are only two log levels, errors only or everything.
	if ( LOG_MESSAGES == "ERRORS_ONLY" && $type != "debug" ) {
		$entry = date("H:i:s") . " " . $type . "    " . $message_text . PHP_EOL;		
	} elseif ( LOG_MESSAGES == "ALL" ) {
		$entry = date("H:i:s") . " " . $type . "    " . $message_text . PHP_EOL;
	} elseif ( LOG_MESSAGES == "NONE") {
		$entry = "";
	}

	// If a log entry is in order, let's add it to the file
	if ( !empty( $entry ) ) {
		if (!$log_handle = fopen($log_filename, 'a')) {
	         echo "Cannot open file ($log_filename)";
	         exit;
	    }

	    // Write $entry to our opened file.
	    if (fwrite($log_handle, $entry) === FALSE) {
	        echo "Cannot write to file ($log_filename)";
	        exit;
	    }
		// And don't forget to close the file.
		fclose($log_handle);
	}
	

}



?>