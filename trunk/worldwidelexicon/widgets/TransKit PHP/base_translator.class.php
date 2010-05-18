<?php
class BaseTranslator {
	var $error = "";
	var $targetLanguage = "";
	var $sourceLanguage =  "";
	var $methods = array();
	var $meta = array();
	
	function canTranslate($config){
		foreach ($this->methods as $method){
			if ($config[$method]){
				return true;
			}
		}
		return false;
	}
	
	function verify(){
		if (!function_exists('curl_init')) {
			$this->error = "CURL is not installed";
			return false;
		}
		return true;
	}
	
	function sendRequest($url, $data = array()) {
		if (!function_exists('curl_init')) {
			return '';
		}
		$this->lastUrl = $url."\n".http_build_query($data);
		$curl = curl_init();
		curl_setopt($curl, CURLOPT_URL, $url);	
		curl_setopt($curl, CURLOPT_REFERER, "http://www.worldwidelexicon.org/");	
		curl_setopt($curl, CURLOPT_HEADER, false); 	
		curl_setopt($curl, CURLOPT_RETURNTRANSFER, true);
		curl_setopt($curl, CURLOPT_TIMEOUT, 20);	
		if ($data) {
		 	curl_setopt($curl, CURLOPT_POST, true);									
			curl_setopt($curl, CURLOPT_POSTFIELDS, $data);	
			//curl_setopt($curl, CURLOPT_POSTFIELDS, http_build_query($data));	
		}
		// Get the response and close the cURL session.
		$response = curl_exec($curl);
		if (curl_getinfo($curl, CURLINFO_HTTP_CODE) != "200") {
			$this->error = "HTTP_CODE: ".curl_getinfo($curl, CURLINFO_HTTP_CODE)." ".$response;
			return '';
		}
		curl_close($curl);
		return $response;
	}
	
	function jsonDecode($input) {
		$json = new Services_JSON(SERVICES_JSON_LOOSE_TYPE);
		return $json->decode($input);
	}
}
?>