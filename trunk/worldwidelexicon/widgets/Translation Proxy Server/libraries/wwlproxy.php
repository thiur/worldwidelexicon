<?php

/**
 *	Takes a passed in URL, parses the HTML, translates the text using WWL, and displays the URL in the target language.
 *
 */
class Wwlproxy extends Wwl {

	private $targetUrl;
	private $source_html;
	private $page_settings;
	private $routeAllLinks;
	private $curl;
	private $doc;
	private $timeout = 20;  // in seconds
	private $z = 0;			// an index
	
	function __construct( $sl, $tl, $url ) {

		
		if (empty($sl) || empty($tl) || empty($url)) {
			log_message("error", "WWL Proxy initialization error - required fields not set.");
			die("WWL Proxy initialization error - required fields not set.");
		}
		
		
		parent::__construct($sl, $tl);

		// The simple stuff
		$this->targetUrl				= $url;
		$this->startTime 				= time();
		$this->curl 					= new Curl();
		$this->doc 						= new DOMDocument();
		$this->routeAllLinks			= false;

		
		// Get the html content of the target site
		$this->source_html				= $this->curl->simple_get( $this->targetUrl->toString() );
		log_message('debug', "Content type: ".$this->curl->info["content_type"]);
		if (!strstr($this->curl->info["content_type"], "text")){
			log_message('debug', "Not acceptable content-type, redirecting to the URL");
			header("Location: ".$this->targetUrl->toString());
			die();
		}

		// Let's use PHPs very decent built in DOMDocument class to parse the HTML.  Suppress errors.
		@$this->doc->loadHTML($this->source_html);
		
		//echo $this->targetUrl->toString();
		
		// If the document is somehow null (it's happened), then display the original HTML
		if ( $this->doc->documentElement == NULL ) {
			echo $this->source_html;
			exit;
		}

		// DEBUG: Let's walk the treeee...
		// $this->walkDom($this->doc);

		// Let's get the setting for that proxy object from (1) the WWL & (2) the page meta tags
		$this->getProxySettings();

		// If we're not supposed to translate this page, just display it (or redirect?)
		if ( $this->page_settings->getTranslate() == 'n')
		{
			echo $this->source_html;
			exit; 
		}
		
		// And let's add the language selector if one is required through a shortcode
		$this->addLanguageSelector();
		
		// DEBUG: What are the page setting?
		// $this->page_settings->printSettings();		

		// Are we creating a local File Cache?
		if ( FILE_CACHE_ENABLED && class_exists("FileCache")) {
			$this->cacher = new FileCache( CACHE_PATH );
			// disable file cache unless configured properly
			if (!$this->cacher->verifyCacheDir()) {
				log_message('error', $this->cacher->error );
				$this->cacher = null;
			} else {
				log_message('debug', "File cache initialized successfully.");
			}
		}
	}

	function Wwlproxy( $sl="", $tl="", $url="") {
		$this-->__construct( $sl, $tl, $url);
	}


