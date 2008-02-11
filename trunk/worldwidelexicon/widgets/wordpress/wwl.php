<?php
/*
Plugin Name: Worldwide Lexicon
Plugin URI: http://www.worldwidelexicon.org/
Description: Community-driven content translations
Version: 0.9.7
Author: WWL
Author URI: http://www.worldwidelexicon.org/about/
*/

$wwl_enabled = true;
$wwl_site_guid = "";
$wwl_site_url = "";
$wwl_site_lang_code = "";
$wwl_site_share = "";

$wwl_content_path = "";
$wwl_title_path = "";
$wwl_js_name = "marx.multi_0_9_6.js";

define('WWL_PLUGIN_HOST', 'marx.worldwidelexicon.org');
define('WWL_WIDGET_HOST', 'http://marx.worldwidelexicon.org');

function wwl_init() {
    global $wwl_site_guid, $wwl_site_url, $wwl_site_lang_code, $wwl_site_share, $wwl_enabled, $wwl_title_path;

    if (empty($wwl_enabled)) {
        $wwl_enabled = get_option('wwl_enabled');
    }
    if (empty($wwl_site_guid) && !($wwl_site_guid = get_option('wwl_site_guid'))) {
        $wwl_site_guid = str_replace('http', '', preg_replace('/[^a-zA-Z0-9.]/', '', get_option('home')));
    }
    if (empty($wwl_site_url) && !($wwl_site_url = get_option('wwl_site_url'))) {
        $wwl_site_url = get_option('home');
    }
    if (empty($wwl_site_lang_code) && !($wwl_site_lang_code = get_option('wwl_site_lang_code'))) {
        $wwl_site_lang_code = get_option('rss_language');
    }
    if (empty($wwl_site_share)) {
        $wwl_site_share = get_option('wwl_site_share');
    }

    if (empty($wwl_title_path) && !($wwl_title_path = get_option('wwl_title_path'))) {
        $wwl_title_path = "div.post:first h2 a";
    }

    add_action('admin_menu', 'wwl_config_page');
}

add_action('init', 'wwl_init');
add_action('activate_wwl', 'wwl_register');

function wwl_config_page() {
    if ( function_exists('add_submenu_page') )
        add_submenu_page('plugins.php', __('Worldwide Lexicon Configuration'), __('WWL Configuration'), 'manage_options', 'wwl-key-config', 'wwl_conf');
}

