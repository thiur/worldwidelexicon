var speaklike = {

	host: 'speaklikeim.appspot.com',
	//host: 'localhost:8080',
	username: 'user_en1',
	pw: 'password',
	http: null,
	sessionId: null,
	channelToken: null,
	channel: null,
	socket: null,

	init: function() {
		var self = this;

		// Load Channel library
		var protocol = (document.location.toString().indexOf("https:")==0) ? "https" : "http";
		var src = protocol + "://speaklikeim.appspot.com/_ah/channel/jsapi";
		var s = document.createElement('script');
		s.setAttribute('type', 'text/javascript');
		s.setAttribute('charset', 'iso-8859-1');
		s.setAttribute('src', src);
		document.getElementsByTagName('head').item(0).appendChild(s);

		// Load XMLHttpRequest object
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

		// Run external script which fetches the HTTP headers
		s = document.createElement('script');
		s.setAttribute('type', 'text/javascript');
		s.setAttribute('charset', 'utf-8');
		s.setAttribute('src', 'http://ajaxhttpheaders.appspot.com?callback=speaklike.processHttpHeaders');
		document.getElementsByTagName('head').item(0).appendChild(s);
	},

	processHttpHeaders: function(headers) {
	
		// Get browser language
        var langHeader = headers['Accept-Language'];
        if (!langHeader) {
        	return;
        }
        var langs = langHeader.split(",");
        if (!langs || (langs.size == 0)) {
        	return;
        }
        var browserLang = this.trim(langs[0]);
        if (browserLang.length < 2) {
        	return;
        }
        if (browserLang.length > 2) {
        	browserLang = browserLang.substring(0,2);
        }
        if (speaklikeConfig.onBrowserLangDetected) {
        	speaklikeConfig.onBrowserLangDetected(browserLang);
        }
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
		http.open("GET", (secure ? "https://" : "http://") + this.host + service + "?" + query, true);
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

		query = this.utf8Encode(parts.join("&"));

		var http = new XMLHttpRequest();
		http.open("POST", (secure ? "https://" : "http://") + this.host + service, true);
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
				params[i][1] = encodeURIComponent(params[i][1]);
				parts.push(params[i].join("="));
			}
	
			query = parts.join("&");
		}

        var http = new XMLHttpRequest();
		http.open("GET", url + "?" + query, true);
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

	//
	// SpeakLike RealTime API
	//

	isSessionStarted: function() {
		return this.sessionId != null;
	},

	startSession: function() {
		var self = this;

		this.sessionId = null;
		this.channelToken = null;

		// TODO: handle username/pwd		
		this.callGetService("/realtime/start",
							[["languages",  "en,es"],
							 ["mode",  "socket"],
							 ["username", this.username],
							 ["pw", this.pw]],
							function(response, failed) {
								if (failed) {
									self.onSessionError();
									return;
								}
								var obj = null;
								try {
									obj = eval('(' + response + ')');
								} catch(e) {
									self.onSessionError();
									return; 
								}
								if (!obj) {
									self.onSessionError();
								}
								if (obj.error) {
									if (obj.error != 200) {
										self.onSessionError(obj.reason);
										return;
									}
								}
								self.sessionId = obj.session;
								self.channelToken = obj.token;
								self.onSessionCreated();
							});
	},
	
	translate: function(sl, tl, st, guid) {
		var self = this;

		if (!this.sessionId) {
			this.onSessionError();
		}
			
		this.callGetService("/realtime/translate",
							[["session", this.sessionId],
							 ["sl", sl],
							 ["tl", tl],
							 ["st", st],
							 ["guid", guid]],
							function(response, failed) {
								if (failed) {
									self.onSessionError();
									return;
								}
								var obj = null;
								try {
									obj = eval('(' + response + ')');
								} catch(e) {
									self.onSessionError();
									return; 
								}
								if (!obj) {
									self.onSessionError();
								}
								if (obj.error) {
									if (obj.error != 200) {
										self.onSessionError(obj.reason);
										return;
									}
								}
								self.onTranslationSubmitted(guid);
							});
	},

	onSessionCreated: function() {
	    this.channel = new goog.appengine.Channel(this.channelToken);
	    this.socket = this.channel.open();
	    this.socket.onopen = this.onChannelOpened;
	    this.socket.onmessage = this.onChannelMessage;
	    this.socket.onerror = this.onChannelError;
	    this.socket.onclose = this.onChannelClose;
	},
	
	onChannelOpened: function() {
        if (speaklikeConfig.onSessionStarted) {
        	speaklikeConfig.onSessionStarted();
        }
    },
	
	onTranslationSubmitted: function(guid) {
        if (speaklikeConfig.onTranslationSubmitted) {
        	speaklikeConfig.onTranslationSubmitted(guid);
        }
	},

	onTranslationCompleted: function(msg) {
        if (speaklikeConfig.onTranslationCompleted) {
        	speaklikeConfig.onTranslationCompleted(msg.sl, msg.st, msg.sl, msg.tt, msg.guid);
        }
	},

    onChannelMessage: function(message) {
		// this = window for this callback
		var msg = null;
		try {
			msg = eval('(' + message.data + ')');
		} catch(e) {
			speaklike.onSessionError();
			return; 
		}
		if (!msg) {
			speaklike.onSessionError();
		}
		if (msg.error) {
			speaklike.onSessionError(msg.error_code, msg.reason);
		}
		if (msg.action == 'translation') {
			speaklike.onTranslationCompleted(msg);
		}
    },

	onSessionError: function(reason) {
		// TODO: maybe kill the connection/session and start again?
        if (speaklikeConfig.onSessionError) {
        	speaklikeConfig.onSessionError(reason);
        }
	},
	        
    onChannelError: function() {
		// this = window for this callback
        speaklike.onSessionError();
    },
    
    onChannelClose: function() {
    	// Reconnect the socket
	    this.socket = this.channel.open();
	    this.socket.onopen = this.onChannelOpened;
	    this.socket.onmessage = this.onChannelMessage;
	    this.socket.onerror = this.onChannelError;
	    this.socket.onclose = this.onChannelClose;
    },
			
	//
	// Utility Functions
	//

	utf8Encode: function (string) {
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
	},
 
	utf8Decode: function(utftext) {
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
	},

	createCookie: function(name,value,days) {
		if (days) {
			var date = new Date();
			date.setTime(date.getTime()+(days*24*60*60*1000));
			var expires = "; expires="+date.toGMTString();
		}
		else var expires = "";
		document.cookie = name+"="+value+expires+"; path=/";
	},
	
	readCookie: function(name) {
		var nameEQ = name + "=";
		var ca = document.cookie.split(';');
		for(var i=0;i < ca.length;i++) {
			var c = ca[i];
			while (c.charAt(0)==' ') c = c.substring(1,c.length);
			if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
		}
		return null;
	},

	trim: function(str) {
		return this.ltrim(this.rtrim(str));
	},
	 
	ltrim: function(str, chars) {
		return str.replace(new RegExp("^[\\s]+", "g"), "");
	},
	 
	rtrim: function(str, chars) {
		return str.replace(new RegExp("[\\s]+$", "g"), "");
	},
	
	
	escapable: /[\\\"\x00-\x1f\x7f-\x9f\u00ad\u0600-\u0604\u070f\u17b4\u17b5\u200c-\u200f\u2028-\u202f\u2060-\u206f\ufeff\ufff0-\uffff]/g,
	substitutions: 	{ // table of character substitutions
            '\b': '\\b',
            '\t': '\\t',
            '\n': '\\n',
            '\f': '\\f',
            '\r': '\\r',
            '"' : '\\"',
            '\\': '\\\\'
    		},
	escapeJSON: function (string) {
		var self = this;
        return this.escapable.test(string) ? string.replace(this.escapable, function (a) {
            var c = self.substitutions[a];
            return typeof c === 'string' ? c :
                '\\u' + ('0000' + a.charCodeAt(0).toString(16)).slice(-4);
		        }) : string;
    }
};
	

speaklike.init();

