<?php
class WWLTranslator extends WWLAPI /* extends BaseTranslator */ {
	var $methods = array('vol', 'pro'); // exclude 'mt' as we use Google directly for it
	
	function get($st, $config){
		if (!$this->canTranslate($config)){
			return '';
		}

		$res = parent::get(
			$st, '', 
			($config["mt"] && $this->methods["mt"]) ? 'y' : 'n', 
			$config["vol"] ? 'y' : 'n',
			$config["pro"] ? 'y' : 'n',
			'',
			$config["pro"] ? 'speaklike' : '',
			$config["pro"] ? $config["speaklike_user"] : '',
			$config["pro"] ? $config["speaklike_pass"] : ''
		);
		
		return $res;
	}
	function submit($st, $tt, $config){
		
		$res = parent::submit(
			$st,
			$tt,
			$_SERVER['HTTP_HOST'],
			$config["url"],
			$config["username"]
		);
		
		return $res;
	}
}
?>