function wwl_conf() {
    global $wwl_site_guid, $wwl_site_url, $wwl_site_lang_code, $wwl_site_share, $wwl_enabled, $wwl_title_path;

    $ms = array();

    if ( isset($_POST['submit']) ) {
        if ( function_exists('current_user_can') && !current_user_can('manage_options') )
            die(__('Cheatin&#8217; uh?'));


        $enabled = preg_replace('/[^0-9]/', '', @$_POST['wwl_enabled'] );
        $guid = preg_replace('/[^-a-zA-Z0-9._]/', '', @$_POST['wwl_site_guid'] );
        $lang = preg_replace('/[^a-z]/', '', substr(@$_POST['wwl_site_lang_code'], 0, 5));
        $share = preg_replace('/[^0-9]/i', '', @$_POST['wwl_site_share'] );

        if ($title = @$_POST['wwl_title_path']) {
            update_option("wwl_title_path", $title);
            $wwl_title_path = $title;
        }

        $url = get_option('home');
        $result = wwl_change($guid, $url, $lang, $share);

        $status = $result['result'];

        if (isset($result['messages']))
            $ms = array_merge($ms, $result['messages']);

    }
    if (isset($result['updated'])) {
        foreach($result['updated'] as $name => $value) {
            update_option("wwl_site_$name", $value);
        }
        wwl_init();
        ?><div id="message" class="updated fade"><p><strong><?php echo ('Options saved.') ?></strong></p></div><?php
    } else {
        $enabled = false;
        ?><div id="message" class="updated fade-ff0000"><pre><?php echo (ucfirst($status)) ?></pre></div><?php
    }
    update_option("wwl_site_enabled", $enabled);

    $messages = array(
        'new_guid_empty' => array('color' => 'aa0', 'text' => __('Your key has been cleared.')),
    );


/*<div id="message" class="updated fade-ff0000"><pre><?php print_r($result) ?></pre></div>*/
?>
<div class="wrap">
    <h2><?php _e('Worldwide Lexicon Configuration'); ?></h2>
    <div class="narrow">
        <?php foreach ( $ms as $m ) { ?>
                <p style="padding: .5em; color: #fff; font-weight: bold;"><?php echo $m; ?></p>
        <?php } ?>
        <form action="" method="post" id="wwl-conf" style="margin: auto; width: 400px; ">
                <h3><label for="wwl_site_guid"><?php _e('WWL Site Guid'); ?></label></h3>
                <p><input id="wwl_site_guid" name="wwl_site_guid" type="text" size="15" maxlength="50" value="<?php echo $wwl_site_guid; ?>" style="font-family: 'Courier New', Courier, mono; font-size: 1.5em;" /> </p>
            <?php if ($wwl_site_guid) { ?>
                <h3><label for="wwl_title_path"><?php _e('Post title CSS path'); ?></label></h3>
                <p><input id="wwl_title_path" name="wwl_title_path" type="text" size="25" maxlength="50" value="<?php echo $wwl_title_path; ?>" style="font-family: 'Courier New', Courier, mono; font-size: 1.5em;" /> </p>
                <h3><label for="wwl_site_lang_code"><?php _e('Your site language'); ?></label></h3>
                <p>
                <?php $langs = array('en'=>'English', 'ja'=>"Japanese", 'de'=>"German", 'es'=>'Spanish', 'fr'=>"French", 'ko'=>"Korean", 'ar'=>"Arabic", 'ru'=>"Russian", 'zh'=>"Chinese"); ?>
                    <select id="wwl_site_lang_code" name="wwl_site_lang_code" style="font-family: 'Courier New', Courier, mono; font-size: 1.5em;" >
                    <?php foreach($langs as $code => $name) { ?>
                    <option value="<?php echo $code; ?>" <?php if ($wwl_site_lang_code == $code) echo ' selected="selected"';?>><?php echo $name; ?></option>
                    <?php }?>
                    </select>
                </p>
                <h3><label for="wwl_site_share"><?php _e('Translations can be contributed by:'); ?></label></h3>
                <p> <br />
                    <label><input name="wwl_site_share" id="wwl_site_share" value="0" type="radio" <?php if ($wwl_site_share == 0) echo ' checked="checked" '; ?> /> <?php _e('everybody'); ?></label>
                    <label><input name="wwl_site_share" id="wwl_site_share" value="1" type="radio" <?php if ($wwl_site_share == 1) echo ' checked="checked" '; ?> /> <?php _e('logged in users'); ?></label>
                    <label><input name="wwl_site_share" id="wwl_site_share" value="2" type="radio" <?php if ($wwl_site_share == 2) echo ' checked="checked" '; ?> /> <?php _e('users that have passcode'); ?></label>
                </p>
            <p><label><input name="wwl_enabled" id="wwl_enabled" value="true" type="checkbox" <?php if ($wwl_site_guid && $wwl_enabled == 'true') echo ' checked="checked" '; ?> /> <?php _e('Enable Worldwide Lexicon translator.'); ?></label></p>
            <p class="submit"><input type="submit" name="submit" value="<?php _e('Update options &raquo;'); ?>"/></p>
            <?php } else { ?>
            <p><?php printf(__('You should register First')); ?></p>
            <p class="submit"><input type="submit" name="submit" value="<?php _e('Register'); ?>" /></p>
            <?php } ?>

        </form>
    </div>

</div>
<?php
}

if ( !get_option('wwl_site_guid') && !$wwl_site_guid && !isset($_POST['submit']) ) {
    function wwl_warning() {
        echo "
        <div id='wwl-warning' class='updated fade-ff0000'><p><strong>".__('WWL Translator is not active.')."</strong> ".sprintf(__('You must <a href="%1$s">enter your WorldWideLanguage.org Site GUID</a> for it to work.'), "plugins.php?page=wwl-key-config")."</p></div>
        <style type='text/css'>
        #adminmenu { margin-bottom: 5em; }
        #wwl-warning { position: absolute; top: 7em; }
        </style>
        ";
    }
    add_action('admin_footer', 'wwl_warning');
    return;
}

function wwl_check($guid, $url) {
    $guid = urlencode($guid);
    $url = urlencode($url);
    $response = wwl_http_post("guid=$guid&url=$url", "/plugin/check/?guid=$guid&url=$url");
    return $response;
}
function wwl_change ($guid, $url, $lang, $share) {
    $guid = urlencode($guid);
    $url = urlencode( get_option('home') );
    $lang = urlencode($lang);
    $share = urlencode($share);
    $name = urlencode(get_option('blogname'));

    $response = wwl_http_post("lang=$lang&share=$share&guid=$guid&url=$url&name=$name", "/plugin/change/");
    return $response;
}
function wwl_register () {
    global $wwl_site_guid, $wwl_site_url, $wwl_site_lang_code, $wwl_site_share, $wwl_enabled;

    $url = urlencode( get_option('home') );
    $guid = preg_replace('/[^a-zA-Z0-9.]/', '', get_option('home'));

    $response = wwl_http_post("guid=$guid&url=$url", "/plugin/register/");
    return $response;
}

