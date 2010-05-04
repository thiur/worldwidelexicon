<?php

	/**
	 *  Class used o log errors and debugging messages.
	 *  ================================================
	 *  Example of use:
	 * 		$log = new Log('/this/path/to/logs/');
	 * 		$log->message('ERROR', 'Your laptop blew up.');
	 */

	class Log
	{
		var $log_filename;


		/**
		 * Log::Log()
		 * 
		 * @param string $path The path to the logs directory
		 * @return void
		 **/
		function Log( $path='')
		{
			// Log files are created daily.
			$this->log_filename = date("Y-m-d") . ".txt";

			// Let's try the default log directory
			if ( empty($path) )
				$this->log_filename = "/var/www/html/logs/" . $this->log_filename;
			else
				$this->log_filename = $path . $this->log_filename;
		}
		
		
		/**
		 *  Add a message to the log.
		 */
		function message($type, $message_text)
		{
			// Compose the entry in the log file
			$entry = date("H:i:s") . " " . $type . "    " . $message_text . PHP_EOL;
			
			if (!$log_handle = fopen($this->log_filename, 'a')) {
		         echo "Cannot open file ($this->log_filename)";
		         exit;
		    }
		
		    // Write $entry to our opened file.
		    if (fwrite($log_handle, $entry) === FALSE) {
		        echo "Cannot write to file ($this->log_filename)";
		        exit;
		    }
		
			// And don't forget to close the file.
			fclose($log_handle);
		}	    
	}
	
?>