	// Carry out the translation process, as requested.
	function translate()
	{
		// Turn off inline editing for now.
		// $this->page_settings->setAllowEdit('n');
		
		// Correctly set the language and the language direction for the page
		$this->_fixLanguageDefinition();
		
		// Next, let's fix the URLs of the embedded assets.
		$this->_fixTagProperty('link', 'href' );
		$this->_fixTagProperty('script', 'src' );
		$this->_fixTagProperty('img', 'src' );
		$this->_fixTagProperty('td', 'background' );

		// Argh, why are ppl using @imports?  Let's fix those too.
		$this->_fixCSSImport();

		// And now, let's fix the internal and external links.
		$this->_fixLinks();

		// Call the recursive translation function on the root node of the DOM Document
		$source_snippets = array();
		$this->buildSourceArray( $this->doc->documentElement, $source_snippets );
		log_message("debug", "Size: " . sizeof($source_snippets) . " source snippets.");
		
		// DEBUG Did we loose the space?
		//echo "<hr />";
		//foreach ($source_snippets as $str) { echo "|".$str."|<br />"; }
		
		// $source_snippets now holds a hash table of the strings to translate, get them all translated in parallel, and pass in all the page-wide settings.
		$translated_snippets = $this->multiget( $source_snippets, 
												$this->targetUrl->getDomain(), 
												$this->page_settings->getAllowMachine(), 
												$this->page_settings->getAllowAnonymous(), 
												$this->page_settings->getRequireProfessional()
/*
												'', 
												$this->page_settings->getLSP(), 
												$this->page_settings->getLSPUsername(), 
												$this->page_settings->getLSPPassword(), 
												''
*/ 
												);

		log_message("debug", "Size: " . sizeof($translated_snippets) . " translated snippets returned by multiget().");

		/* DEBUG
		$translated_snippets = array( $source_snippets, $this->targetUrl->getDomain(), $this->page_settings->getAllowMachine(), $this->page_settings->getAllowAnonymous(), $this->page_settings->getRequireProfessional(), '', $this->page_settings->getLSP(), $this->page_settings->getLSPUsername(), $this->page_settings->getLSPPassword(), '' );
		echo "<pre>"; print_r($translated_snippets); echo "</pre><br/>"; die();
		*/
		
		// Next, iterate recursively one more time, updating the value of all the text nodes.
		$this->translateNodes( $this->doc->documentElement, $translated_snippets, $this->page_settings );

		// Lastly, let's embed the JS & CSS needed for user edits.
		// I probably need another boolean which says "somewhere on this page, editing was enabled" because
		// the page-wide allow_edit could be wrong. (Do it last so it doesn't get messed with.)
		if ( true ) {
			$this->_makeEditable();
		}
	}

	
	// Output the HTML of the translated file to the screen.
	function output()
	{
		// Lastly, save the DOM doucument as HTML and output it to the browser.
		$translated_html = $this->doc->saveHTML();
		echo $translated_html;
		
	}
	
	
	// Setting whether to route links through the proxy
	function setLinkRouting( $bool ) { $this->routeAllLinks = $bool; }
	
	// Connect to the proxy service and get the settings for the current URL
	function getProxySettings() 
	{
		$domain	= $this->targetUrl->getHost();
		$url 	= Wwl::server() . "/proxy/" . $this->targetLanguage . "." . $domain;
		
		$return_settings = array();
		
		// First, query the WWL for the parent setting associated with this domain.
		$response = $this->curl->simple_get( $url );
		
		// Parse the response (sent as mulitple lines of key=value\n)
		$response = explode("\n", $response);
		reset($response);
		
		foreach ( $response as $line ) {
			if ( !empty($line) ) {
				$item = explode( "=", $line);
				$return_settings[ trim($item[0]) ] = trim($item[1]);
			}
		}
		
		// Save the "proxy-wide settings" to this object.
		$this->page_settings = new WwlSettings($return_settings);

		// Second, look at the on-page meta tags to determine if this particular URL has any different settings.
		$meta_tags = $this->doc->getElementsByTagname( 'meta' );
		
		// Now loop through each meta tag and determine if it is a WWL setting.
		foreach( $meta_tags as $node ) 
		{
			if ( !empty($node->attributes->getNamedItem('name')->nodeValue) && !empty($node->attributes->getNamedItem('content')->nodeValue) ) 
			{
				$name = $node->attributes->getNamedItem('name')->nodeValue;
				$value = $node->attributes->getNamedItem('content')->nodeValue;

				switch($name) {
				
					case "allow_machine": 
						if ($value == "y") 		{ $this->page_settings->setAllowMachine('y'); }
						elseif ($value == "n") 	{ $this->page_settings->setAllowMachine('n'); }
						break;

					case "allow_anonymous": 
						if ($value == "y") 		{ $this->page_settings->setAllowAnonymous('y'); }
						elseif ($value == "n") 	{ $this->page_settings->setAllowAnonymous('n'); }
						break;

					case "allow_edit": 
						if ($value == "y") 		{ $this->page_settings->setAllowEdit('y'); }
						elseif ($value == "n") 	{ $this->page_settings->setAllowEdit('n'); }
						break;

					case "require_professional":
						if ($value == "y") 		{ $this->page_settings->setRequireProfessional('y'); }
						if ($value == "n") 		{ $this->page_settings->setRequireProfessional('n'); }
						break;

					case "languages":
						$this->page_settings->setLanguages($value);
						break;

					case "machine_translation_languages":
						$this->page_settings->setMachineLanguages($value);
						break;
					
					case "community_translation_languages":
						$this->page_settings->setTranslationLanguages($value);
						break;
					
					case "professional_translation_languages":
						$this->page_settings->setProfessionalLanguages($value);
						break;
					
					case "lsp":
						$this->page_settings->setLSP(trim($value));
						break;
						
					case "lspusername":
						$this->page_settings->setLSPUsername(trim($value));
						break;
						
					case "lsppw":
						$this->page_settings->setLSPPassword(trim($value));
						break;
						
				}
			}
		}
		
		return $return_settings;
	}
	

