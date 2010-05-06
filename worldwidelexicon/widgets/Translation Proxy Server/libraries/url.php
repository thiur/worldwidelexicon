<?php

	/**
	 *  Class that abstracts an URL
	 *  ============================
	 *  Easily create, manipulate, and get information about URLs, used for dynamic scripts.
	 * 
	 *  Example of use:
	 * 		$action = new URL();
	 * 		$action->addVal("form_submitted", "1");
	 * 		echo $action->toString();
	 */

	class URL
	{
		var $Text;
		var $Scheme;
		var $Host;
		var $Port;
		var $Path;
		var $Query;
		var $Fragment;
		var $Dynamic;  // TRUE if URL have GET vars
		var $Valid;
		var $Args = array();
		var $Cache; // cached previous build of URL


		/**
		 * URL::URL()
		 * 
		 * @param mixed $Text You can specify a URL, otherwise the current one is used.
		 * @return void
		 **/
		function URL($Text = false)
		{
			if ( $Text )
			{
				$this->Text = $Text;
			}	
			else
			{
				$s = empty($_SERVER["HTTPS"]) ? '' : ($_SERVER["HTTPS"] == "on") ? "s" : "";
				$protocol = substr(strtolower($_SERVER["SERVER_PROTOCOL"]), 0, strpos(strtolower($_SERVER["SERVER_PROTOCOL"]), "/")) . $s;
				$port = ($_SERVER["SERVER_PORT"] == "80") ? "" : (":".$_SERVER["SERVER_PORT"]);
				$this->Text = $protocol . "://" . $_SERVER['SERVER_NAME'] . $port . $_SERVER['REQUEST_URI'];
			}

			if ( $this->parseURL() )
				$this->Valid = TRUE;
			else
				$this->Valid = FALSE;
		}



		/**
		 * URL::toString()
		 * This is can be used to build a URL.
		 * @param boolean $full Set to FALSE if you don't want full URL (with hostname etc)
		 * @return string URL
		 **/
		function toString ($full=true)
		{
			$url = "";
			if ($full) {
				$url = $this->Scheme."://";
				$url .= $this->Host;
				if ( isSet($this->Port) ) $url .= ":".$this->Port;
			}
			$url .= $this->Path;
			$i = 0;
			
			foreach ( $this->Args as $key => $value ) {
				if ( $i == 0 ) $url .= "?";
				if ( !is_Null($value) ) $url .= $key."=".$value."&";
				$i = 1;
			}

			if ( $i > 0 ) $url = substr_replace($url, '', -1);
			if ( isSet($this->Fragment) ) $url .= "#".$this->Fragment;

			$this->Cache = $url;
			return $url;
		}


		// Returns the path of a given URL, as in www.domain.com/PATH
		function getPath()
		{
			return $this->toString(false);
		}


		// Returns the base url from a string in the form of example.com
		function getHost()
		{
			return $this->Host;
		}

		// Returns the base url WITHOUT the www in it.
		function getHostBase()
		{
			return preg_replace("%www\.%", "", $this->Host);
		}

		// Returns the domain for the current URL string in the form http://example.com
		function getDomain()
		{
			return $this->Scheme . "://" . $this->Host; 
		}


		/**
		 * URL::parseURL()
		 * This method is private, it parses URL on the parts.
		 * @return boolean URL is right or not;
		 **/
		function parseURL()
		{
			$tmp = parse_url( $this->Text );

			if ( isSet($tmp["scheme"]) )
				$this->Scheme = $tmp["scheme"];
			else
				return (FALSE);

			if ( isSet($tmp["host"]) )
				$this->Host = $tmp["host"];
			else
				return (FALSE);

			if ( isSet($tmp["path"]) )
				$this->Path = $tmp["path"];
			else
				return(FALSE);

			if ( isSet($tmp["query"]) )
				$this->Query  = $tmp["query"];

			if ( isSet($tmp["fragment"]) )
				$this->Fragment = $tmp["fragment"];

			if ( isSet($tmp["port"]) )
				$this->Port = $tmp["port"];

			unset($tmp);

			if ( isSet($this->Query) )
				$this->Dynamic = TRUE;
			else
			 	$this->Dynamic = FALSE;

			if ( $this->Dynamic )
			{
				$temp = explode("&",$this->Query);
				$i = 0;
				while ( list($key, $val) = each ($temp) )
				{
				      $tmp = explode("=",$val);
				      $this->Args[$tmp[0]] = !empty($tmp[1]) ? $tmp[1] : "";
				      $i++;
				}
			}
			return (TRUE);
		}


		/**
		 * URL::dropVal()
		 * Drops a key from URL.
		 * @param mixed $key A key of value to drop.
		 * @return string URL if ok or echo about error.
		 **/
		function dropVal($key)
		{
			if ( isSet($this->Args[$key]) )
				$this->Args[$key] = NULL;
			else
				echo "Key not found.";
			return $this->toString();
		}


		/**
		 * URL::Clear()
		 * Clears previous URL and let u work with another.
		 * @param string $Text This can be used to work with specific URL, not the current one.
		 * @return void
		 **/
		function Clear()
		{
			$this->URL();
			empty($this->Args);
		}


		/**
		 * URL::getVal()
		 * Gets a value from URL. (Even that values that are from 
		 * @param $key
		 * @return mixed key if everything is OK, or echo'es that key is not found.
		 **/
		function getVal ($key)
		{
			if ( isSet($this->Args[$key]) )
				return $this->Args[$key];
			else
				echo "Key not found.";
		}


		/**
		 * URL::addVal()
		 * Adds a key to URL.
		 * @param mixed $key A key to add.
		 * @param mixed $value Value of the key
		 * @return string URL
		 **/
		function addVal ($key, $value)
		{
			if ( !isSet($this->Args[$key]) )
				$this->Args[$key] = $value;
			else
				echo "Key already exists.";
			return $this->toString();
		}


		/**
		 * URL::setVal()
		 * 
		 * @param mixed $key Key name for parameter.
		 * @param mixed $value Value for parameter.
		 * @param boolean $create Create new key if not exists.
		 * @return Echo if key not found and builded URL if everything ok.
		 **/
		function setVal ($key, $value, $create=FALSE)
		{
			if ( isSet($this->Args[$key]) or $create == TRUE)
				$this->Args[$key] = $value;
			else
				echo "Key not found.";
			return $this->toString();
		}


		/**
		 * URL::is_Set()
		 * Checks if key is set in the URL.
		 * @param mixed $key 
		 * @return boolean  
		 **/
		function is_Set ($key)
		{
			if ( isSet($this->Args[$key]) )
				return TRUE;
			else
				return FALSE;
		}

	}

?>
