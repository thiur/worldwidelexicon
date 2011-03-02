//******************************************************************************
// Copyright (C) 2011 WorldWide Lexicon Inc.
// All rights reserved.
//
// http://www.worldwidelexicon.org
//
// The program contains proprietary information of WorldWide Lexicon Inc.,
// and is licensed subject to restrictions on use and distribution.
//******************************************************************************

// Version: beta.09

var dermundo = {

	sourceLang: "en",
	targetLang: "en",
	sourceUrl: null,
	ip: "99.199.174.74",
	loggedIn: false,
	loginTimer: null,
	rolloverTimer: null,
	helper: null,
	http: null,	

	// UI strings
	strings: {
		"dmundo.getTranslationsFailed" : "Oops! Unable to retrieve the translations for this page. Please press refresh to try again.",
		"dmundo.logout" : "Log out",
		"dmundo.status.translating" : "Getting translations...",
		"dmundo.status.error" : "Error getting translations",
		"dmundo.dialog.source" : "Source text",
		"dmundo.dialog.close" : "Close dialog",
		"dmundo.dialog.translation" : "Translation",
		"dmundo.dialog.submit" : "Submit Translation",
		"dmundo.dialog.login" : "Login below to translate!",
		"dmundo.dialog.score" : "Score",
		"dmundo.submitScoreFailed" : "Oops! Unable to submit your score. Please try again."
	},

	rightToLeftLanguages: ["ar" ,"fa", "ur", "iw", "he"], // iw is a synonym for he

	meta: [],			// metadata for the page ([0] - title, [1] - description, [2] - array of keywords)
	textNodes: [],		// array of text nodes on the page
	originals: [],		// array of original text contents of text nodes on the page
	prefixes: [],		// array of original text contents contain node prefixes
	postfixes: [],		// array of original text contents contain node postfixes
	translations: null,   // complete set of translations for the current language path

	getTranslatedUIstringByName: function(name) {
		var str = this.strings[name];
		if (str) {
			return str;
		} else {
			return "";
		}
	},
	
	setElementDir: function(elem, lang) {
		for (var i=0; i < this.rightToLeftLanguages.length; i++) {
			if (lang == this.rightToLeftLanguages[i]) {
				elem.setAttribute("dir", "rtl");
				return; 
			}
		}
		elem.setAttribute("dir", "ltr");
		return; 
	},
	
	getTranslation: function(st, tl) {
		var strs = this.tm[tl];
		if (!strs) {
			return null;
		} else {
			return strs[st];
		}
	},
	
	init: function() {

		if (window.XMLHttpRequest) {
			http = new XMLHttpRequest();
		} else if (window.ActiveXObject) {
			try {
				http = new ActiveXObject("Msxml2.XMLHTTP");
	 		} catch(e) {
		  		try {
					http = new ActiveXObject("Microsoft.XMLHTTP");
				} catch(e) {
					throw(e);
				}
			}
		}
		if (!http && typeof XMLHttpRequest!='undefined') {
			try {
				http = new XMLHttpRequest();
			} catch (e) {
				http = false;
			}
		}
		if (!http && window.createRequest) {
			try {
				http = window.createRequest();
			} catch (e) {
				http = false;
			}
		}
		if (!http) {
			throw('init failed');
		}	
	},

	uninit: function() {
	},

	callGetService: function(service, params, callback) {
		var secure = false;
		var query = "", parts = [];

		for(var i = 0; i < params.length; i++) {
			params[i][1] = encodeURIComponent(params[i][1]);
			parts.push(params[i].join("="));
		}

		query = parts.join("&");

		var http = new XMLHttpRequest();
		http.open("GET", (secure ? "https://" : "http://") + dermundo_serviceUrl + service + "?" + query, true);
		http.onreadystatechange = function() {
			if(http.readyState == 4) {
				if(http.status == 200) {
					callback(http.responseText);
				} else {
					callback(http.responseText, true);
				}
			}
		};
		http.send();
	},

	callPostService: function(service, params, callback) {
		var secure = false;
		var query = "", parts = [];

		for(var i = 0; i < params.length; i++) {
			params[i][1] = encodeURIComponent(params[i][1]);
			parts.push(params[i].join("="));
		}

		query = dmundo_utf8_encode(parts.join("&"));

		var http = new XMLHttpRequest();
		http.open("POST", (secure ? "https://" : "http://") + dermundo_serviceUrl + service, true);
		//http.channel.loadFlags |= this.Ci.nsIRequest.LOAD_BYPASS_CACHE;

		http.setRequestHeader("Content-Type", "application/x-www-form-urlencoded; charset=utf-8");
		http.setRequestHeader("Content-Length", query.length);
		http.setRequestHeader("Accept-Charset", "UTF-8");

		http.onreadystatechange = function() {
			if (http.readyState == 4) {
				if (http.status == 200) {
					callback(http.responseText);
				} else {
					callback(http.responseText, true);
				}
			}
		};
		http.send(query);
	},

	callExternal: function(url, params, callback, type) {
		var query = "", parts = [];

		if (params) {
			for(var i = 0; i < params.length; i++) {
				for(var j = 0; j < params[i].length; j++) {
					params[i][j] = String(params[i][j]).replace(/ /g, "+");
					params[i][j] = encodeURI(params[i][j]);
				}
				parts.push(params[i].join("="));
			}
			query = parts.join("&");
			//query = query.replace(/\//g, "%2F");
		}

        var http = new XMLHttpRequest();
		http.open("GET", url + query, true);
		if (type) {
			http.overrideMimeType(type);
		}
		http.setRequestHeader("Content-Type", type || "application/x-www-form-urlencoded; charset=utf-8");

		http.onreadystatechange = function() {
			if (http.readyState == 4) {
				if(http.status == 200) {
					callback((type && (type == "text/xml")) ? http.responseXML : http.responseText);
				} else {
					callback(http.responseText, false);
				}
			}
		};

		http.send();
	},

	onContentLoaded: function() {
		var self = this;
		if (this.checkBrowserCompatibility()) {
			this.initSourceUrl();
			this.setDefaultTargetLang();
			this.parseDoc();
		}
	},

	checkBrowserCompatibility: function() {
		var compatible = true;
		if (!document.createTreeWalker) {
			compatible = false;
		}
		if (!compatible) {
			alert("Sorry! Your browser is not compatible with Der Mundo.\nPlease upgrade to Firefox or Chrome.");
		}
		return compatible;
	},
	
	onLangSelect: function() {
		var sel = document.getElementById("dmundo_sourceLangSelect"); 
		this.sourceLang = sel.value;
		sel = document.getElementById("dmundo_targetLangSelect"); 
		this.targetLang = sel.value;

		dmundo_createCookie('lastTargetLang', this.targetLang, 999);

		this.translateDocument();
	},
	
	setDefaultTargetLang: function() {
		var sel = document.getElementById("dmundo_targetLangSelect"); 
		var tl = dmundo_readCookie('lastTargetLang');
		if (tl) {
			sel.value = tl;
		} else {
			sel.value = 'en';
		}
	},
	
	initSourceUrl: function() {
		this.sourceUrl = window.location.pathname;
		if (this.sourceUrl.indexOf("/") == 0) {
			this.sourceUrl = this.sourceUrl.substring(1);
		}
	},
	
	setSourceLang: function(langId) {
		var sel = document.getElementById("dmundo_sourceLangSelect"); 
		sel.value = langId;
		this.onLangSelect();
	},

	startLoginTimer: function() {
		var self = this;
		this.loginTimer = setTimeout(function() {
			self.loginTimer = 0;
			FB.getLoginStatus(function(response) {
				if (response.session) {
					self.onLogin();
				} else {
					self.startLoginTimer();
				}
			});
		},
		5000);
	},

	onLogin: function() {
		this.loggedIn = true;
	},
	
	parseDoc: function() {

		function nodeHasParent(node, parentTag) {
			parentTag = parentTag.toLowerCase();

			while(node && node.parentNode && node.parentNode.tagName) {
				if(node.parentNode.tagName.toLowerCase() == parentTag) {
					return true;
				}
				node = node.parentNode;
			}
			return false;
		}

		var doc = document;
		
		if (!this.helper) {
			this.helper = document.getElementById("dmundo_tmp_node");
		}
		
		var treeWalker = this.getTreeWalkerFromDoc(doc);

		var priority1Nodes = [], priority2Nodes = [], otherNodes = [];
		var priority1Texts = [], priority2Texts = [], otherTexts = [];
		var priority1Prefixes = [], priority2Prefixes = [], otherPrefixes = [];
		var priority1Postfixes = [], priority2Postfixes = [], otherPostfixes = [];
		var priorityIndex = 0;

		while(treeWalker.nextNode()) {
			var text = treeWalker.currentNode.textContent;

			var leftWhitespace = dmundo_extractLeftWhitespace(text);
			var rightWhitespace = dmundo_extractRightWhitespace(text);
			text = dmundo_trim(text);

			if (text && text.length) {
				var isTag = (nodeHasParent(treeWalker.currentNode, "h1") || nodeHasParent(treeWalker.currentNode, "h2") || nodeHasParent(treeWalker.currentNode, "h3") ||
							 nodeHasParent(treeWalker.currentNode, "h4") || nodeHasParent(treeWalker.currentNode, "h5") || nodeHasParent(treeWalker.currentNode, "h6"));
				if (isTag && (priorityIndex++ < 10)) {
					priority1Nodes.push(treeWalker.currentNode);
					priority1Texts.push(text);
					priority1Prefixes.push(leftWhitespace);
					priority1Postfixes.push(rightWhitespace);
				} else if(isTag || (text.split(" ").length > 4)) {
					priority2Nodes.push(treeWalker.currentNode);
					priority2Texts.push(text);
					priority2Prefixes.push(leftWhitespace);
					priority2Postfixes.push(rightWhitespace);
				} else {
					otherNodes.push(treeWalker.currentNode);
					otherTexts.push(text);
					otherPrefixes.push(leftWhitespace);
					otherPostfixes.push(rightWhitespace);
				}
			}
		}

		this.textNodes = priority1Nodes.concat(priority2Nodes).concat(otherNodes);
		this.originals = priority1Texts.concat(priority2Texts).concat(otherTexts);
		this.prefixes = priority1Prefixes.concat(priority2Prefixes).concat(otherPrefixes);
		this.postfixes = priority1Postfixes.concat(priority2Postfixes).concat(otherPostfixes);

		if(!this.textNodes.length) {
			return;
		}
		
		for(var i = 0; i < this.textNodes.length; i++) {
			var node = this.textNodes[i];
			var parent = node.parentNode;

			if((parent.childNodes.length == 1) && (parent.childNodes[0] == node)) {
				continue;
			}

			var span = doc.createElement("dmundo_translated");
			span.textContent = this.prefixes[i] + this.originals[i] + this.postfixes[i];
			span.style.display = "inline";
			span.style.position = "static";
			span.style.float = "none";
			span.style.margin = "0px";
			span.style.padding = "0px";
			span.style.backgroundColor = "transparent";
			span.style.background = "none";
			span.style.border = "0px";

			parent.replaceChild(span, this.textNodes[i]);
			this.textNodes[i] = span;
		}

		var self = this;

		// Create a div to house the translation and voting interface:
		var overlay = doc.createElement("dmundo");
		overlay.id = "dmundo_overlay";
		overlay.innerHTML = "<table><tr><td>" + this.getTranslatedUIstringByName("dmundo.dialog.source") + ":</td>" + "<td style=\"text-align:right\"><input id=\"dmundo_overlay_close\" type=\"image\" title=\"" + this.getTranslatedUIstringByName("dmundo.dialog.close") + "\" src=\"http://worldwidelexicon.appspot.com/image/button-close.png\" width=\"12px\" height=\"12px\"></input></td></tr>" +
								"<tr><td colspan=\"2\"><textarea id=\"dmundo_overlay_st\" readonly=\"true\"></textarea></td></tr>" +
								"<tr><td colspan=\"2\">" + this.getTranslatedUIstringByName("dmundo.dialog.translation") + ":</td></tr>" +
								"<tr><td colspan=\"2\"><textarea id=\"dmundo_overlay_tt\" ></textarea><span style=\"display: none\"></span></td></tr>" +
								"<tr><td nowrap>" + this.getTranslatedUIstringByName("dmundo.dialog.score") + ": <div id=\"dmundo_voteDiv\"></div></td><td style=\"text-align:right; padding-top:5px\"><input id=\"dmundo_overlay_submit\" class=\"dmundo_button\" type=\"button\" value=\"" + this.getTranslatedUIstringByName("dmundo.dialog.submit") + "\" /><span id=\"dmundo_overlay_login\">" +this.getTranslatedUIstringByName("dmundo.dialog.login") + "</span></td></tr>" +
						"</table>";
		doc.body.appendChild(overlay);

		var close = doc.getElementById("dmundo_overlay_close");
		var stArea = doc.getElementById("dmundo_overlay_st");
		var ttArea = doc.getElementById("dmundo_overlay_tt");
		var submit = doc.getElementById("dmundo_overlay_submit");
		
		// Add score widget
		dmundo_jVote = new dmundo_jVote('dmundo_voteDiv', {max:6, min:2, labels:['1','2','3','4','5','0']});

		// Attach events to the overlay:
		derMundoAttachEvent(overlay, "mouseover", false, function() {
			if(self.rolloverTimer) {
				clearTimeout(self.rolloverTimer);
				self.rolloverTimer = 0;
			}
		});

		derMundoAttachEvent(overlay, "mouseout", false, function() {
			self.rolloverTimer = setTimeout(function() {
				if(!stArea.focused && !ttArea.focused) {
					overlay.style.display = "none";
					self.rolloverTimer = 0;
				}
			},
			500);
		});

		// Attach events to the overlay elements:
		derMundoAttachEvent(stArea, "focus", false, function() {
			this.focused = true;
		});
		derMundoAttachEvent(stArea, "blur", false, function() {
			this.focused = false;
		});
		derMundoAttachEvent(ttArea, "focus", false, function() {
			this.focused = true;
		});
		derMundoAttachEvent(ttArea, "blur", false, function() {
			this.focused = false;
		});

		// Submit translation:
		var submit = doc.getElementById("dmundo_overlay_submit");
		derMundoAttachEvent(submit, "click", false, function() {
			var tt = ttArea.value;
			if (tt) {
				tt = dmundo_trim(tt);
			}
			
			// Prevent blank translations
			if (!tt || tt.length == 0) {
				return;
			}
			
			// Prevent google translations
			if (tt.indexOf("Google Translation:") == 0) {
				return;
			}
			
			dermundo.callPostService("/wwl/submit", [["url", self.sourceUrl],
											  ["sl",     self.sourceLang],
											  ["tl",     self.targetLang],
											  ["st",     stArea.value],
											  ["tt",     tt],
											  ["output", "text"]
											 ],
									function(response, failed) {
										// Update the text node:
										self.restoreTextNode(overlay.derMundoIndex);
										self.updateTextNode(overlay.derMundoIndex, self.textNodes[overlay.derMundoIndex], tt, overlay.derMundoGuid);
										overlay.style.display = "none";
									}
								);
		});

		// Close dialog:
		var close = doc.getElementById("dmundo_overlay_close");
		derMundoAttachEvent(close, "click", false, function() {
			overlay.style.display = "none";
		});

		this.translateDocument(doc);
		this.detectSourceLang();
	},

	// Retrieves all (human-made) translations for the current page:
	translateDocument: function(doc) {

		var self = this;

		this.setStatus(this.getTranslatedUIstringByName("dmundo.status.translating"));
		this.showProgressIndicator();
		this.translations = null;

		this.callGetService("/u", [
								   ["sl",  dermundo.sourceLang],
								   ["tl",  dermundo.targetLang],
								   ["url", dermundo.sourceUrl],
								   ["output", "json"]
								  ],
							function(response, failed) {
								self.hideProgressIndicator();
								if(failed) {
									self.getTranslationsFailed();
									return;
								}
								var obj = null;
								try {
									obj = eval('(' + response + ')');
								} catch(e) {
									self.getTranslationsFailed(e);
									return; 
								}

								self.setStatus("");
								self.enableLangSelect();

								self.translations = new Array();
								if (obj) {
									for (var i = 0; i < obj.length; i++) {
										var record = obj[i];
										if (record.sl != self.sourceLang) {
											continue;
										}
										if (record.tl != self.targetLang) {
											continue;
										}
										if (!self.translations) {
											self.translations = new Array();
										}
										if (!self.translations[record.st]) { // only use most recent translation
											self.translations[record.st] = record;
										}
									}
								}
								self.applyTranslations(self.doc);
							});
	},
	
	getTranslationsFailed: function(e) {
		this.setStatus("Error getting translations");
		alert(this.getTranslatedUIstringByName("dmundo.getTranslationsFailed"));
	},

	detectSourceLang: function() {

		var self = this;
		
		var sample = "";
		for (var i = 0; i < this.originals.length; i++) {
			if (sample.length > 256) {
				break;
			}
			var st = this.originals[i];
			sample += st + ", ";
		}

		this.callGetService("/wwl/mt/detect", [
								   ["q",  sample],
								   ["output", "json"]
								  ],
							function(response, failed) {
								if(failed) {
									return;
								}
								var obj = null;
								try {
									obj = eval('(' + response + ')');
									self.setSourceLang(obj.responseData.language);
								} catch(e) {
									return; 
								}
							});
	},

	applyTranslations: function(doc) {

		var numCompleted = 0;
		for (var i = 0; i < this.originals.length; i++) {
			var tt = '';
			var guid = null;
			if (this.targetLang != this.sourceLang) {
				var st = this.originals[i];
				if (this.translations) {
					var tln = this.translations[st];
					if (tln && tln.tt) {
						tt = tln.tt;
						guid = tln.guid;
						numCompleted++;
					}
				}
			}
			this.updateTextNode(i, this.textNodes[i], tt, guid);
		}

		if (this.targetLang != this.sourceLang) {
			this.setStatus("Percent translated: " + (Math.round(numCompleted / this.originals.length * 100)) + "%");
		} else {
			this.setStatus("");
		}
	},

	getTreeWalkerFromDoc: function(doc) {
		function nodeIsInToolbar(node) {
			var curNode = node;
			while (curNode && curNode.parentNode) {
				if (curNode.parentNode.id && (curNode.parentNode.id.toLowerCase() == "dmundo")) {
					return true;
				}
				curNode = curNode.parentNode;
			}
			return false;
		}
		
		function nodeIsScript(node) {
			while(node) {
				if(node.tagName && ((node.tagName.toLowerCase() == "script") || (node.tagName.toLowerCase() == "noscript"))) {
					return true;
				}
				node = node.parentNode;
			}
			return false;
		}

		function nodeIsStyle(node) {
			while(node) {
				if(node.tagName && (node.tagName.toLowerCase() == "style")) {
					return true;
				}
				node = node.parentNode;
			}
			return false;
		}

		function textIsInvalid(text) {
			if(text.length == 0) {
				return true;
			}
			var text_ = text.replace(/(^\s+)|(\s+$)/g, "");
			if(text_.length == 0) {
				return true;
			}
			if(text_.replace(/[\d\s\[\]\(\)\.\{\}\+\-=\\\/%&:,\?|!~]/g, "").length == 0) {
				return true;
			}
			return false
		}

		var treeWalker = document.createTreeWalker(
			doc.body, 
			NodeFilter.SHOW_TEXT, 
			{ 
				acceptNode: function(node) {
					var fail = (node.parentNode == null);
					if(!fail) {
						fail = nodeIsInToolbar(node);
					}
					if(!fail) {
						fail = nodeIsScript(node);
					}
					if(!fail) {
						fail = nodeIsStyle(node);
					}
					if(!fail) {
						fail = textIsInvalid(node.textContent);
					}
					return fail ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT;
				}
			},
			false);

		return treeWalker;
	},

	setStatus: function(msg) {
		var status = document.getElementById("dmundo_bar_status"); 
		status.textContent = msg;
	},
	
	showProgressIndicator: function() {
		var pi = document.getElementById("dmundo_spinner"); 
		pi.style.display = "inline";
	},

	hideProgressIndicator: function() {
		var pi = document.getElementById("dmundo_spinner"); 
		pi.style.display = "none";
	},
	
	enableLangSelect: function() {
		var ls = document.getElementById("dmundo_sourceLangSelect"); 
		ls.disabled = false;
		ls = document.getElementById("dmundo_targetLangSelect"); 
		ls.disabled = false;
	},
	
	disableLangSelect: function() {
		var ls = document.getElementById("dmundo_sourceLangSelect"); 
		ls.disabled = true;
		ls = document.getElementById("dmundo_targetLangSelect"); 
		ls.disabled = true;
	},
	
	onScore: function(score) {
		var self = this;
		var overlay = document.getElementById("dmundo_overlay");
		var guid = overlay.derMundoGuid;
		// TODO: hide scoring UI and show progress indicator
		if (!guid) {
			this.onScoreFail();
			return;
		}
		this.callGetService("/wwl/scores/vote", [
								   ["guid",  guid],
								   ["score",  score],
								   ["spam",  score == "0" ? "y" : "n"],
								   ["output", "text"]
								  ],
							function(response, failed) {
								if(failed) {
									self.onScoreFail();								
									return;
								}
								self.onScoreSuccess();								
							});		
	},

	onScoreSuccess: function() {
		// TODO: show "score success" text, hide progress indicator
		alert('Thanks!');
	},

	onScoreFail: function() {
		// TODO: restore score UI, hide progress indicator
		alert(this.getTranslatedUIstringByName("dmundo.submitScoreFailed"));
	},
		
	// Utility methods for translation overlay:
	attachShowOverlay: function(node, translation, index, guid) {
		if(!node || !node.addEventListener) return;

		var self = this;
		var doc = document;

		derMundoAttachEvent(node, "mouseover", false, function(event) {
			if (self.sourceLang == self.targetLang) {
				return;
			}

			if (self.rolloverTimer) {
				clearTimeout(self.rolloverTimer);
				self.rolloverTimer = 0;
			}

			var initX = 0, initY = 0, ct_ = node;
			if (ct_.offsetParent) {
				while (ct_.offsetParent) {
					initX += ct_.offsetLeft;
					initY += ct_.offsetTop;
					ct_ = ct_.offsetParent;
				}
			} else if (ct_.x) {
				initX += ct_.x;
				initY += ct_.y;
			}

			var overlay = doc.getElementById("dmundo_overlay");
			var stArea = doc.getElementById("dmundo_overlay_st");
			var ttArea = doc.getElementById("dmundo_overlay_tt");
			var submitButton = doc.getElementById("dmundo_overlay_submit");
			var loginText = doc.getElementById("dmundo_overlay_login");

			self.rolloverTimer = setTimeout(function() {

				overlay.derMundoIndex = index;
				overlay.derMundoGuid = guid;

				var st = self.originals[index];

				stArea.value = self.originals[index];
				self.setElementDir(stArea, self.sourceLang);
				
				ttArea.value = translation;
				self.setElementDir(ttArea, self.targetLang);

				if (self.loggedIn) {
					ttArea.readOnly = false;
					submitButton.style.display = "inline";
					loginText.style.display = "none";
					
					if (!translation || translation.length == 0) {
						self.getMachineTranslation(st, index);
					}
					
				} else {
					ttArea.readOnly = true;
					submitButton.style.display = "none";
					loginText.style.display = "inline";
				}

				overlay.style.display = "block";
				var top = initY + (((event.clientY + overlay.offsetHeight) > document.body.clientHeight) ? (-1 * overlay.offsetHeight) : node.offsetHeight);
				if (top < 0) {
					top = 0;
				}
				overlay.style.top = top + "px";
				var left = initX + (((initX + overlay.offsetWidth) < doc.body.scrollWidth) ? 0 : (node.offsetWidth - overlay.offsetWidth));
				if (left < 0) {
					left = 0;
				}
				overlay.style.left = left + "px";
				
				self.rolloverTimer = 0;
			},
			1000);
		});

		derMundoAttachEvent(node, "mouseout", false, function() {
			if(self.rolloverTimer) {
				clearTimeout(self.rolloverTimer);
				self.rolloverTimer = 0;
			} else {
				self.rolloverTimer = setTimeout(function() {
					var overlay = doc.getElementById("dmundo_overlay");
					overlay.style.display = "none";
					self.rolloverTimer = 0;
				},
				500);
			}
		});
	},

	getMachineTranslation: function(st, index) {
		var self = this;
		this.callGetService("/wwl/mt", [
								   ["sl",  this.sourceLang],
								   ["tl",  this.targetLang],
								   ["st", st],
								   ["output", "json"]
								  ],
							function(response, failed) {
								if(failed) {
									return;
								}
								var obj = null;
								try {
									obj = eval('(' + response + ')');
								} catch(e) {
									return; 
								}
								if (obj.tt && obj.tt.length > 0) {
									self.showMachineTranslation(index, obj.tt);
								}
							});
	},
	
	showMachineTranslation: function(index, translation) {
		if (!translation || translation.length == 0) {
			return;
		}
		var overlay = document.getElementById("dmundo_overlay");
		if (index != overlay.derMundoIndex) {
			return;
		}
		var ttArea = document.getElementById("dmundo_overlay_tt");
		if (ttArea.value && ttArea.value.length > 0) {
			return;
		}
		ttArea.value = "Google Translation:\n" + translation;
	},

	updateTextNode: function(index, node, translation, guid) {

		if (translation && translation.length > 0) {
			this.helper.innerHTML = translation;
			translation = this.helper.textContent;
			if(!node.tagName && node.parentNode) {
				node.parentNode.style.overflow = "auto";
			} else {
				node.style.overflow = "auto";
			}
			node.textContent = this.prefixes[index] + translation + this.postfixes[index];
		}
		
		if(!node.tagName && node.parentNode) {
			this.setElementDir(node.parentNode, this.targetLang);
			this.attachShowOverlay(node.parentNode, translation, index, guid);
		} else {
			this.setElementDir(node, this.targetLang);
			this.attachShowOverlay(node, translation, index, guid);
		}
	},

	restoreTextNode: function(index) {
		var node = this.textNodes[index];
		var parent = node.parentNode;

		if(node.nodeType == 3) {
			parent.textContent = this.prefixes[index] + this.originals[index] + this.postfixes[index];
			this.textNodes[index] = parent.firstChild;
		} else {
			var txt = node.ownerDocument.createTextNode(this.prefixes[index] + this.originals[index] + this.postfixes[index]);
			parent.replaceChild(txt, node);
			this.textNodes[index] = txt;
		}
	}
};

