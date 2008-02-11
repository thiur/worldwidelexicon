<?php
	define('WWL_WIDGET_HOST', 'http://marx.worldwidelexicon.org');

	$title="The Gettysburg Address";
	$author="Abraham Lincoln";
	
	$permalink = "http://worldwidelexicon.org/phpdemo.php";
	$post_time = "2007-06-12 15:17:29";
	$wwl_site_guid = "foobar.com"; //$sl="en-us";
	$text="<p>Four score and seven years ago our fathers brought forth on this continent, a new nation, conceived in Liberty, and dedicated to the proposition that all men are created equal.</p>
<p>
Now we are engaged in a great civil war, testing whether that nation, or any nation so conceived and so dedicated, can long endure. We are met on a great battle-field of that war. We have come to dedicate a portion of that field, as a final resting place for those who here gave their lives that that nation might live. It is altogether fitting and proper that we should do this.</p>
<p>
But, in a larger sense, we can not dedicate -- we can not consecrate
-- we can not hallow -- this ground. The brave men, living and dead, who struggled here, have consecrated it, far above our poor power to add or detract. The world will little note, nor long remember what we say here, but it can never forget what they did here. It is for us the living, rather, to be dedicated here to the unfinished work which they who fought here have thus far so nobly advanced. It is rather for us to be here dedicated to the great task remaining before us -- that from these honored dead we take increased devotion to that cause for which they gave the last full measure of devotion -- that we here highly resolve that these dead shall not have died in vain -- that this nation, under God, shall have a new birth of freedom -- and that government of the people, by the people, for the people, shall not perish from the earth.</p>";

	// WWL integration code
	$wwl_widget_server = WWL_WIDGET_HOST;
	$guid = md5($post_time.$permalink); 
	$permalink = rawurlencode($permalink);
	$divId = "wpMarxContainer$guid";
	$prefix = <<<HTML
		<script type="text/javascript" src="$wwl_widget_server/js/jquery.multy.js"></script>
		<script type="text/javascript" src="$wwl_widget_server/js/marx_0.9.6.js"></script>
		<script type="text/javascript">
			\$jQ(function() {
				new marx.Widget({site: "$wwl_site_guid", guid: "$guid", content: "#$divId", title: "div.post:first h2 a", link: "$permalink"});
			});
		</script> 
		<div id="marxWidget"></div><div id="marxOverlay"></div><div id="marxModal" class="loading"><div id="lbContent"></div></div>
HTML;
	$data = "title==".$title.",,author==".$author.",,created==".$post_time;
	$str = $prefix.'<div id="'.$divId.'"><!--marxData{"'.$data.'"}--><!--marxBegin-->'.$text.'<!--marxEnd--></div>';
	
	// output the page
	echo("<style>img {border: none;}</style>");
	echo("<h2>".$title."</h2>");
	echo($str);
?>
<p><a href="phpdemo.phps">View source</a></p>