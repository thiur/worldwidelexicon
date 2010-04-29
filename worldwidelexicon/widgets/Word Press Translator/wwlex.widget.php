<?php 
echo $before_widget;
echo $before_title.__('Languages').$after_title;
//echo $wwlex->getUserRole();
//print_r($wwlex->listRoles());
echo '<ul class="wwl-langs-list">';
echo('<li><a href="'.$wwlex->getTranslationUrl($wwlex->sourceLanguage).'">'.$wwlex->sourceLanguageName().'</a> ('. __('original').')</li>');
	foreach ($wwlex->languages as $k=>$v) {
		$languageEnabled = false;
		foreach ($wwlex->tOptions as $kk=>$vv) {
			if (get_option($k.'_'.$kk.'_enable')) {
				$languageEnabled = true;
				break;
			}
			if (get_option($k.'_'.$kk.'_select') && get_option($k.'_'.$kk.'_select') != "none") {
				$languageEnabled = true;
				break;
			}
		}
		if ($languageEnabled) {
			if ($k == $wwlex->targetLanguage) {
				echo('<li class="wwl-lang-'.$k.'">'.$wwlex->languageName($k).'</li>');
			} else {
				echo('<li class="wwl-lang-'.$k.'"><a href="'.$wwlex->getTranslationUrl($k).'">'.$wwlex->languageName($k).'</a></li>');
			}
		}
	}
echo '</ul>';	
echo $after_widget; 
?>