function derMundoAttachEvent(obj, evt, useCapture, fnc){
	if (!useCapture) {
		useCapture = false;
	}
	if (obj.addEventListener) {
		obj.addEventListener(evt, fnc, useCapture);
		return true;
	} else if (obj.attachEvent) {
		return obj.attachEvent("on" + evt, fnc);
	}
} 

// Attach load/unload events
derMundoAttachEvent(window, "load", false, function() { dermundo.init();  });
derMundoAttachEvent(window, "unload", false, function() { dermundo.uninit() });

// Cross-browser attach DOMContentLoaded event
(function(i) {var u =navigator.userAgent;var e=/*@cc_on!@*/false; var st = 
setTimeout;if(/webkit/i.test(u)){st(function(){var dr=document.readyState;
if(dr=="loaded"||dr=="complete"){i()}else{st(arguments.callee,10);}},10);}
else if((/mozilla/i.test(u)&&!/(compati)/.test(u)) || (/opera/i.test(u))){
document.addEventListener("DOMContentLoaded",i,false); } else if(e){     (
function(){var t=document.createElement('doc:rdy');try{t.doScroll('left');
i();t=null;}catch(e){st(arguments.callee,0);}})();}else{window.onload=i;}})(derMundoOnContentLoaded);
function derMundoOnContentLoaded() {dmundo_addToolbar(); dermundo.onContentLoaded();}

