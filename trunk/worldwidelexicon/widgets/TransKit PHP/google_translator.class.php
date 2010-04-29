<?php
class GoogleTranslator extends BaseTranslator {

	var $methods = array('mt');
	var $meta = array("mtengine" => "google", "username" => "");

	function get($st, $config){
		if (!$this->canTranslate($config)){
			return '';
		}
		$url = "http://ajax.googleapis.com/ajax/services/language/translate";
		$params = array(
			"v" => "1.0",
			"q" => $st,
			"langpair" => $this->sourceLanguage."|".$this->targetLanguage,
			"userip" => $_SERVER["REMOTE_ADDR"]
		);
		
		$res = $this->sendRequest($url, $params);
		if ($res) {
			$res = $this->jsonDecode($res);
			if ($res["responseStatus"] == "200"){
				return $res["responseData"]["translatedText"];
			}
			$this->error = $res["responseStatus"]." ".$res["responseDetails"];
		}
		return '';
	}
	
}
?>