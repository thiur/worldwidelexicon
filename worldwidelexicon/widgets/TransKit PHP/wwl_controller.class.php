<?php
/*
 *	WWLController
 * 
 *	@package		wwlphp
 *  @author 		Alexey Gavrilov
 * 					
 *  @version 		1.0
 *  @license		BSD
 */
class WWLController {
	var $rtl = Array('ar', 'he', 'ur', 'fa');
	var $languages = Array(
		'af'=>'Afrikaans',
		'sq'=>'Albanian',
		'ar'=>'Arabic',
		'hy'=>'Armenian',
		'as'=>'Assamese',
		'az'=>'Azeri',
		'eu'=>'Basque',
		'be'=>'Belarusian',
		'bn'=>'Bengali',
		'bg'=>'Bulgarian',
		'ca'=>'Catalan',
		'zh'=>'Chinese',
		'hr'=>'Croatian',
		'cs'=>'Chech',
		'da'=>'Danish',
		'div'=>'Divehi',
		'nl'=>'Dutch',
		'en'=>'English',
		'et'=>'Estonian',
		'fo'=>'Faeroese',
		'fa'=>'Farsi',
		'fi'=>'Finnish',
		'fr'=>'French',
		'mk'=>'FYRO Macedonian',
		'gd'=>'Gaelic',
		'ka'=>'Georgian',
		'de'=>'German',
		'el'=>'Greek',
		'gu'=>'Gujarati',
		'he'=>'Hebrew',
		'hi'=>'Hindi',
		'hu'=>'Hungarian',
		'is'=>'Icelandic',
		'id'=>'Indonesian',
		'it'=>'Italian',
		'ja'=>'Japanese',
		'kk'=>'Kazakh',
		'ko'=>'Korean',
		'kz'=>'Kyrgyz',
		'lv'=>'Latvian',
		'lt'=>'Lithuanian',
		'ms'=>'Malay',
		'ml'=>'Malayalam',
		'mt'=>'Maltese',
		'mr'=>'Marathi',
		'mn'=>'Mongolian',
		'ne'=>'Nepali',
		'no'=>'Norwegian (Bokmal)',
		'nn'=>'Norwegian (Nynorsk)',
		'or'=>'Oriya',
		'pl'=>'Polish',
		'pt'=>'Portuguese',
		'pa'=>'Punjabi',
		'rm'=>'Rhaeto-Romanic',
		'ro'=>'Romanian',
		'ru'=>'Russian',
		'sa'=>'Sanskrit',
		'sr'=>'Serbian',
		'sk'=>'Slovak',
		'ls'=>'Slovenian',
		'sb'=>'Sorbian',
		'es'=>'Spanish',
		'sx'=>'Sutu',
		'sw'=>'Swahili',
		'sv'=>'Swedish',
		'ta'=>'Tamil',
		'tt'=>'Tatar',
		'te'=>'Telugu',
		'th'=>'Thai',
		'ts'=>'Tsonga',
		'tn'=>'Tswana',
		'tr'=>'Turkish',
		'uk'=>'Ukrainian',
		'ur'=>'Urdu',
		'uz'=>'Uzbek',
		'vi'=>'Vietnamese',
		'xh'=>'Xhosa',
		'yi'=>'Yiddish',
		'zu'=>'Zulu'
	);
	var $nativeNames = array(
		"ab"=>"Аҧсуа",
		"aa"=>"Afaraf",
		"af"=>"Afrikaans",
		"ak"=>"Akan",
		"sq"=>"Shqip",
		"am"=>"አማርኛ",
		"ar"=>"العربية",
		"an"=>"Aragonés",
		"hy"=>"Հայերեն",
		"as"=>"অসমীয়া",
		"av"=>"авар мацӀ",
		"ae"=>"Avesta",
		"ay"=>"Aymar aru",
		"az"=>"Azərbaycan dili",
		"bm"=>"Bamanankan",
		"ba"=>"Башҡорт теле",
		"eu"=>"Euskara",
		"be"=>"Беларуская",
		"bn"=>"বাংলা",
		"bh"=>"भोजपुरी",
		"bi"=>"Bislama",
		"bs"=>"Bosanski",
		"br"=>"Brezhoneg",
		"bg"=>"Български",
		"my"=>"ဗမာစာ",
		"ch"=>"Chamoru",
		"ce"=>"Нохчийн мотт",
		"ny"=>"chiCheŵa",
		"zh"=>"中文",
		"cv"=>"Чӑваш чӗлхи",
		"kw"=>"Kernewek",
		"co"=>"Corsu",
		"cr"=>"ᓀᐦᐃᔭᐍᐏᐣ",
		"hr"=>"Hrvatski",
		"cs"=>"Čeština",
		"da"=>"Dansk",
		"dv"=>"ދިވެހި",
		"nl"=>"Nederlands",
		"dz"=>"རྫོང་ཁ",
		"en"=>"English",
		"eo"=>"Esperanto",
		"et"=>"Eesti",
		"ee"=>"Eʋegbe",
		"fo"=>"Føroyskt",
		"fj"=>"vosa Vakaviti",
		"fi"=>"Suomi",
		"fr"=>"Français",
		"ff"=>"Fulfulde",
		"gl"=>"Galego",
		"ka"=>"ქართული",
		"de"=>"Deutsch",
		"el"=>"Ελληνικά",
		"gn"=>"Avañe'ẽ",
		"gu"=>"ગુજરાતી",
		"ht"=>"Kreyòl ayisyen",
		"ha"=>"Hausa",
		"he"=>"עברית",
		"hz"=>"Otjiherero",
		"hi"=>"हिन्दी",
		"ho"=>"Hiri Motu",
		"hu"=>"Magyar",
		"ia"=>"Interlingua",
		"id"=>"Bahasa Indonesia",
		"ga"=>"Gaeilge",
		"ig"=>"Asụsụ Igbo",
		"ik"=>"Iñupiaq",
		"io"=>"Ido",
		"is"=>"Íslenska",
		"it"=>"Italiano",
		"iu"=>"ᐃᓄᒃᑎᑐᑦ",
		"ja"=>"日本語",
		"jv"=>"basa Jawa",
		"kl"=>"Kalaallisut",
		"kn"=>"ಕನ್ನಡ",
		"kr"=>"Kanuri",
		"kk"=>"Қазақ тілі",
		"km"=>"ភាសាខ្មែរ",
		"ki"=>"Gĩkũyũ",
		"rw"=>"Ikinyarwanda",
		"ky"=>"Кыргыз тили",
		"kv"=>"Коми кыв",
		"kg"=>"KiKongo",
		"ko"=>"한국어",
		"ku"=>"Kurdî",
		"kj"=>"Kuanyama",
		"la"=>"Latina",
		"lb"=>"Lëtzebuergesch",
		"lg"=>"Luganda",
		"li"=>"Limburgs",
		"ln"=>"Lingála",
		"lo"=>"ພາສາລາວ",
		"lt"=>"Lietuvių",
		"lv"=>"Latviešu",
		"gv"=>"Gaelg",
		"mk"=>"Македонски",
		"mg"=>"Malagasy fiteny",
		"ml"=>"മലയാളം",
		"mt"=>"Malti",
		"mi"=>"te reo Māori",
		"mr"=>"मराठी",
		"mh"=>"Kajin M̧ajeļ",
		"mn"=>"Монгол",
		"na"=>"Ekakairũ Naoero",
		"nv"=>"Diné bizaad",
		"nb"=>"Norsk bokmål",
		"nd"=>"isiNdebele",
		"ne"=>"नेपाली",
		"ng"=>"Owambo",
		"nn"=>"Norsk nynorsk",
		"no"=>"Norsk",
		"ii"=>"ꆈꌠ꒿ Nuosuhxop",
		"nr"=>"isiNdebele",
		"oc"=>"Occitan",
		"oj"=>"ᐊᓂᔑᓈᐯᒧᐎᓐ",
		"cu"=>"ѩзыкъ словѣньскъ",
		"om"=>"Afaan Oromoo",
		"or"=>"ଓଡ଼ିଆ",
		"os"=>"Ирон æвзаг",
		"pi"=>"पाऴि",
		"fa"=>"فارسی",
		"pl"=>"Polski",
		"ps"=>"پښتو",
		"pt"=>"Português",
		"qu"=>"Runa Simi",
		"rm"=>"rumantsch grischun",
		"rn"=>"kiRundi",
		"ru"=>"Русский",
		"sa"=>"संस्कृतम्",
		"sc"=>"sardu",
		"se"=>"Davvisámegiella",
		"sm"=>"gagana fa'a Samoa",
		"sg"=>"yângâ tî sängö",
		"sr"=>"Српски",
		"gd"=>"Gàidhlig",
		"sn"=>"chiShona",
		"si"=>"සිංහල",
		"sk"=>"Slovenčina",
		"sl"=>"Slovenščina",
		"so"=>"Soomaaliga",
		"st"=>"Sesotho",
		"es"=>"Español",
		"su"=>"Basa Sunda",
		"sw"=>"Kiswahili",
		"ss"=>"SiSwati",
		"sv"=>"Svenska",
		"ta"=>"தமிழ்",
		"te"=>"తెలుగు",
		"th"=>"ไทย",
		"ti"=>"ትግርኛ",
		"bo"=>"བོད་ཡིག",
		"tk"=>"Türkmen",
		"tl"=>"Tagalog",
		"tn"=>"Setswana",
		"to"=>"faka Tonga",
		"tr"=>"Türkçe",
		"ts"=>"Xitsonga",
		"tw"=>"Twi",
		"ty"=>"Reo Mā`ohi",
		"uk"=>"Українська",
		"ur"=>"اردو",
		"ve"=>"Tshivenḓa",
		"vi"=>"Tiếng Việt",
		"vo"=>"Volapük",
		"wa"=>"Walon",
		"cy"=>"Cymraeg",
		"wo"=>"Wollof",
		"fy"=>"Frysk",
		"xh"=>"isiXhosa",
		"yi"=>"ייִדיש",
		"yo"=>"Yorùbá",
		"za"=>"Saɯ cueŋƅ",
		"zu"=>"isiZulu"
	);
	var $cacheProviders = array();
	var $translationProviders = array();
	