	// Recursively build the array of snippets of text within this document that need to be translated.
	function buildSourceArray( &$node, &$snippets ) 
	{					
		// Do we even care to translate this node? Only translate none-blank TEXT nodes.
		if ( $node->nodeName == "#text" && !$this->_isBlankString($node->nodeValue) && mb_strlen($node->nodeValue) > 2 ) 
		{
			// Save the snippet in an array
			$snippets[] = $this->_fixEncoding( $node->nodeValue );
		}

		if ( $node->hasChildNodes() && !$this->_isSkipped($node) ) 
		{
			// Now recurse through all the child nodes.
			foreach ( $node->childNodes as $child ) { $this->buildSourceArray( $child, $snippets ); }
		}
	}


	// Recurse through the DOM Document and translate all the text snippets to the target language
	function translateNodes( &$node, $translations, $parent_settings ) 
	{
		// Start by combining the settings from the parent node with the settings found in this nodes CSS classes
		$my_settings = $this->updateNodeSettings($node, $parent_settings);
		
		// Base case, recurse through all the child nodes.
		if ( $node->hasChildNodes() && !$this->_isSkipped($node) )
		{
			foreach ( $node->childNodes as $child ) { $this->translateNodes( $child, $translations, $my_settings ); }
		}

		// Do we even care to translate this node? Only translate none-blank TEXT nodes.
		if ( $node->nodeName == "#text" && !$this->_isBlankString($node->nodeValue) && mb_strlen($node->nodeValue) > 2 ) 
		{
		
			$st = $this->_fixEncoding( $node->nodeValue );
			$k  = md5( $st );
			
			// DEBUG
			// echo $k." => |".$st."|<br />";
			
			if ( !empty( $translations[$k] ) ) { $tt = $translations[$k]; }
			else { $tt = ''; log_message('error', "WWL: No translation for {$node->nodeValue}"); }
			
			// Is the translation non-empty and non-error? Then update the value of the text node with the translation.
			
			if ( $this->_isValidTranslation( $tt )) 
			{ 
			
				if ( $my_settings->getAllowEdit() == 'y' && !$this->_isSkippedForEditing($node) ) 
				{					
					// If edits are allowed, then add two spans with the source and target snippes (source hidden) to enable JS translator.
										
					$span_src = $this->doc->createElement( 'span', htmlentities($st) );
					$span_tgt = $this->doc->createElement( 'span', html_entity_decode( $tt, ENT_QUOTES ) );

					try {
						$node->parentNode->insertBefore( $span_src, $node );
					} catch (Exception $e) { }

					try {
						$node->parentNode->insertBefore( $span_tgt, $node );
					} catch (Exception $e) { }

					
					// And render the current node irrelevant. 
					// I had to do this, because simply replacing the node was breaking the recursion.
					$node->nodeValue = "";
	
					$span_src_id = $this->doc->createAttribute('id');
					$span_tgt_id = $this->doc->createAttribute('id');

					$span_src_id_text = $this->doc->createTextNode( ("wwl-content-".$this->z."-src") );
					$span_tgt_id_text = $this->doc->createTextNode( ("wwl-content-".$this->z) ); $this->z++;
					

					$span_src_class = $this->doc->createAttribute('class');
					$span_tgt_class = $this->doc->createAttribute('class');

					$span_src_class_text = $this->doc->createTextNode('wwl-hide');
					$span_tgt_class_text = $this->doc->createTextNode('wwl-is-editable');


					$span_src_id->appendChild( $span_src_id_text );
					$span_tgt_id->appendChild( $span_tgt_id_text );

					$span_src_class->appendChild( $span_src_class_text );
					$span_tgt_class->appendChild( $span_tgt_class_text );

					$span_src->appendChild( $span_src_id );
					$span_src->appendChild( $span_src_class );

					$span_tgt->appendChild( $span_tgt_id );
					$span_tgt->appendChild( $span_tgt_class );


				}
				else
				{
					// Because some character return from the WWL as html entities we have to decode them....
					// Because DOMDocument is going to RE-encode them automatically.
					$node->nodeValue = html_entity_decode( $tt, ENT_QUOTES );
					
					//log_message('debug', "Translating node: " . $node->nodeValue . " ==>> " . html_entity_decode( $tt, ENT_QUOTES ));
					
				}
			}			
		}		
	}


