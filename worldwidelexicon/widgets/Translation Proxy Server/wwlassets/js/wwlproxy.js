
var wwlproxy = {};

wwlproxy.snippetID = -1;

//find all span tags with class isEditable and id as fieldname parsed to update script. add onclick function
wwlproxy.init = function() {
    if (!document.getElementsByTagName) {
        return;
    }
    var spans = document.getElementsByTagName("span");

    // loop through all span tags
    for (var i = 0; i < spans.length; i++) {
        var spn = spans[i];

        if (((' ' + spn.className + ' ').indexOf("wwl-is-editable") != -1) && (spn.id)) {

            spn.ondblclick = wwlproxy.showTranslatorForm;
            spn.title = "Double click to edit this translation.";
            
			// Can use this handler to determine what to do when a link is clicked... have to think this out better.
            spn.parentNode.onclick = function() { return true;  }
        }
    }
}


wwlproxy.showTranslatorForm = function( e ) {

	if (!e) var e = window.event;
	
	wwlproxy.snippetID = this.id;
	var target_text = this.innerHTML;
	var source_text = document.getElementById(this.id + "-src").innerHTML;

	document.getElementById("wwl-translator-title").innerHTML = "Edit translation";
	document.getElementById("wwl-translator-source-text").innerHTML = source_text;
	document.getElementById("wwl-translator-target-text").value = target_text;
	document.getElementById("wwl-translator-target-text").disabled = false;
	document.getElementById("wwl-lightbox").style.display = "block";

	return false;
}


wwlproxy.hideTranslatorForm = function() {
	document.getElementById("wwl-lightbox").style.display = "none";
	return false;
}


wwlproxy.submitTranslation = function() {

	document.getElementById("wwl-translator-title").innerHTML = "Saving translation...";
	document.getElementById("wwl-translator-target-text").disabled = true;

	var stext = document.getElementById("wwl-translator-source-text").innerHTML;
	var ttext = document.getElementById("wwl-translator-target-text").value;
	
	var mysack = new wwlproxysack(wwlproxy.ajaxURL);

	//mysack.execute = 1;
	mysack.method = 'POST';
	mysack.setVar("stext", stext);
	mysack.setVar("ttext", ttext);
	mysack.setVar("slang", wwlproxy.sourceLanguage);
	mysack.setVar("tlang", wwlproxy.targetLanguage);
	
	mysack.onError = function() { 
		wwlproxy.hideTranslatorForm();
	};
	
	mysack.onCompletion = function() {
		var target_element = document.getElementById(wwlproxy.snippetID);
		var result = null;

		try {
			eval ('result = ' + mysack.response);
		} catch (e) {}

		if(result) {
			target_element.innerHTML = ttext;	
		} else {}
				
		wwlproxy.hideTranslatorForm();
	}
	
	mysack.runAJAX();
	return false;
}

// Crossbrowser load function
wwlproxy.addEvent = function(elm, evType, fn, useCapture) {
    if (elm.addEventListener) {
        elm.addEventListener(evType, fn, useCapture);
        return true;
    } else if (elm.attachEvent) {
        var r = elm.attachEvent("on" + evType, fn);
        return r;
    } else {
        alert("Please upgrade your browser to use full functionality on this page");
    }
}

wwlproxy.changeLanguage = function(lang) {
	var new_url = window.location.toString();
	var new_url = new_url.replace(/\/\/([a-zA-Z][a-zA-Z])/, "\/\/"+lang);

	//alert(new_url);

	if (new_url != window.location.toString()) {
		window.location = new_url;
	}
}


/************************************************************************************************/
/* Simple AJAX Code-Kit (SACK) v1.6.1 															*/
/* © 2005 Gregory Wild-Smith 																	*/
/* www.twilightuniverse.com 																	*/
/* Software licenced under a modified X11 licence,												*/
/* see documentation or authors website for more details 										*/

