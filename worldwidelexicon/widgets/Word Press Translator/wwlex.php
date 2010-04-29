<?php
/*
Plugin Name: Worldwide Lexicon Translator
Plugin URI: http://worldwidelexicon.org/
Description: Add community-powered, professional or automatic translations to your WordPress blog.
Version: 0.98
Author: Worldwide Lexicon Inc
Author URI: http://www.worldwidelexicon.org/
*/
// Pre-2.6 compatibility
if ( ! defined( 'WP_CONTENT_URL' ) )
      define( 'WP_CONTENT_URL', get_option( 'siteurl' ) . '/wp-content' );
if ( ! defined( 'WP_CONTENT_DIR' ) )
      define( 'WP_CONTENT_DIR', ABSPATH . 'wp-content' );
if ( ! defined( 'WP_PLUGIN_URL' ) )
      define( 'WP_PLUGIN_URL', WP_CONTENT_URL. '/plugins' );
if ( ! defined( 'WP_PLUGIN_DIR' ) )
      define( 'WP_PLUGIN_DIR', WP_CONTENT_DIR . '/plugins' );

require (dirname(__FILE__)."/wwl.libs/services_json.class.php");
require (dirname(__FILE__)."/wwl.libs/filecache.class.php");
require (dirname(__FILE__)."/wwl.libs/base_translator.class.php");
require (dirname(__FILE__)."/wwl.libs/wwl_api.class.php");
require (dirname(__FILE__)."/wwl.libs/wwl_translator.class.php");
require (dirname(__FILE__)."/wwl.libs/google_translator.class.php");
require (dirname(__FILE__)."/wwl.libs/wwl_controller.class.php");
require (dirname(__FILE__)."/wordpress_wwl.class.php");

$wwlex = new WordpressWWLController(WP_PLUGIN_DIR);
$wwlex->addCacheProvider(new FileCache(WP_PLUGIN_DIR."/wwlex-cache/"));
$wwlex->addTranslationProvider(new WWLTranslator());
$wwlex->addTranslationProvider(new GoogleTranslator());
	
if (get_option('wwl_translation_timeout')) {
	$wwlex->timeout = get_option('wwl_translation_timeout');
}
if (get_option('wwl_cache_timeout')) {
	$wwlex->setCacheTTL(get_option('wwl_cache_timeout'));
}

function wwl_init() {
	global $wwlex;

	add_action('admin_menu', 'wwl_config_page');
}
function wwl_admin_init() {
	global $wwlex;
	// Never translate content inside admin pages
	$wwlex->needTranslation = false;
	if (function_exists('register_setting')){
		$wwlex->registerWpOptions();
	}
}
function wwl_inject_script() {
	wp_print_scripts( array( 'sack' ));
	$parts = preg_split("/(\\\\|\/)/", dirname(__FILE__), -1, PREG_SPLIT_NO_EMPTY);
	$plugin_url = array_pop($parts);
	
	echo '<!--wwl script--><script src="'.WP_PLUGIN_URL.'/'.$plugin_url.'/wwlex.js" type="text/javascript"></script>';
	echo '<!--wwl css--><link rel="stylesheet" href="'.WP_PLUGIN_URL.'/'.$plugin_url.'/wwl.libs/wwlex.css" type="text/css" media="screen" />';
}
function wwl_footer() {
	global $wwlex;
	echo '<script type="text/javascript">';
	echo 'wwl.chunks = '.$wwlex->chunksJSON().';';
	echo 'wwl.sourceLanguageName = "'.$wwlex->sourceLanguageName().'";';
	echo 'wwl.targetLanguageName = "'.$wwlex->targetLanguageName().'";';
	echo 'wwl.targetLanguage = "'.$wwlex->targetLanguage.'";';
	echo 'wwl.ajaxurl = "'.get_option('siteurl').'/wp-admin/admin-ajax.php";';
	echo '</script>';
	echo '<div id="wwl-inline-editor" class="wwl-hide" dir="'.($wwlex->isTargetRtl() ? 'rtl':'ltr').'" lang="'.$wwlex->targetLanguage.'">';
	echo '	<div id="wwl-inline-editor-title">'.__('Edit translation').'</div>';
	echo '	<div id="wwl-inline-editor-original"></div>';
	echo '	<textarea id="wwl-inline-editor-translated"></textarea>';
	echo '	<input id="wwl-inline-editor-update" type="button" value="'.__('Update translation').'" onclick="return wwl.submitTranslation();"/>';
	echo '	or <a href="#" onclick="return wwl.hideTranslatorWindow();">'.__('Cancel').'</a>';
	echo '</div>';
}
function wwl_config_page() {
	add_options_page(__('Worldwide Lexicon Options'), __('Worldwide Lexicon'), 'administrator', 'wwlex-options', 'wwl_options');
}

function wwl_options() {
	global $wwlex;
	require(dirname(__FILE__)."/wwlex.options.php");
}

function wwl_clear_cache() {
	global $wwlex;
	$wwlex->clearCache();
}

