<div class="wrap">
<h2><?php _e('Worldwide Lexicon Options');?></h2>

<form method="post" action="options.php">
<?php 
if (function_exists('register_setting')){
	settings_fields('wwl-options'); 
} else {
	wp_nonce_field('update-options');
}
?>
<h3><?php _e('Source language') ?></h3>
<?php
if (!function_exists('curl_init')) {
	echo '<div class="updated fade error"><p>';
	_e('<strong>Warning:</strong> CURL is not installed. Worldwide Lexicon won\'t work correctly.');
	echo '</p></div>';
}
if ($wwl->error) {
	echo '<div class="updated fade error"><p>';
	echo $wwl->error;
	echo '</p></div>';
}
wwl_inject_script();
?>
<script type="text/javascript">
wwl.langs = <?php echo $wwlex->languagesJSON(); ?>;
</script>
<table class="form-table">
<tr valign="top">
<th scope="row"><label for="wwl_language"><?php _e('Your blog language:') ?></label></th>
<td><select name="wwl_language" id="wwl_language">
<?php
	$current = $wwlex->getSourceLanguage();

	foreach ($wwlex->languages as $k=>$v) {
		$sel = (($k === $current ) ? "selected" : "");
		echo '<option value = "'.$k.'" '.$sel.'>'.$v.'</option>';
	}
?>
</select>
</td>
</tr>
</table>
<h3><?php _e('Target languages') ?></h3>
<table class="form-table">
<tr valign="top">
<th></th>
<?php
	foreach($wwlex->tOptions as $k=>$v) {
		echo '<td align="center">'. __($v).'</td>';
	}
?>
</tr>
<tr valign="top">
<th></th>
<?php
	foreach($wwlex->tOptions as $k=>$v) {
		echo '<td align="center" style="border-bottom: 1px gray solid">';
		switch ($k) {
			case "vol":
				echo '<select onchange="wwl.massSelect(\''.$k.'\', this);">';
				foreach ($wwlex->listRoles() as $role => $name) {
					echo '<option value="'.$role.'" >'.$name.'</option>';
				}
				echo '</select>';
				break;
			default:
				echo '<input type="checkbox" onclick="wwl.massSwitch(\''.$k.'\', this);"/>';
		}
		echo '</td>';
	}
?>
</tr>
<?php
	$permOptions = array();
	foreach ($wwlex->languages as $k=>$v) {
		echo '<tr>';
		echo '<th>'.$v.'</th>';
		foreach ($wwlex->tOptions as $kk=>$vv) {
			echo '<td align="center">';
			$line = '';
			switch ($kk) {
				case "vol":
					$access = get_option($k.'_'.$kk.'_select');
					if (!$access) $access = "none";
					$line .= '<select id="'.$k.'_'.$kk.'_select" name="'.$k.'_'.$kk.'_select">';
					foreach ($wwlex->listRoles() as $role => $name) {
						$selected = $role == $access ? 'selected' : '';
						$line.= '<option value="'.$role.'" '.$selected.'>'.$name.'</option>';
					}
					$line .= '</select>';
					$permOptions [] = $k.'_'.$kk.'_select';
					break;
				default:	
					$checked = get_option($k.'_'.$kk.'_enable') ? "checked" : "";
					$line = '<input type="checkbox" id="'.$k.'_'.$kk.'_enable" name="'.$k.'_'.$kk.'_enable" '.$checked .'/>'.$line;
					$permOptions [] = $k.'_'.$kk.'_enable';
			}
			echo $line;
			echo '</td>';
			
		}
		echo '</tr>';
	}
?>
</table>
<h3><?php _e('SpeakLike account (required for professional translations)') ?></h3>
<table class="form-table">
<tr valign="top">
<th scope="row"><label for="speaklike_user"><?php _e('SpeakLike Username:') ?></label></th>
<td><input type="text" id="speaklike_user"  name="speaklike_user" value="<?php echo get_option('speaklike_user');?>"/>
</td>
</tr>
<tr valign="top">
<th scope="row"><label for="speaklike_pass"><?php _e('SpeakLike Password:') ?></label></th>
<td><input type="password" id="speaklike_pass" name="speaklike_pass" value="<?php echo get_option('speaklike_pass');?>"/>
</td>
</tr>
</table>

<h3><?php _e('Advanced options') ?></h3>
<table class="form-table">
<tr valign="top">
<th scope="row"><label for="wwl_translation_timeout"><?php _e('Page translation timeout') ?></label></th>
<td><input type="text" id="wwl_translation_timeout" name="wwl_translation_timeout" value="<?php echo $wwlex->timeout;?>"/> <?php _e('seconds') ?>
</td>
</tr>
<tr valign="top">
<th scope="row"><label for="wwl_cache_timeout"><?php _e('Cache timeout:') ?></label></th>
<td><input type="text" id="wwl_cache_timeout" name="wwl_cache_timeout" value="<?php echo $wwlex->cacheTTL;?>"/> <?php _e('seconds') ?> 
<input type="button" class="button-primary" onclick="return wwl.API.clearCache();" value="<?php _e('Clear cache') ?>" />
</td>
</tr>
<tr valign="top">
<th scope="row"><label for="wwl_hide_decorations"><?php _e('Don\'t add post decorations') ?></label></th>
<td><input type="checkbox" id="wwl_hide_decorations" name="wwl_hide_decorations" <?php if (!$wwlex->decorateOutput) echo "checked"?>/>
</td>
</tr>
<tr valign="top">
<th scope="row"><label for="wwl_hook_gettext"><?php _e('Translate templates (via gettext hook)') ?></label></th>
<td><input type="checkbox" id="wwl_hook_gettext" name="wwl_hook_gettext" <?php if (get_option('wwl_hook_gettext')) echo "checked"?>/>
</td>
</tr>
</table>
<input type="hidden" name="action" value="update" />
<?php 
if (!function_exists('register_setting')) {
?>
<input type="hidden" name="page_options" value="wwl_hook_gettext,wwl_hide_decorations,wwl_translation_timeout,wwl_cache_timeout,wwl_language,speaklike_user,speaklike_pass,<?php echo implode(",", $permOptions);?>" />
<?php } ?>
<p class="submit">
<input type="submit" class="button-primary" value="<?php _e('Save Changes') ?>" />
</p>

<p class="submit">

</p>
</form>

</div>