	// This function takes the parent node's settings and updates them for the current
	// context using any settings available in the nodes classes
	function updateNodeSettings( $node, $parent_settings ) {
	
		$this_settings = clone $parent_settings;
		
		// Only need to do updating if current node has any attributes to begin with
		if ($node->hasAttributes()) {
		
			$class_atts = $node->attributes->getNamedItem('class');
			if (!empty($class_atts)) {
				$classes = explode(" ", $class_atts->nodeValue);

				foreach ($classes as $class) { 
					switch ($class) {
					
						//
						case "allow_machine": $this_settings->setAllowMachine('y'); break;
						case "disallow_machine": $this_settings->setAllowMachine('n'); break;
						case "allow_anonymous": $this_settings->setAllowAnonymous('y'); break;
						case "disallow_anonymous": $this_settings->setAllowAnonymous('n'); break;
						case "allow_edit": $this_settings->setAllowEdit('y'); break;
						case "disallow_edit": $this_settings->setAllowEdit('n'); break;
						case "require_professional": $this_settings->setRequireProfessional('y'); break;
						case "dont_require_professional": $this_settings->setRequireProfessional('n'); break;
					}
				}
			}
		}
		return $this_settings;
	}
	
	
	// Some nodes we always skip during translation
	function _isSkipped( $node )
	{
		$skipme = array( 'style', 'script', 'link' );
		if ( in_array($node->nodeName, $skipme) ) return true;
		else return false;
	}

	// And some we skipped when allowing user-edits
	function _isSkippedForEditing( $node )
	{
		$skipme = array( 'title' );
		if ( in_array($node->parentNode->nodeName, $skipme) ) return true;
		else return false;
	}

	// Fixes the encoding to utf8.  Not very comprehensive though, I think utf8_encode is only meant to
	// re-encode one of the non utf8 charsets.
	function _fixEncoding($in_str)
	{
	  	$cur_encoding = mb_detect_encoding($in_str) ;
	  	if ($cur_encoding == "UTF-8" && mb_check_encoding($in_str,"UTF-8"))
	    	return $in_str;
	  	else
	    	return utf8_encode($in_str);
	}