	var $targetLanguage = "";
	var $sourceLanguage =  "";
	var $maxChunk = 512;
	var $addDecorations = true;
	var $needTranslation = false;
	
	var $timeout = 10; // in seconds 
	var $cacheTTL = 86400;
	var $chunksCache = array();
	var $logProgress = true;
	var $lastError = "";
	
	var $config = array(
		'mt' => false,
		'vol' => false,
		'pro' => false
	);
	
	function __construct($sl = '', $tl = '', $basePath = '/tmp/') {
		$this->setTargetLanguage($tl);
		$this->setSourceLanguage($sl);
		$this->logPath = $basePath."/wwlex-cache/log.txt";		
		if (preg_match("/(png|ico|gif|jpg|jpeg)$/i", $_SERVER["REQUEST_URI"])) {
			$this->logProgress = false;
		}
		$this->log("Logging started: ".$_SERVER["REQUEST_URI"], true);
		$this->startTime = time();
	}			
	function WWLController($sl = '', $tl = '', $basePath = '/tmp/') {
		$this->__construct($sl, $tl, $basePath);		
	}
	/*
	 * TODO: Implement explicit priority. For now the providers will be used in the order they were added
	 */
	function addCacheProvider($obj, $priority = 1.0){
		// Validate that cache provider implements all required methods
		if (!is_object($obj) || 
			!method_exists($obj, "set") ||
			!method_exists($obj, "get") ||
			!method_exists($obj, "verify") ||
			!method_exists($obj, "clear")
			) {
			$this->lastError = "Invalid cache provider";
			return false;
		}
		if (!$obj->verify()){
			$this->lastError = $obj->error;
			return false;
		}
		$obj->ttl = $this->cacheTTL;
		$this->cacheProviders[] = array(
			"worker" => $obj,
			"priority" => $priority
		);
		return true;
	}
	function addTranslationProvider($obj, $priority = 1.0){
		// Validate that cache provider implements all required methods
		if (!is_object($obj) || 
			!method_exists($obj, "get") ||
			!method_exists($obj, "verify")
			) {
			$this->lastError = "Invalid translation provider";
			return false;
		}
		if (!$obj->verify()){
			$this->lastError = $obj->error;
			return false;
		}
		$obj->targetLanguage = $this->targetLanguage;
		$obj->sourceLanguage = $this->sourceLanguage;
		$this->translationProviders[] = array(
			"worker" => $obj,
			"priority" => $priority
		);
		return true;
	}
	function setCacheTTL($ttl) {
		$this->cacheTTL = $ttl;
		foreach ($this->cacheProviders as $cacher){
			$cacher["worker"]->ttl = $this->cacheTTL;
		}
	}
	function clearCache(){
		foreach ($this->cacheProviders as $cacher){
			$cacher["worker"]->clear();
		}
	}
	/*
	 * TODO: Use JSON to store cache. Pipe-separated format is not safe
	 */
	function saveToCache($st, $tt, $ttl = 0){
		$key = md5($this->sourceLanguage . $this->targetLanguage . $st);
		$data = $tt."|".$st."|".$this->sourceLanguage."|".$this->targetLanguage."|".$this->meta["username"]."|".$this->meta["mtengine"];
		foreach ($this->cacheProviders as $cacher){
			$cacher["worker"]->set($key, $data, $ttl);
		}
	}
	function getCached($st){
		$key = md5($this->sourceLanguage . $this->targetLanguage . $st);
		foreach ($this->cacheProviders as $cacher){
			if ($res = $cacher["worker"]->get($key)) {
				$res = explode("|", $res);
				$this->log("res/".get_class($cacher["worker"])."/ = ".$res[0]);
				// 0 -- translated string
				// 1 -- source string
				// 2 -- source language
				// 3 -- target language
				// 4 -- username
				// 5 -- mtengine
				$this->meta = array(
					"username" => isset($res[4]) ? $res[4] : "",
					"mtengine" => isset($res[5]) ? $res[5] : ""
				);
				return $res[0];
			}
		}
		$this->meta = array("mtengine" => "google", "username" => "");
		return "";
	}	
	function translate($st){
		if ($res = $this->getCached($st)){
			return $res;
		}
		foreach ($this->translationProviders as $translator){
			if ($translator["worker"]->canTranslate($this->config)) {
				$this->log("Trying ".get_class($translator["worker"]));
			}
			$res = $translator["worker"]->get($st, $this->config);
			$this->meta = $translator["worker"]->meta;
			$this->log("url: ".$translator["worker"]->lastUrl);
			
			if ($res){
				$this->saveToCache($st, $res);
				$this->log("res/".get_class($translator["worker"])."/ = ".$res);
				$this->log("username: ".$translator["worker"]->meta["username"]);
				$this->log("mtengine: ".$translator["worker"]->meta["mtengine"]);
				return $res;
			}
		}
		$this->saveToCache($st, $st);
		$this->log("res/not-translated/ = ".$st);
		return "";
	}
	function updateTranslation($st, $tt){
		$this->log("Submitting translation");
		$this->log("Source: ".$st);
		$this->log("Translated: ".$tt);
		$this->meta = array(
			"username" => $this->config["username"],
			"mtengine" => ""
		);
		$this->saveToCache($st, $tt);
		foreach ($this->translationProviders as $translator){
			if (!method_exists($translator["worker"], "submit")){
				continue;
			}
			$translator["worker"]->submit($st, $tt, $this->config);
			$this->log("url: ".$translator["worker"]->lastUrl);
		}
	}	
	function setSourceLanguage($lang){
		$lang = explode("-", $lang);
		$lang = $lang[0];
		if ($lang == $this->sourceLanguage){
			return;
		}
		$this->sourceLanguage = $lang;
		foreach ($this->translationProviders as $translator){
			$translator["worker"]->sourceLanguage = $lang;
		}
		$this->needTranslation = $this->isTranslationNeeded();
		$this->log("Source language set to: ".$lang);
	}
	