// Returns array with headers in $response[0] and body in $response[1]
function wwl_http_post($request, $path) {
    global $wp_version;

    $http_request  = "POST $path HTTP/1.0\r\n";
    $http_request .= "Host: ".WWL_PLUGIN_HOST."\r\n";
    $http_request .= "Content-Type: application/x-www-form-urlencoded; charset=" . get_option('blog_charset') . "\r\n";
    $http_request .= "Content-Length: " . strlen($request) . "\r\n";
    $http_request .= "User-Agent: WordPress/$wp_version | WWL Translator/2.0\r\n";
    $http_request .= "\r\n";
    $http_request .= $request;

    $response = array('result'=>'Could not connect to server');
    if( false != ( $fs = fsockopen(WWL_PLUGIN_HOST, 80, $errno, $errstr, 10) ) ) {
        fwrite($fs, $http_request);

        while ( !feof($fs) )
            $response .= fgets($fs, 1160); // One TCP-IP packet
        fclose($fs);

        $response = explode("\r\n\r\n", $response, 2);
        $response = unserialize($response[1]);
    } else {
        echo "Error: $fs<br /><pre>Request: $http_request</pre>";

    }
    return $response;
}


/**
 * Format string in "key==value,,ke2==value2" format
 *
 * @param array $array array to format
 * @return string
 */
function toWWL($array) {
    $glue = array();
    foreach($array as $key => $value) {
        $glue[] = "$key==$value";
    }
    return join(',,', $glue);
}

function wwl_content ($str) {
    static $inites = false;
    global $wwl_site_guid, $wwl_site_url, $wwl_site_lang_code, $wwl_site_share, $wwl_enabled, $wwl_title_path;
    if (!$inites) {
        $wwl_widget_server = WWL_WIDGET_HOST;
        $guid = md5(get_the_time() . ($permalink = get_permalink()));
        $permalink = rawurlencode($permalink);
        $divId = "wpMarxContainer$guid";
        $prefix = <<<HTML
            <script type="text/javascript" src="$wwl_widget_server/js/jquery.multy.js"></script>
            <script type="text/javascript" src="$wwl_widget_server/js/marx_0.9.6.js"></script>
            <script language="JavaScript" defer="defer" type="text/javascript">
                \$jQ(function() {
                    new marx.Widget({
                        site: "$wwl_site_guid",
                        guid: "$guid",
                        content: "#$divId",
                        title: "$wwl_title_path",
                        link: "$permalink"
                    });
                });
            </script>
            <div id="marxWidget"></div><div id="marxOverlay"></div><div id="marxModal" class="loading"><div id="lbContent"></div></div>
HTML;
        global $post;
        $str = $prefix . '<div id="'. $divId .'"><!--marxData{"'.toWWL(array('title'=>get_the_title(), 'author'=>get_the_author(), 'created'=>$post->post_date_gmt)).'"}--><!--marxBegin-->'. $str .'<!--marxEnd--></div>';
    }
    return $str;
}

function wwl_multi_content ($str) {
    static $page = 0;
    global $wwl_site_guid, $wwl_site_url, $wwl_site_lang_code, $wwl_site_share, $wwl_enabled, $wwl_js_name;
    $prefix = '';
    if ($page++ == 0) {
        $wwl_widget_server = WWL_WIDGET_HOST;
        $prefix .= <<<HTML
    <script type="text/javascript" src="$wwl_widget_server/js/jquery.multy.js"></script>
<script type="text/javascript" src="$wwl_widget_server/js/$wwl_js_name"></script>
<script language="JavaScript" defer="defer" type="text/javascript">
    \$jQ(function(){
        wwl.initialize({site: "$wwl_site_guid"});
    });
</script>
HTML;
    }
    $guid = md5(get_the_time() . ($permalink = get_permalink()));
    $divId = "wpWWLContainer$guid";
    $permalink = rawurlencode($permalink);
    $prefix .= <<<HTML
            <script language="JavaScript" defer="defer" type="text/javascript">
                \$jQ(function() {
                    wwl.widgets[$page] = new wwl.Widget({guid: "$guid", content: "#$divId", link: "$permalink"});
                });
            </script>
            <div id="$divId" class="marxWidget"></div>
HTML;
        return $prefix . $str;
}

function wwwl_get_caller_func($nf){
    $tr=debug_backtrace();
    for($i;$i<sizeof($tr);$i++)
        if( $tr[$i]["function"] == $nf) return true;
    return false;
}

function wwl_filter($str){
    if(wwwl_get_caller_func('wp_trim_excerpt')) return $str;
    if (is_page() || is_feed()) return $str;

    if (!is_single()) {
        return wwl_multi_content($str);
    } else {
        return wwl_content($str);
    }

}

if ($wwl_enabled) {
    add_filter('the_content', wwl_filter);
    add_filter('the_excerpt', wwl_filter);
}