	// Add the JS script that enables us to submit user-generated translations to the WWL.
	function _makeEditable()
	{
		$assets_url_base = "/"; //"http://" . $this->targetLanguage . "." . $this->targetUrl->getHostBase() . "/";
		$head = $this->doc->getElementsByTagname('head')->item(0);

		// Create and append: JS
		$inline_edit_js = $this->doc->createElement('script');
		$head->appendChild( $inline_edit_js );

		$type = $this->doc->createAttribute('type'); 
		$inline_edit_js->appendChild( $type );
		
		$type_text = $this->doc->createTextNode('text/javascript');
		$type->appendChild( $type_text );
		
		$src = $this->doc->createAttribute('src');
		$inline_edit_js->appendChild( $src );
		
		$src_text = $this->doc->createTextNode($assets_url_base. "wwlassets/js/wwlproxy.js");
		$src->appendChild( $src_text );


		// Create and append: CSS
		$inline_edit_css = $this->doc->createElement('link');
		$head->appendChild( $inline_edit_css );

		$rel = $this->doc->createAttribute('rel');
		$inline_edit_css->appendChild( $rel );
		
		$rel_text = $this->doc->createTextNode('stylesheet');
		$rel->appendChild( $rel_text );

		$type = $this->doc->createAttribute('type'); 
		$inline_edit_css->appendChild( $type );
		
		$type_text = $this->doc->createTextNode('text/css');
		$type->appendChild( $type_text );
		
		$href = $this->doc->createAttribute('href');
		$inline_edit_css->appendChild( $href );
		
		$href_text = $this->doc->createTextNode($assets_url_base . "wwlassets/css/wwlproxy.css");
		$href->appendChild( $href_text );


		// And now insert the Translator Form as the last element of the HTML document
		$nodes = $this->doc->getElementsByTagname('body');
		if (!empty($nodes)) { $body = $nodes->item(0); } else return;
		
		$tform_html = "<script type=\"text/javascript\">wwlproxy.sourceLanguage=\"" . $this->sourceLanguage . "\";wwlproxy.targetLanguage=\"" . $this->targetLanguage . "\";wwlproxy.ajaxURL=\"" . $assets_url_base . "wwlassets/ajax/submit.php\";</script><div id=\"wwl-lightbox\"><div id=\"wwl-overlay\"></div><div id=\"wwl-translator\"><div id=\"wwl-translator-title\">Edit Translation</div><div id=\"wwl-translator-source-text\"></div><textarea id=\"wwl-translator-target-text\"></textarea><input id=\"wwl-inline-editor-update\" type=\"button\" value=\"Update translation\" onclick=\"return wwlproxy.submitTranslation();\" /> or <a href=\"#\" onclick=\"return wwlproxy.hideTranslatorForm();\">Cancel</a></div></div>";

		$tform = $this->doc->createDocumentFragment();
		$tform->appendXML($tform_html);
		$body->appendChild($tform);
	}


	// Fixes CSS and JS declaration URLs
	function _fixTagProperty( $tag, $property )
	{
		// Get all the nodes that represent <$tag> elements - eg. <link>, <img>, etc.
		$nodes = $this->doc->getElementsByTagname( $tag );
		
		// Now loop through those <$tag> nodes and check that their corresponding property points to a full URL, not a relative one.
		foreach( $nodes as $node ) 
		{
			// Does the property even exist for this node (eg. Not every <td> has a background="" property.)
			if ( !empty($node->attributes->getNamedItem($property)->nodeValue) ) 
			{
				$href = $node->attributes->getNamedItem( $property )->nodeValue;

				if ( !preg_match( '/^http/', $href ) && preg_match( '%^/%', $href ) ) 
				{
					// This a root-indexed url. Prepend the http://example.com bit.
					$node->attributes->getNamedItem( $property )->nodeValue = 
						htmlentities( $this->targetUrl->getDomain() . $href );
				}
				elseif ( !preg_match('/^http/', $href ) && !preg_match( '%^/%', $href ) )
				{
					// This is a relative url.  Prepend the http://example.com/path/to/directory/ bit.
					$node->attributes->getNamedItem( $property )->nodeValue = 
						htmlentities( $this->_combinedURL( $this->targetUrl->toString(), $href ) );
				}
			}
		}
	}


