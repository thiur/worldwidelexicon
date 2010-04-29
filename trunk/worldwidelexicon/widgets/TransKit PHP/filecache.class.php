<?php
/*
 * Based on wp-cache.php code (see copyright notice below)
 * Author: Alexey Gavrilov
 */
/*  Copyright 2005-2006  Ricardo Galli Granada  (email : gallir@uib.es)

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
*/
class FileCache {
	var $cacheDir = "/tmp/";
	var $filePrefix = "fc_";
	var $ttl = 86400; /*= 24 hrs cache timeout in seconds*/
	
	function __construct($cacheDir = null) {
		if ($cacheDir) {
			$this->cacheDir = $cacheDir;
		}
	}		
			
	function FileCache($cacheDir = null) {
		$this->__construct($param);		
	}
	
	function set($key, $data, $ttl = 0) {
		$file = $this->cacheDir.$this->filePrefix.$key;
		$fpo = @fopen($file, "w");
		if (!$fpo) return false;
		if (!$ttl) {
			$ttl = $this->ttl;
		}
		$expire = time() + $ttl;
		fwrite($fpo, $expire."\n");
		fwrite($fpo, $data);
		fflush($fpo);
		fclose($fpo);
		return true;
	}
	
	function get($key) {
		$file = $this->cacheDir.$this->filePrefix.$key;
		if (!file_exists($file))
			return "";
		$lines = file($file);
		// if cached content still valid? lines[0] is expiration timestamp
		if (intval($lines[0]) > time()) {
			array_shift($lines);
			return join ('', $lines);
		} else {
			@unlink($file);
			return "";
		}
	}
	
	function verify() {
		$dir = dirname($this->cacheDir);
		if ( !file_exists($this->cacheDir) ) {
			if ( !is_writable( $dir ) || !($dir = mkdir( $this->cacheDir, 0777) ) ) {
					$this->error = "Cache directory ($this->cacheDir) did not exist and couldn't be created by the web server. Check $dir permissions.";
					return false;
			}
		}
		if ( !is_writable($this->cacheDir)) {
			$this->error = "Cache directory ($this->cacheDir) or $dir need to be writable.";
			return false;
		}
	
		if ( '/' != substr($this->cacheDir, -1)) {
			$this->cacheDir .= '/';
		}
		return true;
	}
	
	function clear() {
		$expr = "/^".$this->filePrefix."/";
		if ( $handle = opendir( $this->cacheDir ) ) { 
			while ( false !== ($file = readdir($handle))) {
				if ( preg_match($expr, $file) ) {
					@unlink($this->cacheDir . $file);
				}
			}
			closedir($handle);
		}
	}
}
?>