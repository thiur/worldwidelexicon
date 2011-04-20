// TransKit for Javascript
// Experimental version 0.1
// Brian S McConnell <bsmcconnell@gmail.com>
var transkit = {

	// SpeakLike service address
	serviceUrl: "worldwidelexicon2.appspot.com",

        realtimeUrl: "speaklikeim.appspot.com",

	// HTTP connection object
	http: null,	

	// List of lang ids that are right-to-left
	rightToLeftLanguages: ["ar" ,"fa", "ur", "iw", "he"], // iw is a synonym for he

	// Called when the initial HTML source has been loaded.
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

        getComments: function(guid, language, callback) {
            var self = this;

            this.callGetService("/comments", [
                                                               ["guid",  guid],
                                                               ["language",  language],
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
                                                            return obj;
                                                            }
                                                    });
        },

        submitComment: function(guid, language, text, callback) {
            var self = this;

            this.callPostService("/comments", [
                                                               ["guid",  guid],
                                                               ["language",  language],
                                                               ["text", text],
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
                                                            return obj;
                                                    });
        },

        getTranslation: function(sl, tl, st, username, pw, callback) {
            var self = this;

            this.callGetService("/t", [
                                                               ["sl",  sl],
                                                               ["tl",  tl],
                                                               ["st", st],
                                                               ["lspusername", username],
                                                               ["lsppw", pw],
                                                               ["multi","n"],
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
                                                            return obj;
                                                    });
        },

        submitTranslation: function(sl,tl,st,tt,url, callback) {
            var self = this;

            this.callPostService("/submit", [
                                                               ["sl",  sl],
                                                               ["tl",  tl],
                                                               ["st", st],
                                                               ["tt", tt],
                                                               ["url", url],
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
                                                            return obj;
                                                    });
        },

        getByUrl: function(url, tl, callback) {
            var self = this;

            this.callGetService("/u", [
                                                               ["url",  url],
                                                               ["tl",  tl],
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
                                                            return obj;
                                                    });
        },

        getScores: function(guid, callback) {
            var self = this;

            this.callGetService("/scores", [
                                                               ["guid",  guid],
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
                                                            return obj;
                                                    });
        },

        submitScore: function(guid, score, callback) {
            var self = this;

            this.callPostService("/scores", [
                                                               ["guid",  guid],
                                                               ["score", score],
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
                                                            return obj;
                                                    });
        },

	// Issues an HTTP GET to the SpeakLike service
	callGetService: function(service, params, callback) {
		var secure = false;
		var query = "", parts = [];

		for(var i = 0; i < params.length; i++) {
			params[i][1] = encodeURIComponent(params[i][1]);
			parts.push(params[i].join("="));
		}

		query = parts.join("&");

		var http = new XMLHttpRequest();
		http.open("GET", (secure ? "https://" : "http://") + this.serviceUrl + service + "?" + query, true);
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

	// Issues an HTTP POST to the SpeakLike service
	callPostService: function(service, params, callback) {
		var secure = false;
		var query = "", parts = [];

		for(var i = 0; i < params.length; i++) {
			params[i][1] = encodeURIComponent(params[i][1]);
			parts.push(params[i].join("="));
		}

		query = speaklike_utf8_encode(parts.join("&"));

		var http = new XMLHttpRequest();
		http.open("POST", (secure ? "https://" : "http://") + this.serviceUrl + service, true);
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

	translate: function(elemId, sl, tl) {
		var self = this;

		var sourceElem = document.getElementById(elemId);
		if (!sourceElem) {
			return;
		}
		var st = sourceElem.innerHTML;
		if (!st || st.length == 0) {
			return;
		}

		this.callGetService("/t", [
								   ["sl",  sl],
								   ["tl",  tl],
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
									self.onTranslation(elemId, obj.tt);
								}
							});
	},
	
	onTranslation: function(elemId, translation) {
		if (!translation || translation.length == 0) {
			return;
		}
		var targetElem = document.getElementById(elemId);
		if (!targetElem) {
			return;
		}
		targetElem.innerHTML = translation;
		this.setElementDir(targetElem);
	},
};

// Utility function to attach to an event
function speaklikeAttachEvent(obj, evt, useCapture, fnc){
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
speaklikeAttachEvent(window, "load", false, function() { transkit.init();  });
speaklikeAttachEvent(window, "unload", false, function() { transkit.uninit() });

// Utility function to utf8 encode text 
function speaklike_utf8_encode(string) {
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

// Utility function to utf8 decode text 
function speaklike_utf8_decode(utftext) {
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