	// Fix the language codes and text direction embedded in the HTML tag
	function _fixLanguageDefinition()
	{
		$elem = $this->doc->getElementsByTagname('html');
		$rtl_langs = array( "ar", "fa", "he", "iw", "ur" );
		
		foreach( $elem as $html_tag ) {
			
			// Update the lang definitions in the HTML tag
			if ( !empty($html_tag->attributes->getNamedItem('lang')->nodeValue) ) {
				$html_tag->attributes->getNamedItem('lang')->nodeValue = $this->targetLanguage;
			}
			
			if ( !empty($html_tag->attributes->getNamedItem('xml:lang')->nodeValue) )
				$html_tag->attributes->getNamedItem('xml:lang')->nodeValue = $this->targetLanguage;

			// Ensure the text direction is set correctly
			if ( in_array( $this->targetLanguage, $rtl_langs ))
			{
				if ( !empty($html_tag->attributes->getNamedItem('dir')->nodeValue) ) {
					$html_tag->attributes->getNamedItem('dir')->nodeValue = "rtl";
				} 
				else 
				{
					$dir = $this->doc->createAttribute('dir');
					$html_tag->appendChild( $dir );
					$dir_text = $this->doc->createTextNode('rtl');
					$dir->appendChild( $dir_text );
				
				}
			}
		}
	}


	// Fix root-indexed and relative targets for links by adding the base URL
	function _fixLinks()
	{
		// Get all the links in the page
		$nodes = $this->doc->getElementsByTagname('a');
		
		// Now loop through those links and check that 
		// (1) if they're internal, they point to a full URL. 
		// (2) if they're external, route through WWL.
		foreach( $nodes as $node ) 
		{
			if ( !empty($node->attributes->getNamedItem('href')->nodeValue) ) 
			{
				$href = $node->attributes->getNamedItem('href')->nodeValue;

				// For preg_match purposes
				$pattern = '%' . $this->targetUrl->getHost() . '%';
				
				if ( $this->routeAllLinks )
				{
					// Is this page already routed through the WWL? Route all links through the WWL then.
					$node->attributes->getNamedItem('href')->nodeValue = 
						htmlentities( "http://proxy.worldwidelexicon.org?l=" . $this->targetLanguage . "&u=" . $this->_combinedURL( $this->targetUrl->toString(), $href ) );
					
				} 
				elseif ( preg_match("%^http%", $href ) && !preg_match( $pattern, $href ) )
				{
					// Is this a link to an external url? Route it through the WWL.
					$node->attributes->getNamedItem('href')->nodeValue = 
						htmlentities( "http://proxy.worldwidelexicon.org?l=" . $this->targetLanguage . "&u=" . $href );
				}
				elseif ( preg_match("%^http://www%", $href) && preg_match($pattern, $href) )
				{
					// Is this an absolute internal url with the "www"? Remove the www and add the language code.
					$node->attributes->getNamedItem('href')->nodeValue =
						htmlentities($this->_addLanguageCode( preg_replace("%http://www\.%", "http://", $href)));
				}
				elseif ( preg_match("%^http%", $href ) && preg_match( $pattern, $href ) )
				{
					// Is this an absolute internal url without the "www"?  Add the language code.
					$node->attributes->getNamedItem('href')->nodeValue = 
						htmlentities( $this->_addLanguageCode( $href ) );
				}
				elseif ( !empty($href) && !preg_match( "%^http%", $href ) ) 
				{
					// Is this a relative internal url? Combine it and add the language code.
					$newurl = $this->_combinedURL( $this->targetUrl->toString(), $href );
					$newurl = htmlentities($this->_addLanguageCode( preg_replace("%http://www\.%", "http://", $newurl)));
					$node->attributes->getNamedItem('href')->nodeValue = $newurl;
				}
			}
		}		
	}
	
	// Fixes CSS @import statements that are on-page.
	function _fixCSSImport()
	{
		// Get all the <style> nodes, only place we might see
		$nodes = $this->doc->getElementsByTagname( 'style' );
		$baseurl = $this->targetUrl->getDomain();
		
		// Loop through any / all <style> declarions and fix @import declarations if need be.
		foreach( $nodes as $node )
		{
			// This sh**t makes me dizzy.
			$node->nodeValue = preg_replace( '/@import "(.*?)"/', "@import \"$baseurl$1\"", $node->nodeValue);
		}
	}


