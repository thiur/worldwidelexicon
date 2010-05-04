<?php

	/**
	 *  Helper Class to deal with Language Codes & Language Detection.
	 *  ===================================================================
	 *	@author 	Cesar Gonzalez (icesar@gmail.com)
	 *  @version 		1.0
	 *  @license		BSD
	 */

	class LanguageHelper
	{
		var $Text;

		//The 186 languages of ISO 639-1 according to fractilizer.ru
		private static $iso_languages = array( "aa" => "Afar", "ab" => "Abkhazian", "ae" => "Avestan", "af" => "Afrikaans", "ak" => "Akan", "am" => "Amharic", "an" => "Aragonese", "ar" => "Arabic", "as" => "Assamese", "av" => "Avaric", "ay" => "Aymara", "az" => "Azerbaijani", "ba" => "Bashkir", "be" => "Belarusian", "bg" => "Bulgarian", "bh" => "Bihari", "bi" => "Bislama", "bm" => "Bambara", "bn" => "Bengali", "bo" => "Tibetan", "br" => "Breton", "bs" => "Bosnian", "ca" => "Catalan", "ce" => "Chechen", "ch" => "Chamorro", "co" => "Corsican", "cr" => "Cree", "cs" => "Czech", "cu" => "Church Slavic", "cv" => "Chuvash", "cy" => "Welsh", "da" => "Danish", "de" => "German", "dv" => "Divehi", "dz" => "Dzongkha", "ee" => "Ewe", "el" => "Greek", "en" => "English", "eo" => "Esperanto", "es" => "Spanish", "et" => "Estonian", "eu" => "Basque", "fa" => "Persian", "ff" => "Fulah", "fi" => "Finnish", "fj" => "Fijian", "fo" => "Faroese", "fr" => "French", "fy" => "Western Frisian", "ga" => "Irish", "gd" => "Scottish Gaelic", "gl" => "Galician", "gn" => "Guarani", "gu" => "Gujarati", "gv" => "Manx", "ha" => "Hausa", "he" => "Hebrew", "hi" => "Hindi", "ho" => "Hiri Motu", "hr" => "Croatian", "ht" => "Haitian", "hu" => "Hungarian", "hy" => "Armenian", "hz" => "Herero", "ia" => "Interlingua", "id" => "Indonesian", "ie" => "Interlingue", "ig" => "Igbo", "ii" => "Sichuan Yi", "ik" => "Inupiaq", "io" => "Ido", "is" => "Icelandic", "it" => "Italian", "iu" => "Inuktitut", "ja" => "Japanese", "jv" => "Javanese", "ka" => "Georgian", "kg" => "Kongo", "ki" => "Kikuyu", "kj" => "Kwanyama", "kk" => "Kazakh", "kl" => "Kalaallisut", "km" => "Khmer", "kn" => "Kannada", "ko" => "Korean", "kr" => "Kanuri", "ks" => "Kashmiri", "ku" => "Kurdish", "kv" => "Komi", "kw" => "Cornish", "ky" => "Kirghiz", "la" => "Latin", "lb" => "Luxembourgish", "lg" => "Ganda", "li" => "Limburgish", "ln" => "Lingala", "lo" => "Lao", "lt" => "Lithuanian", "lu" => "Luba-Katanga", "lv" => "Latvian", "mg" => "Malagasy", "mh" => "Marshallese", "mi" => "Maori", "mk" => "Macedonian", "ml" => "Malayalam", "mn" => "Mongolian", "mr" => "Marathi", "ms" => "Malay", "mt" => "Maltese", "my" => "Burmese", "na" => "Nauru", "nb" => "Norwegian Bokmal", "nd" => "North Ndebele", "ne" => "Nepali", "ng" => "Ndonga", "nl" => "Dutch", "nn" => "Norwegian Nynorsk", "no" => "Norwegian", "nr" => "South Ndebele", "nv" => "Navajo", "ny" => "Chichewa", "oc" => "Occitan", "oj" => "Ojibwa", "om" => "Oromo", "or" => "Oriya", "os" => "Ossetian", "pa" => "Panjabi", "pi" => "Pali", "pl" => "Polish", "ps" => "Pashto", "pt" => "Portuguese", "qu" => "Quechua", "rm" => "Raeto-Romance", "rn" => "Kirundi", "ro" => "Romanian", "ru" => "Russian", "rw" => "Kinyarwanda", "sa" => "Sanskrit", "sc" => "Sardinian", "sd" => "Sindhi", "se" => "Northern Sami", "sg" => "Sango", "si" => "Sinhala", "sk" => "Slovak", "sl" => "Slovenian", "sm" => "Samoan", "sn" => "Shona", "so" => "Somali", "sq" => "Albanian", "sr" => "Serbian", "ss" => "Swati", "st" => "Southern Sotho", "su" => "Sundanese", "sv" => "Swedish", "sw" => "Swahili", "ta" => "Tamil", "te" => "Telugu", "tg" => "Tajik", "th" => "Thai", "ti" => "Tigrinya", "tk" => "Turkmen", "tl" => "Tagalog", "tn" => "Tswana", "to" => "Tonga", "tr" => "Turkish", "ts" => "Tsonga", "tt" => "Tatar", "tw" => "Twi", "ty" => "Tahitian", "ug" => "Uighur", "uk" => "Ukrainian", "ur" => "Urdu", "uz" => "Uzbek", "ve" => "Venda", "vi" => "Vietnamese", "vo" => "Volapuk", "wa" => "Walloon", "wo" => "Wolof", "xh" => "Xhosa", "yi" => "Yiddish", "yo" => "Yoruba", "za" => "Zhuang", "zh" => "Chinese", "zu" => "Zulu" );


		/**
		 *	Constructor
		 */
		function LanguageHelper() { }

		// Return the target language for this WWL proxy call, or an empty string if it can't be identified
		function detectTargetLanguage()
		{
			$serverhost = explode('.', $_SERVER["HTTP_HOST"]);
			$subdomain = $serverhost[0];

			// Check if it really is a subdomain
			if (isset($serverhost[2]) and ($serverhost[2] != "") ? $sub = $subdomain : $sub = "" );

			// Is the subdomain actually a 2-letter language code?
			if ( $this->isLanguageCode( $sub ) )
			{
				return $sub;
			}
			else
			{
				// 2 -- Look of the language code in a cookie
				// 3 -- Use the first language in the Accept Language header.

				return "es";
			}
		}


		// Detect the Source Language for this WWL proxy call.  Hint:it won't always be English.
		function detectSourceLanguage()
		{
			// Detect the site's primary language using: 
			// a) return value from /proxy API, 
			// b) xml:lang parameter in page header, 
			// c) use Google's translate API to detect language using text from page (optional)
			return "en";  // Dummy for now....how do I cleanly call the proxy from in here(??)
		}


		// Check if a given string (eg. from the subdomain) is a valid language code
		function isLanguageCode( $string )
		{
			if ( in_array( $string, $this->getLanguageCodes() ))
			{
				return true;
			}
			else
			{
				return false;
			}
		}


		// Removes any two-letter language code prepended to a URL string for translation
		function removeLanguageCode( $url_string )
		{
			return preg_replace('/\/\/[a-zA-Z][a-zA-Z]\./', '//', $url_string);
		}


		// Here are all the language codes in an array...there's probably a better way to do this.
		public function getLanguageCodes()
		{
			return array( 	"aa", "ab", "ae", "af", "ak", "am", "an", "ar", "as", "av", "ay", "az", "ba", "be", "bg", "bh", "bi", "bm", "bn", "bo", "br", "bs", 
							"ca", "ce", "ch", "co", "cr", "cs", "cu", "cv", "cy", "da", "de", "dv", "dz", "ee", "el", "en", "eo", "es", "et", "eu", "fa", "ff", 
							"fi", "fj", "fo", "fr", "fy", "ga", "gd", "gl", "gn", "gu", "gv", "ha", "he", "hi", "ho", "hr", "ht", "hu", "hy", "hz", "ia", "id", 
							"ie", "ig", "ii", "ik", "io", "is", "it", "iu", "ja", "jv", "ka", "kg", "ki", "kj", "kk", "kl", "km", "kn", "ko", "kr", "ks", "ku", 
							"kv", "kw", "ky", "la", "lb", "lg", "li", "ln", "lo", "lt", "lu", "lv", "mg", "mh", "mi", "mk", "ml", "mn", "mr", "ms", "mt", "my", 
							"na", "nb", "nd", "ne", "ng", "nl", "nn", "no", "nr", "nv", "ny", "oc", "oj", "om", "or", "os", "pa", "pi", "pl", "ps", "pt", "qu", 
							"rm", "rn", "ro", "ru", "rw", "sa", "sc", "sd", "se", "sg", "si", "sk", "sl", "sm", "sn", "so", "sq", "sr", "ss", "st", "su", "sv", 
							"sw", "ta", "te", "tg", "th", "ti", "tk", "tl", "tn", "to", "tr", "ts", "tt", "tw", "ty", "ug", "uk", "ur", "uz", "ve", "vi", "vo", 
							"wa", "wo", "xh", "yi", "yo", "za", "zh", "zu" );
		}
		
		
		// This public function translate a 2-letter language code into its corresponding language name in English.
		public static function getLanguageName( $code ) {
				
			if ( array_key_exists($code, self::$iso_languages) ) { return self::$iso_languages[$code]; }
			else { return ""; }

		}

	}

?>