// Voting widget: adapted from jVote
function dmundo_jVote(parentId, settings)
{
	this.locked = false;
	this.images = [];
	this.settings = settings;
	this.parentId = parentId;
	this.init();
}

dmundo_jVote.prototype.init = function() {
	var that = this;
	for (var i = 0, e = this.settings.max; i < e; i++) {
		var image = document.createElement('img');
		this.images[i] = image;
		image.value = this.settings.labels[i];
		image.alt = this.settings.labels[i];
		image.style.cursor = 'pointer';
		image.onmouseover = function() {
			if(that.locked) {
				return;
			}
			that.set(this);
		};
		image.onclick = function(evnt) {
			if(that.locked) {
				return;
			}
			var eEvent = evnt || window.event;
			dermundo.onScore(this.value);
		};
		document.getElementById(this.parentId).appendChild(image);
	}
	this.set(this.images[this.settings.min]);
};

dmundo_jVote.prototype.set = function(domImage) {
	domImage.alt == '0' ? domImage.src = dermundo_imagesPath + 'spam_star.png' : domImage.src = dermundo_imagesPath + 'star.png';
	var next = domImage.nextSibling;
	while(next) {
		next.off = true;
		next.alt == '0' ? next.src = dermundo_imagesPath + 'spam_star.png' : next.src = dermundo_imagesPath + 'dark_star.png';
		next = next.nextSibling;
	}
	var prev = domImage.previousSibling;
	while(prev) {
		prev.off = false;
		prev.alt == '0' ? prev.src = dermundo_imagesPath + 'spam_star.png' : prev.src = dermundo_imagesPath + 'star.png';
		prev.src = domImage.alt == '0' ? dermundo_imagesPath + 'dark_star.png' : dermundo_imagesPath + 'star.png';
		prev = prev.previousSibling;
	}
};