function wwlproxysack(file) {
	this.xmlhttp = null;

	this.resetData = function() {
		this.method = "POST";
  		this.queryStringSeparator = "?";
		this.argumentSeparator = "&";
		this.URLString = "";
		this.encodeURIString = true;
  		this.execute = false;
  		this.element = null;
		this.elementObj = null;
		this.requestFile = file;
		this.vars = new Object();
		this.responseStatus = new Array(2);
  	};

	this.resetFunctions = function() {
  		this.onLoading = function() { };
  		this.onLoaded = function() { };
  		this.onInteractive = function() { };
  		this.onCompletion = function() { };
  		this.onError = function() { };
		this.onFail = function() { };
	};

	this.reset = function() {
		this.resetFunctions();
		this.resetData();
	};

	this.createAJAX = function() {
		try {
			this.xmlhttp = new ActiveXObject("Msxml2.XMLHTTP");
		} catch (e1) {
			try {
				this.xmlhttp = new ActiveXObject("Microsoft.XMLHTTP");
			} catch (e2) {
				this.xmlhttp = null;
			}
		}

		if (! this.xmlhttp) {
			if (typeof XMLHttpRequest != "undefined") {
				this.xmlhttp = new XMLHttpRequest();
			} else {
				this.failed = true;
			}
		}
	};

	this.setVar = function(name, value){
		this.vars[name] = Array(value, false);
	};

	this.encVar = function(name, value, returnvars) {
		if (true == returnvars) {
			return Array(encodeURIComponent(name), encodeURIComponent(value));
		} else {
			this.vars[encodeURIComponent(name)] = Array(encodeURIComponent(value), true);
		}
	}

	this.processURLString = function(string, encode) {
		encoded = encodeURIComponent(this.argumentSeparator);
		regexp = new RegExp(this.argumentSeparator + "|" + encoded);
		varArray = string.split(regexp);
		for (i = 0; i < varArray.length; i++){
			urlVars = varArray[i].split("=");
			if (true == encode){
				this.encVar(urlVars[0], urlVars[1]);
			} else {
				this.setVar(urlVars[0], urlVars[1]);
			}
		}
	}

	this.createURLString = function(urlstring) {
		if (this.encodeURIString && this.URLString.length) {
			this.processURLString(this.URLString, true);
		}

		if (urlstring) {
			if (this.URLString.length) {
				this.URLString += this.argumentSeparator + urlstring;
			} else {
				this.URLString = urlstring;
			}
		}

		// prevents caching of URLString
		this.setVar("rndval", new Date().getTime());

		urlstringtemp = new Array();
		for (key in this.vars) {
			if (false == this.vars[key][1] && true == this.encodeURIString) {
				encoded = this.encVar(key, this.vars[key][0], true);
				delete this.vars[key];
				this.vars[encoded[0]] = Array(encoded[1], true);
				key = encoded[0];
			}

			urlstringtemp[urlstringtemp.length] = key + "=" + this.vars[key][0];
		}
		if (urlstring){
			this.URLString += this.argumentSeparator + urlstringtemp.join(this.argumentSeparator);
		} else {
			this.URLString += urlstringtemp.join(this.argumentSeparator);
		}
	}

	this.runResponse = function() {
		eval(this.response);
	}

	this.runAJAX = function(urlstring) {
		if (this.failed) {
			this.onFail();
		} else {
			this.createURLString(urlstring);
			if (this.element) {
				this.elementObj = document.getElementById(this.element);
			}
			if (this.xmlhttp) {
				var self = this;
				if (this.method == "GET") {
					totalurlstring = this.requestFile + this.queryStringSeparator + this.URLString;
					this.xmlhttp.open(this.method, totalurlstring, true);
				} else {
					this.xmlhttp.open(this.method, this.requestFile, true);
					try {
						this.xmlhttp.setRequestHeader("Content-Type", "application/x-www-form-urlencoded")
					} catch (e) { }
				}

				this.xmlhttp.onreadystatechange = function() {
					switch (self.xmlhttp.readyState) {
						case 1:
							self.onLoading();
							break;
						case 2:
							self.onLoaded();
							break;
						case 3:
							self.onInteractive();
							break;
						case 4:
							self.response = self.xmlhttp.responseText;
							self.responseXML = self.xmlhttp.responseXML;
							self.responseStatus[0] = self.xmlhttp.status;
							self.responseStatus[1] = self.xmlhttp.statusText;

							if (self.execute) {
								self.runResponse();
							}

							if (self.elementObj) {
								elemNodeName = self.elementObj.nodeName;
								elemNodeName.toLowerCase();
								if (elemNodeName == "input"
								|| elemNodeName == "select"
								|| elemNodeName == "option"
								|| elemNodeName == "textarea") {
									self.elementObj.value = self.response;
								} else {
									self.elementObj.innerHTML = self.response;
								}
							}
							if (self.responseStatus[0] == "200") {
								self.onCompletion();
							} else {
								self.onError();
							}

							self.URLString = "";
							break;
					}
				};

				this.xmlhttp.send(this.URLString);
			}
		}
	};

	this.reset();
	this.createAJAX();
}


wwlproxy.addEvent(window, "load", wwlproxy.init);