function wwl_update_translation() {
	global $wwlex;
	$wwlex->setTargetLanguage($_POST["tl"]);
	$wwlex->config["url"] = $_POST["url"];
	if (!$wwlex->canTranslate()){
		die("{'error':'Access denied'}");
	}
	$out = array();
	$out["chunkId"] = $_POST["chunkId"]; // echo back
	$out["result"] = $wwlex->updateTranslation($_POST["source"], $_POST["text"]);
	$out["translated"] = $wwlex->moveTags($_POST["sourceWithTags"], $_POST["text"]);
	//print_r($out);
	die(str_replace("\\\\", "\\", $wwlex->jsonEncode($out)));
}

function wwl_sidebar_widget($args) {
	extract($args);
	global $wwlex;
	require(dirname(__FILE__)."/wwlex.widget.php");
}
// title doesn't need splitting into chunks
function wwl_translate_title($str) {
	global $wwlex, $id, $post;
	$str = html_entity_decode($str, ENT_COMPAT, "UTF-8");
	if (($post->post_title == $str) && ($wwlex->decorateOutput || $wwlex->canTranslate())) {
		$idt = "wwl-title-".$id;
		return 	'<span id="'.$idt.'" dir="'.($wwlex->isTargetRtl() ? 'rtl':'ltr').'" lang="'.$wwlex->targetLanguage.'">'.$wwlex->translateSentence($str, true).'</span>'.
				'<span id="'.$idt.'_tr" class="wwl-hide">'.$str.'</span>';
	} else {
		return '<span dir="'.($wwlex->isTargetRtl() ? 'rtl':'ltr').'" lang="'.$wwlex->targetLanguage.'">'.$wwlex->translateSentence($str).'</span>';
	}
}
function wwl_translate_content($str) {
	global $wwlex, $id;
	$str = html_entity_decode($str, ENT_COMPAT, "UTF-8");
	if ($wwlex->decorateOutput || $wwlex->canTranslate()) {
		$idt = "wwl-title-".$id;
		$idw = "wwl-content-".$id;
		$out = "<span id=\"".$idw."\"><blockquote class=\"wwl-decorations\">(".$wwlex->sourceLanguageName()." &rarr; ".$wwlex->targetLanguageName().") ";
		$out.= "<a href\"#\" onclick=\"wwl.swap('".$id."_tr', '".$id."'); return false;\">".__('View original')."</a>";
		if ($wwlex->canTranslate()) {
			$out.= ' [<a href="#" onclick="return wwl.edit(\''.$id.'\');">'.__('Edit').'</a>]';
		}
		$out.= "</blockquote>";
		$out.= '<span dir="'.($wwlex->isTargetRtl() ? 'rtl':'ltr').'" lang="'.$wwlex->targetLanguage.'">';
		$out.= $wwlex->translateContent($str, true);
		$out.= "</span>";
		$out.= "</span>";
		$out.= "<span id=\"".$idw."_tr\" class=\"wwl-decorations wwl-hide\">";
		$out.= "<blockquote>".__('(original)')." ";
		$out.= "<a href\"#\" onclick=\"wwl.swap('".$id."', '".$id."_tr'); return false;\">".__('View')." ".$wwlex->targetLanguageName()." ".__('translation')."</a></blockquote>";
		$out.= $str."</span>";
	} else {
		$out = '<span dir="'.($wwlex->isTargetRtl() ? 'rtl':'ltr').'" lang="'.$wwlex->targetLanguage.'">';
		$out.= $wwlex->translateContent($str);
		$out.= "</span>";
	}
	return $out;
}

function wwl_gt($translated) {
	global $wwlex;
	if ($wwlex->needTranslation) {
		$res = $wwlex->translateContent($translated);
	} else {
		$res = $translated;
	}
	return $res;
}

function wwl_gte($text) {
	echo wwl_gt($text);
}

function wwl_shortcode($atts, $content = null){
	global $id;
	//echo("id:".$id);
	//print_r($atts);
	return '';
}

add_shortcode('wwlex', 'wwl_shortcode');

add_action('init', 'wwl_init');
add_action('admin_init', 'wwl_admin_init');
add_action('wp_head', 'wwl_inject_script');
add_action('wp_footer', 'wwl_footer');
add_action('wp_ajax_wwl_clear_cache', 'wwl_clear_cache');
add_action('wp_ajax_wwl_update_translation', 'wwl_update_translation');
add_action('wp_ajax_nopriv_wwl_update_translation', 'wwl_update_translation');

register_sidebar_widget('Worldwide Lexicon Widget', 'wwl_sidebar_widget');

// don't add the filter unless we need it
if ($wwlex->needTranslation && !strstr($_SERVER["REQUEST_URI"], "wp-admin")) {
	// Put filter to the end of the list or so to avoid messing up Wordpress shortcodes
	// Default priority is 10
	add_filter('the_title','wwl_translate_title', 100); 
	add_filter('the_category','wwl_translate_title', 100);
	add_filter('the_content','wwl_translate_content', 100);
	if (get_option('wwl_hook_gettext')) {
		add_filter('gettext', 'wwl_gt');
	}
} else {
	$wwlex->needTranslation = false;
}
?>