	// Adds a dropdown menu language selector to the current page, if shortcode exists.
	function addLanguageSelector()
	{
		// The two possible shortcodes for a language dropdown
		// are <!-- wwl_language_selector --> and <div id="wwl_language_selector"></div>
		$divs = $this->doc->getElementsByTagname( 'div' );
		$comments = $this->getCommentNodes();

		// First, let's generate the HTML for the language selector dropdown menu.
		$lang_select_html  = "<form action=\"./\"><select onchange=\"wwlproxy.changeLanguage(this.options[this.selectedIndex].value)\" id=\"wwl_language_selector\" class=\"disallow_edit\">";
		$lang_select_html .= "<option selected=\"selected\">Translate this page...</option><option disabled=\"disabled\">------------------</option>";
		foreach ( $this->page_settings->getLanguages() as $language_code ) {
			$lang_select_html .= "<option value=\"{$language_code}\">" . LanguageHelper::getLanguageName($language_code) . "</option>";
		}
		$lang_select_html .= "</select></form>";

		// Now let's turn the HTML into a DOMDocument Node
		$lang_select = $this->doc->createDocumentFragment();
		$lang_select->appendXML($lang_select_html);

		// Do we have any DIVs to replace?
		foreach( $divs as $div ) {
			if ( $div->hasAttribute('id') && ($div->getAttribute('id') == "wwl_language_selector") ) {
				try {
					$div->parentNode->replaceChild( $lang_select->cloneNode(true), $div );
				} catch (Exception $e) { }
			}
		}
		
		// Do we have an <!-- wwl_language_selector --> instances to replace?		
		foreach( $comments as $comment ) {
			if (trim($comment->nodeValue) == "wwl_language_selector") {
				try {
					$comment->parentNode->replaceChild( $lang_select->cloneNode(true), $comment );
				} catch (Exception $e) { }	
			}
		}		
	}
	
	// Recursively build the array of snippets of text within this document that need to be translated.
	function getCommentNodes() 
	{					
		$comment_nodes = array();
		
		if ( $this->doc->documentElement != NULL ) {
			$this->recursiveFindComments( $this->doc->documentElement, $comment_nodes );
		}
		
		return $comment_nodes;
	}
	
	// The workhorse for the results above
	function recursiveFindComments ( &$node, &$comment_nodes)
	{
		// Have we found a comment node?
		if ( $node->nodeName == "#comment" ) { $comment_nodes[] = $node; }

		// Now recurse through all the child nodes.
		if ( $node->hasChildNodes() ) {
			foreach ( $node->childNodes as $child ) { $this->recursiveFindComments( $child, $comment_nodes ); }
		}
	}
	
	
	
	// Many of the text nodes in the DOMDocument are simply collections of spaces.  No need to translate them.
	function _isBlankString( $string )
	{
		if (strlen(trim(preg_replace('/\xc2\xa0/',' ',$string))) == 0) return true;
		else return false;
		
	}

	
	//  Sometimes the WWL returns duds and errors, don't display them as translations, but do log them.
	function _isValidTranslation( $translation )
	{
		if ( empty( $translation ) ) 
		{
			return false;
		}

		if ( preg_match( '/<pre>Traceback \(most recent call last\)/', $translation ) )
		{
			log_message('error', 'WWL Translation returned Traceback: ' . $translation );
			return false;
		}

		if ( preg_match( '/<title>500 Server Error<\/title>/', $translation ) ) 
		{
			log_message('error', "WWL Translation returned '500 Server Error':".$translation);
			return false;
		}
		
		else return true;
	}


	/* URL Helper Functions **************************************************************/

