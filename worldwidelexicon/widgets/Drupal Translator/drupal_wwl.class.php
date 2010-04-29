<?php
class DrupalWWLController extends WWLController {
	var $tOptions = array(
		"mt" => "Allow machine translations", 
		"vol" => "Community translations",
		"pro" => "Request professional translations" 
	);
	
	function __construct($param = null) {
		$sl = $this->getSourceLanguage();
		$tl = $this->detectTargetLanguage();
		$this->config = $this->getLanguageConfig($tl);
		parent::__construct($sl, $tl, $param);
		$this->decorateOutput = !variable_get('wwl_hide_decorations', false);
	}				
	function wwlex($param = null) {
		$this->__construct($param);		
	}
	function getLanguageConfig($lang) {
		$config = array();
		$allowedMethods = variable_get('wwl_enable_target_'.$lang, array());
		foreach ($this->tOptions as $k=>$v){
			$config[$k] = ($allowedMethods[$k] !== 0);
		}
		$config["speaklike_user"] = variable_get('speaklike_user', '');
		$config["speaklike_pass"] = variable_get('speaklike_pass', '');
		// professional translations require credentials
		$config['pro'] = $config['pro'] && strlen($config["speaklike_user"]) > 0 && strlen($config["speaklike_pass"]) > 0;
		return $config;
	}
	function detectTargetLanguage() {
		global $language;
		$lang = $language->language;
		$lang = explode("-", $lang);
		$lang = $lang[0];
		$this->log("Target language: ".$lang);
		return $lang;
	}
	function getSourceLanguage() {
		$lang = variable_get('wwl_language', 'en'); //get_option('wwl_language');
		return $lang;
	}
	function canTranslate() {
		global $user;
		$this->config["username"] = $user->name;
		return $this->config["vol"] && (user_access("translate to ".$this->targetLanguage) || user_access("translate to any language"));
	}
}
?>