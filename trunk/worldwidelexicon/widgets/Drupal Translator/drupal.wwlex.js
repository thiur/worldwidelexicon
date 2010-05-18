wwl.showOriginal = function(id) {
	wwl.fixTitle(id);
	wwl.$hide('wwl-content-' + id);
	wwl.$hide('wwl-title-' + id);
	wwl.$show('wwl-content-' + id + '_tr');
	wwl.$show('wwl-title-' + id + '_tr');
	return false;
}
wwl.showTranslated = function(id) {
	wwl.fixTitle(id);
	wwl.$hide('wwl-content-' + id + '_tr');
	wwl.$hide('wwl-title-' + id + '_tr');
	wwl.$show('wwl-content-' + id);
	wwl.$show('wwl-title-' + id);
	return false;
}
wwl.fixed = {}
/*
 * Drupal needs titles hack so injecting it
 */
var supEdit = wwl.edit;
wwl.edit = function(id) {
	wwl.fixTitle(id);
	return supEdit(id);
}
var supHL = wwl.highlightAuthor;
wwl.highlightAuthor = function(sender, id) {
	wwl.fixTitle(id);
	return supHL(sender, id);
}
/*
 * This will break if:
 * 1. There are nodes with the same title on the page
 * 2. There are menu items with the same name 
 */
wwl.fixTitle = function(id) {
	if (wwl.fixed[id]) {
		return;
	}
	var t = $("#wwl-title-" + id +">span:first-child");

	var found = null;
	$("*").each(function(index){
	    if ($(this).html() == t.html() && $(this) != t){
	        found = $(this);
	        return false;
	    }
	});
	if (found) {
		found.html($("#wrap-wwl-title-" + id).html());
		$("#wrap-wwl-title-" + id).html('');
		wwl.fixed[id] = true;
	}
}
/*
 * Will use this to translate 
 * 
 */
wwl.findTextNodes = function() {
	$("span,a,p,div,h1,h2,h3,h4,h5").contents().filter(
	    function(){
	        return (this.nodeType === 3) && /\S/m.test(this.nodeValue);
	    })
	.each(function(){
	    //console.debug(this.nodeValue);
	});
}