	function setTargetLanguage($lang){
		$lang = explode("-", $lang);
		$lang = $lang[0];
		if ($lang == $this->targetLanguage){
			return;
		}
		$this->targetLanguage = $lang;
		foreach ($this->translationProviders as $translator){
			$translator["worker"]->targetLanguage = $lang;
		}
		$this->needTranslation = $this->isTranslationNeeded();
		$this->log("Target language set to: ".$lang);
	}
	
	function detectUserLanguage() {
		$lang = isset($_GET["tl"]) ? $_GET["tl"]: false;
		if (!$lang) {
			$lang = isset($_POST["tl"]) ? $_POST["tl"]:false;
		}
		if (!$lang) {
			$lang = isset($_COOKIE["tl"]) ? $_COOKIE["tl"]:false;
		}
		if (!$lang) {
			$lang = isset($_SERVER["HTTP_ACCEPT_LANGUAGE"]) ? $this->parseLanguageHeader($_SERVER["HTTP_ACCEPT_LANGUAGE"]): "en";
		}
		setcookie("tl", $lang, 0, '/'); // save to session cookie
		$this->log("Detected user language: ".$lang);
		return $lang;
	}
		
	function isTranslationNeeded() {
		if ($this->targetLanguage  === $this->sourceLanguage) {
			$this->log("Translation is not needed");
			return false;
		}
		if (!$this->config["mt"] && !$this->config["pro"] && !$this->config["vol"]) {
			$this->log("Translation is disabled for this pair");
			return false;
		}
		$this->log("Translation will be performed");
		return true;
	}
	/* Re-load this method */
	function getSourceLanguage() {
		return "en";
	}
	/* Re-load this method */
	function canTranslate() {
		return $this->config["vol"];
	}
	function languageName($code, $native = true) {
		if ($native && isset($this->nativeNames[$code])) {
			return $this->nativeNames[$code];
		} else {
			return $this->languages[$code];
		}
	}
	function targetLanguageName() {
		return $this->languageName($this->targetLanguage);
	}
	function sourceLanguageName() {
		return $this->languageName($this->sourceLanguage);
	}
	function moveTags($source, $target) {
		global $gwwl_savedTags;
		$cnt = preg_match_all('/<([a-z]+)(.*?)>/i', $source, $gwwl_savedTags);
		return preg_replace_callback('/<([a-z]+)>/i', "gwwl_replace_inline_tags", $target);
	}
	function translateSentence($str, $decorate = false) {
		if (!$this->needTranslation) {
			return $str;
		}
		// Is it safe to trim here?
		$str = trim($str);
		
		// if we run out of time return local results only
		if (time() - $this->startTime > $this->timeout) {
			$this->log("getCached('".$str."')");
			$res = $this->getCached($str);
			if (!$res) {
				$this->log("res/Not in cache/");
			}
		} else {
			$this->log("get('".$str."')");
			$res = $this->translate($str);
		}
		$res = (strlen($res) > 0) ? $res : $str;
		if ($decorate) {
			$chunkId = $this->makeId();
		
			$out = '<span class="wwl-translated-fragment">'.$res.'</span>';
			$out.= '<span class="wwl-original-fragment wwl-hide">'.$chunkId.'</span>';
			
			$this->chunksCache[$chunkId] = array("original" => $str, "translated" => $res, "meta" => $this->meta);
		} else {
			$out = $res;
		}
		return $out;
	}
	function translateContent($str, $decorate = false) {
		if (!$this->needTranslation) {
			return $str;
		}
		$this->addDecorations = $decorate;
		return $this->decompose($str);
	}
	function translateText($str) {
		if (strlen($str) <= $this->maxChunk) {
			$out = $this->translateSentence($str, $this->addDecorations);
		} else {
			// split longer text by sentences
			$splitted = preg_split('/((?:\.|!|\?)(?:\s+|$))/', $str, -1, PREG_SPLIT_NO_EMPTY | PREG_SPLIT_DELIM_CAPTURE);
		
			if (sizeof($splitted) > 2) {
				$out = "";
				$val = $splitted[0].$splitted[1];
				for ($i = 1; $i < sizeof($splitted)/2; $i++) {
					
					if (strlen($val.$splitted[2*$i].$splitted[2*$i + 1]) > $this->maxChunk) {
						$out.= $this->translateText($val);
						$val = $splitted[2*$i].$splitted[2*$i + 1];
					} else {
						$val.= $splitted[2*$i].$splitted[2*$i + 1];
					}
				}
				$out.= $this->translateText($val);
			} else {
				//split by words
				//echo("<!--".$str."-->");
				$splitted = preg_split('/(\s+|[.!?]+)/', $str, -1, PREG_SPLIT_NO_EMPTY | PREG_SPLIT_DELIM_CAPTURE);
				if (sizeof($splitted) > 2) {
					
					$out = "";
					$val = $splitted[0].$splitted[1];
					for ($i = 1; $i < sizeof($splitted)/2; $i++) {
						
						if (strlen($val.$splitted[2*$i].$splitted[2*$i + 1]) > $this->maxChunk) {
							$out.= $this->translateText($val);
							$val = $splitted[2*$i].$splitted[2*$i + 1];
						} else {
							$val.= $splitted[2*$i].$splitted[2*$i + 1];
						}
					}
					$out.= $this->translateText($val);
				} else {
				
					//no good -- string can't be reasonably splitted and still longer than 
					//max chunck -- just send it back
					$out = substr($str, 0, $this->maxChunk);
				}
			}
		}
		return $out;
	}
	function decompose($s) {
		global $gwwl_savedTags;
		$src = $s;
		// Group A: a, em, strong, b, i, span, img, sub, sup  -- inline tags
		$ATags = array("a", "em", "strong", "i", "b", "img", "sub", "sup", "span");
		// Group B: style, script -- should be excluded with all content inside
		$BTags = array("style", "script");
		// Group C: p, div, h* -- all other tags

		// 1. Save Group B, and replace it with markers (~)
		// 2. Save Group A, and replace it with markers (^)
		// 3. Save Group C, replace with markers (#)
		// 4. Explode result using # markers
		$reA = '/(<(?:'.implode('|', $ATags).').*?>|<\/(?:'.implode('|', $ATags).').*?>)/i';
		$reB = '/<(?:'.implode('|', $BTags).').*?>.*<\/(?:'.implode('|', $BTags).').*?>/i';
		$reC = '/<.*?>/i';
		//1. Replace each source string with translated
		//2. Replace # markers with Group C
		//3. Replace ^ markers with Group A
		//4. Replace ~ markers with Group B
		$matches = array();
		$matches["B"] = array();
		$numMatches = preg_match_all($reB, $s, $matches["B"]);
		$s = preg_replace($reB, "~", $s);
		$matches["B"] = $matches["B"][0];
		
		$matches["A"] = array();
		$numMatches = preg_match_all($reA, $s, $matches["A"]);
		$s = preg_replace($reA, "^", $s);
		$matches["A"] = $matches["A"][0];
		
		$matches["C"] = array();
		$numMatches = preg_match_all($reC, $s, $matches["C"]);
		$matches["C"] = $matches["C"][0];
		
		$s = preg_replace($reC, "##", $s);
		$ssave = $s;
		$s = preg_split('/(##)+/', $s, -1, PREG_SPLIT_NO_EMPTY);
		$count = 0;
		foreach ($s as $index=>$value) {
			if (($pos = strpos($value, "^")) === false) {
				continue;
			}
			$value = explode("^", $value);
			$s[$index] = "";
			for ($i = 0; $i < sizeof($value) - 1; $i++) {
				$s[$index].= $value[$i].$matches["A"][$count];
				$count++;
			}
			$s[$index].= $value[sizeof($value) - 1];
		}
		$out = array();
		foreach ($s as $index=>$value) {
			if (trim(strip_tags($s[$index])) != "") {
		
				$gwwl_savedTags = array();
				// Find is there are any inline tags and save them
				$cnt = preg_match_all('/<([a-z]+)(.*?)>/i', $value, $gwwl_savedTags);
				// Replace inline tags with shortened versions
				$value = preg_replace('/<([a-z]+)(.*?)>/i', "<$1>", $value);
				// Translate modified text
				$out[$index] = $this->translateText($value);
				// Any tags were saved
				if ($cnt) {
					// Put them back now
					$out[$index] = preg_replace_callback('/<([a-z]+)>/i', "gwwl_replace_inline_tags", $out[$index]);
				}
			} else {
				unset($s[$index]);
			}
		}

		$s = str_replace($s, $out, $src);
		return $s;
	}
	function languagesJSON() {
		return $this->jsonEncode($this->languages);
	}
	function chunksJSON() {
		$out = $this->jsonEncode($this->chunksCache);
		$out = str_replace("\r\n", "\n", $out);
		$out = str_replace("\r", "\n", $out);
		$out = str_replace("\n", "\\n", $out);
		return $out;
	}
	function jsonDecode($input) {
		$json = new Services_JSON(SERVICES_JSON_LOOSE_TYPE);
		return $json->decode($input);
	}
	function jsonEncode($value) {
		$json = new Services_JSON(SERVICES_JSON_IN_ARR);
		return $json->encode($value);
	}
	function makeId($len = 32) {
		list($usec, $sec) = explode(' ', microtime());
		$seed =  (float) $sec + ((float) $usec * 100000);
	
		srand($seed);
	
		$feed = "abcdefghijklmnopqrstuvwxyz0123456789";
		$out = "";
		for ($i=0;$i<$len;$i++) {
			$out .= substr($feed, rand(0, strlen($feed)-1), 1);
		}
		return $out;
	}
	function parseLanguageHeader($header) {
		$parts = explode(",", $header);
		$parts = explode(";", $parts[0]);
		$parts = explode("-", $parts[0]); // split pairs like 'en-us' or 'pt-br'
		return $parts[0];
	}	
	function isTargetRtl() {			
		return in_array($this->targetLanguage, $this->rtl);
	}
	function getTranslationUrl($lang){
		$url = $_SERVER["REQUEST_URI"];
		if (!strstr($url, "?")) {
			return $url."?tl=".$lang;
		}
		if ($_GET["tl"]) {
			return str_replace("tl=".$_GET["tl"], "tl=".$lang, $url);
		}
		return $url."&tl=".$lang;
	}
	function log($txt, $reset = false){
		if (!$this->logProgress) return;
		$f = @fopen($this->logPath, $reset ? "w+" : "a+");
		if (!$f) {
			return;
		}
		fwrite($f, date("m/d/y H:i:s")."\t".$txt."\n");
		fflush($f);
		fclose($f);
	}
}
/*
*	The function below is only used ONCE in wwlex::decompose method.
*	Replace shortened inline tags with full versions previously saved
*	to $gwwl_savedTags global var. This is ugly.
*	A better way would be to use anonymous function but it's only available in PHP 5.3.0+
*/
function gwwl_replace_inline_tags($matches) {
	global $gwwl_savedTags;
	foreach ($gwwl_savedTags[1] as $i=>$tag) {
		if ($tag == $matches[1]) {
			$res = $gwwl_savedTags[0][$i];
			unset($gwwl_savedTags[0][$i]);
			unset($gwwl_savedTags[1][$i]);
			return $res;
		}
	}
}
?>