dmundo_jVote.prototype.reset = function(num) {
	if(this.locked) {
		return;
	}
	var index = (num) ? num : this.settings.min;
	this.set(this.images[index-1]);
};

dmundo_jVote.prototype.lock = function() {
	this.locked = true;
};

dmundo_jVote.prototype.unLock = function() {
	this.locked = false;
};

function dmundo_addToolbar() {
	var toolbar = document.createElement("dmundo");
	toolbar.id = "dmundo";
	toolbar.className = "dmundo";
	toolbar.innerHTML = 
		'<div id="dmundo" class="dmundo">' +
		'	<div id="dmundo_bar" class="dmundo_bar">' +
		'		<div class="dmundo_bar_left">&nbsp;</div>' +
		'		<div class="dmundo_bar_middle">' +
		'			<div class="dmundo_bar_section">' +
		'				<div class="dmundo_bar_title"><a href="http://www.dermundo.com">Der Mundo</a></div>' +
		'			</div>' +
		'			<div class="dmundo_bar_section">' +
		'				<select id="dmundo_sourceLangSelect" onchange="dermundo.onLangSelect()" disabled="disabled">' +
		'					<option value="af">Afrikaans</option>' +
		'					<option value="ar">العربية</option>' +
		'					<option value="bg">български език</option>' +
		'					<option value="ca">Català</option>' +
		'					<option value="cs">česky</option>' +
		'					<option value="cy">Cymraeg</option>' +
		'					<option value="da">Dansk</option>' +
		'					<option value="de">Deutsch</option>' +
		'					<option value="el">Ελληνικά</option>' +
		'					<option value="en" selected="selected">English</option>' +
		'					<option value="es">Español</option>' +
		'					<option value="et">Eesti keel</option>' +
		'					<option value="eu">Euskara</option>' +
		'					<option value="fa">فارسی </option>' +
		'					<option value="fi">suomen kieli</option>' +
		'					<option value="fr">Français</option>' +
		'					<option value="ga">Gaeilge</option>' +
		'					<option value="gl">Galego</option>' +
		'					<option value="gu">ગુજરાતી</option>' +
		'					<option value="he">עברית </option>' +
		'					<option value="hi">हिन्दी </option>' +
		'					<option value="hr">Hrvatski</option>' +
		'					<option value="ht">Kreyòl ayisyen</option>' +
		'					<option value="hu">Magyar</option>' +
		'					<option value="id">Indonesian</option>' +
		'					<option value="is">Íslenska</option>' +
		'					<option value="it">Italiano</option>' +
		'					<option value="ja">日本語</option>' +
		'					<option value="jv">basa Jawa</option>' +
		'					<option value="ko">한국어</option>' +
		'					<option value="ku">كوردی</option>' +
		'					<option value="la">lingua latina</option>' +
		'					<option value="lt">lietuvių</option>' +
		'					<option value="lv">latviešu</option>' +
		'					<option value="mn">Монгол </option>' +
		'					<option value="ms">بهاس ملايو</option>' +
		'					<option value="my">Burmese</option>' +
		'					<option value="ne">नेपाली </option>' +
		'					<option value="nl">Nederlands</option>' +
		'					<option value="no">Norsk</option>' +
		'					<option value="oc">Occitan</option>' +
		'					<option value="pa">ਪੰਜਾਬੀ </option>' +
		'					<option value="po">polski</option>' +
		'					<option value="ps">پښتو</option>' +
		'					<option value="pt">Português</option>' +
		'					<option value="ro">română</option>' +
		'					<option value="ru">Русский</option>' +
		'					<option value="sk">slovenčina</option>' +
		'					<option value="sr">српски језик</option>' +
		'					<option value="sv">svenska</option>' +
		'					<option value="sw">Kiswahili</option>' +
		'					<option value="th">ไทย </option>' +
		'					<option value="tl">Tagalog</option>' +
		'					<option value="tr">Türkçe</option>' +
		'					<option value="uk">Українська</option>' +
		'					<option value="vi">Tiếng Việt</option>' +
		'					<option value="yi">ייִדיש</option>' +
		'					<option value="zh">中文</option>' +
		'				</select>' +
		'				<div class="dmundo_lang_dir">-&gt;</div>' +
		'				<select id="dmundo_targetLangSelect" onchange="dermundo.onLangSelect()" disabled="disabled">' +
		'					<option value="af">Afrikaans</option>' +
		'					<option value="ar">العربية</option>' +
		'					<option value="bg">български език</option>' +
		'					<option value="ca">Català</option>' +
		'					<option value="cs">česky</option>' +
		'					<option value="cy">Cymraeg</option>' +
		'					<option value="da">Dansk</option>' +
		'					<option value="de">Deutsch</option>' +
		'					<option value="el">Ελληνικά</option>' +
		'					<option value="en">English</option>' +
		'					<option value="es">Español</option>' +
		'					<option value="et">Eesti keel</option>' +
		'					<option value="eu">Euskara</option>' +
		'					<option value="fa">فارسی </option>' +
		'					<option value="fi">suomen kieli</option>' +
		'					<option value="fr">Français</option>' +
		'					<option value="ga">Gaeilge</option>' +
		'					<option value="gl">Galego</option>' +
		'					<option value="gu">ગુજરાતી</option>' +
		'					<option value="he">עברית </option>' +
		'					<option value="hi">हिन्दी </option>' +
		'					<option value="hr">Hrvatski</option>' +
		'					<option value="ht">Kreyòl ayisyen</option>' +
		'					<option value="hu">Magyar</option>' +
		'					<option value="id">Indonesian</option>' +
		'					<option value="is">Íslenska</option>' +
		'					<option value="it">Italiano</option>' +
		'					<option value="ja">日本語</option>' +
		'					<option value="jv">basa Jawa</option>' +
		'					<option value="ko">한국어</option>' +
		'					<option value="ku">كوردی</option>' +
		'					<option value="la">lingua latina</option>' +
		'					<option value="lt">lietuvių</option>' +
		'					<option value="lv">latviešu</option>' +
		'					<option value="mn">Монгол </option>' +
		'					<option value="ms">بهاس ملايو</option>' +
		'					<option value="my">Burmese</option>' +
		'					<option value="ne">नेपाली </option>' +
		'					<option value="nl">Nederlands</option>' +
		'					<option value="no">Norsk</option>' +
		'					<option value="oc">Occitan</option>' +
		'					<option value="pa">ਪੰਜਾਬੀ </option>' +
		'					<option value="po">polski</option>' +
		'					<option value="ps">پښتو</option>' +
		'					<option value="pt">Português</option>' +
		'					<option value="ro">română</option>' +
		'					<option value="ru">Русский</option>' +
		'					<option value="sk">slovenčina</option>' +
		'					<option value="sr">српски језик</option>' +
		'					<option value="sv">svenska</option>' +
		'					<option value="sw">Kiswahili</option>' +
		'					<option value="th">ไทย </option>' +
		'					<option value="tl">Tagalog</option>' +
		'					<option value="tr">Türkçe</option>' +
		'					<option value="uk">Українська</option>' +
		'					<option value="vi">Tiếng Việt</option>' +
		'					<option value="yi">ייִדיש</option>' +
		'					<option value="zh">中文</option>' +
		'				</select>' +
		'			</div>' +
		'			<div class="dmundo_bar_last_section">' +
		'				<div id="dmundo_bar_status" class="dmundo_bar_status"></div>' +
		'			</div>' +
		'			<div class="dmundo_bar_section">' +
		'				<div class="dmundo_spinner_container"><div id="dmundo_spinner" class="dmundo_spinner">&nbsp;</div></div>' +
		'			</div>' +
		'			<div class="dmundo_bar_last_section">' +
		'				<div id="dmundo_bar_loginStatus" class="dmundo_bar_login">' +
		'					<fb:login-button autologoutlink="true" perms="email, publish_stream, user_about_me"></fb:login-button>' +
		'				</div>' +
		'			</div>' +
		'		</div>' +
		'		<div class="dmundo_bar_right">&nbsp;</div>' +
		'	</div>' +
		'	<span id="dmundo_tmp_node" style="display:none"/>' +
		'</div>' +
		'<div id="fb-root"></div>';
		
	document.body.appendChild(toolbar);

	// Facebook login button
	window.fbAsyncInit = function() {
		FB.init({appId: "140342715320", status: true, cookie: true, xfbml: true});
		FB.Event.subscribe("auth.logout", function(response) {
				window.location.reload();
		});
		FB.Event.subscribe("auth.login", function(response) {
			dermundo.onLogin();
		});
		dermundo.startLoginTimer();
	};
	(function() {
			var e = document.createElement("script");
			e.type = "text/javascript";
			e.src = document.location.protocol + "//connect.facebook.net/en_US/all.js";
			e.async = true;
			document.getElementById("fb-root").appendChild(e);
	}());
}