	// Combines an absolute path and a relative URL to provide an absolute URL.
	// Thanks to http://www.web-max.ca/PHP/misc_24.php
	function _combinedURL( $absolute, $relative )
	{
		$p = parse_url($relative);
		if(!empty($p["scheme"])) return $relative;

		extract(parse_url($absolute));
		// if (!empty($path)) { $path = dirname($path); } else { $path = ''; }
		$path = dirname($path);

		if (!empty($relative) && $relative{0} == '/') {
			$cparts = array_filter(explode("/", $relative));
		}
		else 
		{
			$aparts = array_filter(explode("/", $path));
			$rparts = array_filter(explode("/", $relative));
			$cparts = array_merge($aparts, $rparts);

			foreach ($cparts as $i => $part) 
			{
				if ($part == '.') {
					$cparts[$i] = null;
				}

				if ($part == '..') {
					$cparts[$i - 1] = null;
					$cparts[$i] = null;
				}
			}
			$cparts = array_filter($cparts);
		}
		
		$path = implode("/", $cparts);
		$url = "";
		
		if (!empty($scheme)) {
			$url = "$scheme://";
		}
		if (!empty($user)) {
			$url .= "$user";
			if ($pass) {
				$url .= ":$pass";
			}
			$url .= "@";
		}
		
		if(!empty($host)) {
			$url .= "$host/";
		}

		$url .= $path;
		return $url;
	}


	// Prepend current two-letter language code prepended to a URL
	function _addLanguageCode( $url )
	{
		return preg_replace( '/^http:\/\//', "http://".$this->targetLanguage.".", $url );
	}

	// Returns the full URL of the page currently displayed
	function _fullUrl()
	{
		$s = empty($_SERVER["HTTPS"]) ? '' : ($_SERVER["HTTPS"] == "on") ? "s" : "";
		$protocol = substr(strtolower($_SERVER["SERVER_PROTOCOL"]), 0, strpos(strtolower($_SERVER["SERVER_PROTOCOL"]), "/")) . $s;
		$port = ($_SERVER["SERVER_PORT"] == "80") ? "" : (":".$_SERVER["SERVER_PORT"]);
		return $protocol . "://" . $_SERVER['SERVER_NAME'] . $port . $_SERVER['REQUEST_URI'];
	}
		
	// Returns the path of a given URL, as in www.domain.com/PATH
	function _getPathURL( $url )
	{
		$url_bits = parse_url($url);
		$return_val = $url_bits['path'];
		if (!empty($url_bits['query'])) { $return_val .= "?" . $url_bits['query']; }
		if (!empty($url_bits['fragment'])) { $return_val .= "#" . $url_bits['fragment']; }
		
		return $return_val;
	}
	
	
	/* Cache Helper Functions **************************************************************/
	function setCacheExpire($expire) {
		$this->cacheExpire = $expire;
		if ($this->cacher) {
			$this->cacher->expire = $expire;
			$this->cacher->clearExpired();
		}
	}
	function clearCache(){
		if ($this->cacher){
			$this->cacher->clear();
		}
	}
	
	
	/* JSON Helper Functions **************************************************************/
	function jsonDecode($input) {
		$json = new Services_JSON(SERVICES_JSON_LOOSE_TYPE);
		return $json->decode($input);
	}

	function jsonEncode($value) {
		$json = new Services_JSON(SERVICES_JSON_IN_ARR);
		return $json->encode($value);
	}


	/* DOM Debugging Functions **************************************************************/ 
	function walkDom($node, $level = 0) {
		$indent = '';
		for ($i = 0; $i < $level; $i++)
		$indent .= '&nbsp;&nbsp;&nbsp;&nbsp;'; //prettifying the output
		if (true /*$node->nodeType == XML_TEXT_NODE*/) {
			echo $indent.'<b>'.$node->nodeName.'</b> - |'.$node->nodeValue.'|';

			if ( $node->nodeType == XML_ELEMENT_NODE ) {
				$attributes = $node->attributes; // get all the attributes(eg: id, class)
				foreach($attributes as $attribute) {
					echo ', '.$attribute->name.'='.$attribute->value;
				}				
			}

			echo '<br />';
		}

		$cNodes = $node->childNodes;
		if (count($cNodes) > 0) {
			$level++ ; // go one level deeper
			foreach($cNodes as $cNode)
				$this->walkDom($cNode, $level);
			$level = $level - 1;
		}
	}

}

/* Location: ./system/application/controllers/wwlproxy.php */