<?php

	/**
	 *	class Wwlsettings - This class encapsulates the settings we will pay attention to when translating a page.
	 *		
	 *	@author		Cesar Gonzalez (icesar@gmail.com)
	 *	@version	0.1
	 *	@license	BSD
	 */


	class WwlSettings {
	
		// The almight settings array.
		private $settings;

		function __construct( $initial_settings ) {
		
			$this->settings = array();
			$this->settings['translate'] = 'y';
			$this->settings['allow_machine'] = 'y';
			$this->settings['allow_anonymous'] = 'y';
			$this->settings['min_score'] = 0;
			$this->settings['allow_edit'] = 'y';
			$this->settings['require_professional'] = 'n';
			$this->settings['languages'] = array();
			$this->settings['machine_translation_languages'] = array();
			$this->settings['community_translation_languages'] = array();
			$this->settings['professional_translation_languages'] = array();
			$this->settings['lsp'] = '';
			$this->settings['lspusername'] = '';
			$this->settings['lsppw'] = '';
			
			// Ok, the defaults are set, now let's process anything that was passed in.
			if (!empty( $initial_settings )) 
			{
				foreach ( $initial_settings as $key => $value ) 
				{
					switch($key)
					{
						case "languages":
						case "machine_translation_languages":
						case "community_translation_languages":
						case "professional_translation_languages":
						
							$this->setLanguageArray( $key, $value );
							break;
						
						default:
						
							$this->settings[$key] = $value;
							break;
					}
				}
			}
		}
	
		function WwlSettings( $initial_settings = array() ) {
			$this->__construct( $initial_settings );
		}


		// Print setting to screen, mostly for debuggins purposes
		public function printSettings() {
			foreach( $this->settings as $key => $value ) {
				echo "settings[ '" . $key . "'] = " . $value . "; <br />";
			}
		}
		
		// Extract page-wide setting from the HTML. These live entirely in the meta tags.
		// Where is the right place to do this, since DOMDocument is already being read by WWLPRoxy?
		function getSettingFromHTML( $domdocument ) {}
		
		// Simple setter methods, no error checking.	
		public function setTranslate( $bool ) { $this->settings['translate'] = $bool; }
		public function setAllowMachine( $bool ) { $this->settings['allow_machine'] = $bool; }
		public function setAllowAnonymous ( $bool ) { $this->settings['allow_anonymous'] = $bool; }
		public function setMinScore( $int ) { $this->settings['min_score'] = $int; }
		public function setAllowEdit( $bool ) { $this->settings['allow_edit'] = $bool; }
		public function setRequireProfessional( $bool ) { $this->settings['require_professional'] = $bool; }
		public function setLanguages( $value ) { $this->setLanguageArray( "languages", $value ); }
		public function setMachineLanguages( $value ) { $this->setLanguageArray( "machine_translation_languages", $value ); }
		public function setCommunityLanguages( $value ) { $this->setLanguageArray( "community_translation_languages", $value ); }
		public function setProfessionalLanguages( $value ) { $this->setLanguageArray( "professional_translation_languages", $value ); }
		public function setLSP( $string ) { $this->settings['lsp'] = $string; }
		public function setLSPUsername( $string ) { $this->settings['lspusername'] = $string; }
		public function setLSPPassword( $string ) { $this->settings['lsppw'] = $string; }


		// Simple getter methods.
		public function getTranslate() { return $this->settings['translate'];}
		public function getAllowMachine() { return  $this->settings['allow_machine']; }
		public function getAllowAnonymous() { return  $this->settings['allow_anonymous']; }
		public function getMinScore() { return  $this->settings['min_score']; }
		public function getAllowEdit() { return  $this->settings['allow_edit']; }
		public function getRequireProfessional() { return  $this->settings['require_professional']; }
		public function getLanguages() { return  $this->settings['languages']; }
		public function getMachineLanguages() { return  $this->settings['machine_translation_languages']; }
		public function getCommunityLanguages() { return  $this->settings['community_translation_languages']; }
		public function getProfessionalLanguages() { return  $this->settings['professional_translation_languages']; }
		public function getLSP() { return  $this->settings['lsp']; }
		public function getLSPUsername() { return  $this->settings['lspusername']; }
		public function getLSPPassword() { return  $this->settings['lsppw']; }

		// Function that do actual work
		private function setLanguageArray( $key, $value ) { 
		
			if ($value == "*" || $value == "all") 
			{ 
				$this->settings[$key] = LanguageHelper::getLanguageCodes();	
			} 
			else 
			{
				$langs = explode(",", $value); $trimmed_langs = array();
				foreach ($langs as $lang) { $trimmed_langs[] = trim($lang); }
				$this->settings[$key] =  $trimmed_langs;
			}		
		}
		
	}
	
?>