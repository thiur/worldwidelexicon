<?php
class DrupalCache {
	var $ttl = 86400; /*= 24 hrs cache timeout in seconds*/
	var $prefix = "dc_";
	function set($key, $data, $ttl = 0) {
		if (!$ttl) {
			$ttl = $this->ttl;
		}
		$expire = time() + $ttl;
		cache_set($this->prefix.$key, $data, 'cache', $expire);
	}
	
	function get($key) {
		$res = cache_get($this->prefix.$key);
		return $res ? $res->data : '';
	}
	
	function verify() {
		if (!function_exists('cache_get')){
			$this->error = "cache_get function is not found. Using outside of Drupal?";
			return false;
		}
		return true;
	}
	
	function clear() {
		cache_clear_all($this->prefix, 'cache', TRUE);
	}
}
?>