<?php
/*
 * WWLController implementation for Wordpress
 */
class WordpressWWLController extends WWLController {
	var $tOptions = array(
		"mt" => "Allow machine translations", 
		"vol" => "Community translations",
		"pro" => "Request professional translations" 
	);
	function __construct($param = null) {
		$sl = $this->getSourceLanguage();
		$tl = $this->detectUserLanguage();
		$this->config = $this->getLanguageConfig($tl);
		parent::__construct($sl, $tl, $param);
		$this->decorateOutput = !get_option('wwl_hide_decorations');
	}				
	function wwlex($param = null) {
		$this->__construct($param);		
	}

	function getLanguageConfig($lang) {
		$config = array();
		foreach ($this->tOptions as $k=>$v){
			switch ($k) {
				case "vol":
					$config[$k] = get_option($lang.'_'.$k.'_select');
					break;
				default:	
					$config[$k] = get_option($lang.'_'.$k.'_enable');
			}
		}
		
		$config["speaklike_user"] = get_option('speaklike_user');
		$config["speaklike_pass"] = get_option('speaklike_pass');
		// professional translations require credentials
		$config['pro'] = $config['pro'] && strlen($config["speaklike_user"]) > 0 && strlen($config["speaklike_pass"]) > 0;
		if ($config["vol"] == "none") {
			$config["vol"] = false;
		}
		return $config;
	}
	function registerWpOptions() {
		register_setting('wwl-options', 'wwl_language');
		register_setting('wwl-options', 'speaklike_user');
		register_setting('wwl-options', 'speaklike_pass');
		register_setting('wwl-options', 'wwl_hide_decorations');
		register_setting('wwl-options', 'wwl_translation_timeout');
		register_setting('wwl-options', 'wwl_cache_timeout');
		register_setting('wwl-options', 'wwl_hook_gettext');
		foreach($this->languages as $lang=>$name) {
			foreach ($this->tOptions as $k=>$v){
				switch ($k) {
					case "vol":
						register_setting('wwl-options', $lang.'_'.$k.'_select');
						break;
					default:	
						register_setting('wwl-options', $lang.'_'.$k.'_enable');
				}
			}
		}
	}
	function getSourceLanguage() {
		$lang = get_option('wwl_language');
		if (!$lang ) $lang = WPLANG;
		if (!$lang ) $lang = "en";
		$this->log("Source language: ".$lang);
		return $lang;
	}
	function getUserRole() {
		$current_user = wp_get_current_user();
		$this->config["username"] = $current_user->display_name;
		return isset($current_user->roles[0]) ? $current_user->roles[0] : "anonymous";
	}
	function canTranslate() {
		$userRole = $this->getUserRole();
		$requiredRole = $this->config["vol"];
		if (!$requiredRole) {
			$requiredRole = "none";
		}
		foreach ($this->listRoles() as $role => $name) {
			if ($role == $userRole) {
				return true;
			}
			if ($role == $requiredRole) {
				return false;
			}
		}
	}
	function listRoles() {
		$role = new WP_Roles();
		$out = array(
			"none" => "Disabled"
		);
		foreach ($role->roles as $k=>$v) {
			$out[$k] = $v['name'];
		}
		$out["anonymous"] = "Anonymous";
		return $out;
	}
}

?>