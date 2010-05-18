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
wwl.editing = {}
wwl.edit = function(id) {
	
	
	var unsetEditable = function(elem) {
		if (/wwl-translated-fragment/.test(elem.className)) {
			var chunkId = elem.nextSibling.innerHTML;
			if (wwl.chunks[chunkId]) {
				elem.className = "wwl-translated-fragment";
				elem.onclick = null;
				elem.onmouseover = null;
			}
		}
	}
	var setEditable = function(elem) {
		if (/wwl-translated-fragment/.test(elem.className)) {
			var chunkId = elem.nextSibling.innerHTML;
			if (wwl.chunks[chunkId]) {
				elem.className = "wwl-translated-fragment wwl-editing";
				elem.onclick = function() {
					if (!wwl.editing[id]) return false;
					wwl.showTranslatorWindow(this);
					return false;
				}
				elem.onmouseover = function() {
					if (!wwl.editing[id]) return false;
					var _this = this;
					setTimeout(function(){
						if (_this) {
							wwl.showTranslatorWindow(_this);
						}
					}, 1000);
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
		wwl.processChunksForId(id, unsetEditable);
		wwl.editing[id] = false;
		return false;
	}
	
	wwl.processChunksForId(id, setEditable);
	wwl.editing[id] = true;
	return false;
}
wwl.processChunksForId = function(id, func) {
	var titleRoot = wwl.$('wwl-title-' + id);
	var contentRoot = wwl.$('wwl-content-' + id);
	var tspans = titleRoot ? titleRoot.getElementsByTagName("SPAN") : [];
	var spans = contentRoot ? contentRoot.getElementsByTagName("SPAN") : [];
	var si;
	
	for (si in spans) {
		func(spans[si]);
	}
	for (si in tspans) {
		func(tspans[si]);
	}
	
}
wwl.showTranslatorWindow = function(sender) {
	var chunkId = sender.nextSibling.innerHTML;
	wwl.chunks[chunkId].translatedWithTags = sender.innerHTML;
		
	wwl.$("wwl-inline-editor-translated").disabled = false;
	wwl.$("wwl-inline-editor-update").disabled = false;
	
	wwl.$("wwl-inline-editor-title").innerHTML = "Edit " +  wwl.sourceLanguageName + " &rarr; " + 	wwl.targetLanguageName + " translation";
	
	wwl.$("wwl-inline-editor-original").innerHTML = wwl.chunks[chunkId].original;
	wwl.$("wwl-inline-editor-translated").value = wwl.chunks[chunkId].translated;

	wwl.$("wwl-inline-editor").style.display = "block";
	wwl.$("wwl-inline-editor-translated").style.height = (28 + wwl.$("wwl-inline-editor-original").offsetHeight) + "px";
	wwl.activeChunkId = chunkId;
	wwl.activeElement = sender;
	wwl.$("wwl-inline-editor-mt").innerHTML = "Loading...";
	google.language.translate(wwl.chunks[chunkId].original, wwl.sourceLanguage, wwl.targetLanguage,
	    function(result) {
	       	if (result.translation) {
	           	wwl.$("wwl-inline-editor-mt").innerHTML  = result.translation;
	       	}
	    }
	);

	return false;
}
wwl.useMT = function() {
	wwl.$("wwl-inline-editor-translated").value = wwl.$("wwl-inline-editor-mt").innerHTML;
	return false;
}
wwl.submitTranslation = function() {
	wwl.$("wwl-inline-editor-title").innerHTML = "Saving translation...";
	var text = wwl.$("wwl-inline-editor-translated").value;
	wwl.chunks[wwl.activeChunkId].translated = text;
	
	wwl.$("wwl-inline-editor-translated").disabled = true;
	wwl.$("wwl-inline-editor-update").disabled = true;

	jQuery.post(wwl.ajaxurl, {
		"action": "wwl_update_translation",
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
	var data = {
		action: 'wwl_clear_cache'
	};
	if (typeof wwl.clr_ajaxurl == "undefined") {
		alert("This function is not supported");
		return false;
	}
	jQuery.post(wwl.clr_ajaxurl, data, function(response) {
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
wwl.renderTranslators = function() {
	var out = {};
	for (var i in wwl.chunks) {
		var meta = wwl.chunks[i].meta;
		var label = meta.username;
		if (label) {
			label += (meta.mtengine ? " (" + meta.mtengine + ")" : "");
		} else {
			label = 'not translated';
		}
		if (!meta.id) {
			continue;
		}
		meta.id = '' + meta.id;
		if (!out[meta.id]) {
			out[meta.id] = {};
		}
		if (!out[meta.id][label]) {
			out[meta.id][label] = [];
		}
		out[meta.id][label].push(i);
		
	}
	for (i in out) {
		if (wwl.$("wwl-translators-" + i)) {
			var list = [];
			for (var j in out[i]) {
				list.push(
					'<a href="#" onmouseover="wwl.highlightAuthor(this, ' + i + ');" onclick="wwl.toggleAuthorHighlight(this, ' + i + ');return false;">' + j + '</a>'
				);
			}
			wwl.$("wwl-translators-" + i).innerHTML = list.join(', ');
		}
	}
	wwl.translatorsMap = out;
}
wwl.toggleAuthorHighlight = function(sender, id) {
	if (/wwl-highlight/.test(sender.className)) {
		wwl.unHighlightAuthor(sender, id);
		sender.className = "";
	} else {
		wwl.highlightAuthor(sender, id);
		sender.className = "wwl-highlight";
		sender.onmouseout = null;
	}
}
wwl.highlightAuthor = function(sender, id) {
	sender.onmouseout = function() {
		wwl.unHighlightAuthor(sender, id);
	}
	var cIds = wwl.translatorsMap[id][sender.innerHTML];
	var highlight = function(elem) {
		if (/wwl-translated-fragment/.test(elem.className)) {
			if (!elem.nextSibling) {
				return; // should never happen
			}
			var chunkId = elem.nextSibling.innerHTML;
			if (wwl.chunks[chunkId] && wwl.inArray(cIds, chunkId)) {
				if (wwl.editing[id]) {
					elem.className = "wwl-translated-fragment wwl-editing wwl-highlight";
				} else {
					elem.className = "wwl-translated-fragment wwl-highlight";
				}
			}
		}
	}
	wwl.processChunksForId(id, highlight);
}
wwl.unHighlightAuthor = function(sender, id){
	var cIds = wwl.translatorsMap[id][sender.innerHTML];
	var unhighlight = function(elem) {
		if (/wwl-translated-fragment/.test(elem.className)) {
			if (!elem.nextSibling) {
				return; // should never happen
			}
			var chunkId = elem.nextSibling.innerHTML;
			if (wwl.chunks[chunkId] && wwl.inArray(cIds, chunkId)) {
				if (wwl.editing[id]) {
					elem.className = "wwl-translated-fragment wwl-editing";
				} else {
					elem.className = "wwl-translated-fragment";
				}
			}
		}
	}
	wwl.processChunksForId(id, unhighlight);
}
wwl.inArray = function(arr, el) {
	for (var i = 0; i < arr.length; i++) {
		if (arr[i] === el) {
			return true;
		}
	}
	return false;
}
wwl.init = function() {

	var onLoad = function() {
		wwl.renderTranslators();
	};
	if (window.attachEvent) {
		window.attachEvent('onload', onLoad);
	} else {
		window.addEventListener('load', onLoad, false);
	}
	
}
wwl.init();
