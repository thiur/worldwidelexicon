var wwl = {};
wwl.$ = function(id) {
	return document.getElementById(id) || false;
}
wwl.$hide = function(id) {
	if (wwl.$(id)) {
		wwl.$(id).style.display = "none";
	}
}
wwl.$show = function(id) {
	if (wwl.$(id)) {
		wwl.$(id).style.display = "inline";
	}
}
wwl.swap = function(id0, id1) {

	wwl.$hide('wwl-content-' + id1);
	wwl.$hide('wwl-title-' + id1);
	wwl.$show('wwl-content-' + id0);
	wwl.$show('wwl-title-' + id0);
	return false;
}
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
wwl.editing = {}
wwl.fixed = {}
wwl.edit = function(id) {
	wwl.fixTitle(id);
	//alert('Editing translation for post #' + id);
	var titleRoot = wwl.$('wwl-title-' + id);
	var contentRoot = wwl.$('wwl-content-' + id);
	var tspans = titleRoot ? titleRoot.getElementsByTagName("SPAN") : [];
	var spans = contentRoot ? contentRoot.getElementsByTagName("SPAN") : [];
	var si;
	
	var unsetEditable = function(elem) {
		if (/wwl-translated-fragment/.test(elem.className)) {
			var chunkId = elem.nextSibling.innerHTML;
			if (wwl.chunks[chunkId]) {
				elem.className = "wwl-translated-fragment";
				elem.onclick = null;
			}
		}
	}
	var setEditable = function(elem) {
		if (/wwl-translated-fragment/.test(elem.className)) {
			var chunkId = elem.nextSibling.innerHTML;
			if (wwl.chunks[chunkId]) {
				elem.className = "wwl-translated-fragment wwl-editing";
				elem.onclick = function() {
					wwl.showTranslatorWindow(this);
					return false;
				}
				elem.onmouseover = function() {
					var _this = this;
					setTimeout(function(){
						if (_this) {
							wwl.showTranslatorWindow(_this);
						}
					}, 800);
					this.onmouseout = function() {
						_this = null;
						return false;
					}
					return false;
				}
			}
		}
	}	
	
	if (wwl.editing[id]) {
		for (si in spans) {
			unsetEditable(spans[si]);
		}
		for (si in tspans) {
			unsetEditable(tspans[si]);
		}
		wwl.editing[id] = false;
		return false;
	}
	
	for (si in spans) {
		setEditable(spans[si]);
	}
	for (si in tspans) {
		setEditable(tspans[si]);
	}
	wwl.editing[id] = true;
	return false;
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
	    console.debug(this.nodeValue);
	});
}
wwl.showTranslatorWindow = function(sender) {
	var chunkId = sender.nextSibling.innerHTML;
	wwl.chunks[chunkId].translatedWithTags = sender.innerHTML;
		
	wwl.$("wwl-inline-editor-translated").disabled = false;
	wwl.$("wwl-inline-editor-update").disabled = false;
	
	wwl.$("wwl-inline-editor-title").innerHTML = "Edit " +  wwl.sourceLanguageName + " &rarr; " + wwl.targetLanguageName + " translation";
	
	wwl.$("wwl-inline-editor-original").innerHTML = wwl.chunks[chunkId].original;
	wwl.$("wwl-inline-editor-translated").value = wwl.chunks[chunkId].translated;

	wwl.$("wwl-inline-editor").style.display = "block";
	wwl.$("wwl-inline-editor-translated").style.height = (28 + wwl.$("wwl-inline-editor-original").offsetHeight) + "px";
	wwl.activeChunkId = chunkId;
	wwl.activeElement = sender;
	return false;
}
wwl.submitTranslation = function() {
	wwl.$("wwl-inline-editor-title").innerHTML = "Saving translation...";
	var text = wwl.$("wwl-inline-editor-translated").value;
	wwl.chunks[wwl.activeChunkId].translated = text;
	
	wwl.$("wwl-inline-editor-translated").disabled = true;
	wwl.$("wwl-inline-editor-update").disabled = true;

	// Use jQuery -- suppose it's included with Drupal
	$.post("/wwlex/post", {
		"text": text,
		"source": wwl.chunks[wwl.activeChunkId].original,
		"sourceWithTags": wwl.activeElement.innerHTML,
		"chunkId": wwl.activeChunkId,
		"tl": wwl.targetLanguage,
		"url": document.location.href
	}, function(data){
		if (data && data.translated && wwl.activeElement) {
			wwl.activeElement.innerHTML = data.translated;
		}
		wwl.hideTranslatorWindow();
	}, "json");

	return false;
}
wwl.hideTranslatorWindow = function() {
	wwl.$("wwl-inline-editor").style.display = "none";
	return false;
}
wwl.API = {}
wwl.API.clearCache = function() {

	$.post("/wwlex/clearcache", function(response) {
		alert("Cache cleared");
	});
	return false;
}

wwl.massSwitch = function(option, check) {
	for (var i in wwl.langs) {
		if (wwl.$(i + '_' + option + '_enable')) {
			wwl.$(i + '_' + option + '_enable').checked = check.checked;
		}
	}
}
wwl.massSelect = function(option, select) {
	
	for (var i in wwl.langs) {
		if (wwl.$(i + '_' + option + '_select')) {
			wwl.$(i + '_' + option + '_select').selectedIndex = select.selectedIndex;
		}
	}
	
}
wwl.init = function() {
	
}
wwl.init();