function dmundo_trim(str) {
	return dmundo_ltrim(dmundo_rtrim(str));
}
 
function dmundo_ltrim(str, chars) {
	return str.replace(new RegExp("^[\\s]+", "g"), "");
}
 
function dmundo_rtrim(str, chars) {
	return str.replace(new RegExp("[\\s]+$", "g"), "");
}

function dmundo_extractLeftWhitespace(str) {
	var prefix = "";
	if (!str) {
		return prefix;
	}
	for (var i=0; i < str.length; i++) {
		if (str[i] == ' ' || str[i] == '\n' || str[i] == '\t' || str[i] == '\r') {
			prefix = prefix + str[i];
		}
	}
	return prefix;
}

function dmundo_extractRightWhitespace(str) {
	var postfix = "";
	if (!str) {
		return postfix;
	}
	for (var i=str.length-1; i > 0; i--) {
		if (str[i] == ' ' || str[i] == '\n' || str[i] == '\t' || str[i] == '\r') {
			postfix = str[i] + postfix;
		}
	}
	return postfix;
}

function dmundo_utf8_encode(string) {
	string = string.replace(/\r\n/g,"\n");
	var utftext = "";
 
	for (var n = 0; n < string.length; n++) {
 		var c = string.charCodeAt(n);
		if (c < 128) {
			utftext += String.fromCharCode(c);
		} else if((c > 127) && (c < 2048)) {
			utftext += String.fromCharCode((c >> 6) | 192);
			utftext += String.fromCharCode((c & 63) | 128);
		} else {
			utftext += String.fromCharCode((c >> 12) | 224);
			utftext += String.fromCharCode(((c >> 6) & 63) | 128);
			utftext += String.fromCharCode((c & 63) | 128);
		}
 	}
	return utftext;
}
 
function dmundo_utf8_decode(utftext) {
	var string = "";
	var i = 0;
	var c = c1 = c2 = 0;
 
	while ( i < utftext.length ) {
		c = utftext.charCodeAt(i);
		if (c < 128) {
			string += String.fromCharCode(c);
			i++;
		} else if((c > 191) && (c < 224)) {
			c2 = utftext.charCodeAt(i+1);
			string += String.fromCharCode(((c & 31) << 6) | (c2 & 63));
			i += 2;
		} else {
			c2 = utftext.charCodeAt(i+1);
			c3 = utftext.charCodeAt(i+2);
			string += String.fromCharCode(((c & 15) << 12) | ((c2 & 63) << 6) | (c3 & 63));
			i += 3;
		}
	}
 	return string;
}

function dmundo_createCookie(name,value,days) {
	if (days) {
		var date = new Date();
		date.setTime(date.getTime()+(days*24*60*60*1000));
		var expires = "; expires="+date.toGMTString();
	}
	else var expires = "";
	document.cookie = name+"="+value+expires+"; path=/";
}

function dmundo_readCookie(name) {
	var nameEQ = name + "=";
	var ca = document.cookie.split(';');
	for(var i=0;i < ca.length;i++) {
		var c = ca[i];
		while (c.charAt(0)==' ') c = c.substring(1,c.length);
		if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
	}
	return null;
}
