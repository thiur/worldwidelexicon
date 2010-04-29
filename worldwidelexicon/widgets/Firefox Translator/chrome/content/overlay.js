/* Worldwide Lexicon translation memory developed by Brian S McConnell.
 * Firefox add-on developed by Dmitriy Khudorozhkov.
 *
 * Copyright 2009 by Worldwide Lexicon Inc. All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without modification,
 * are permitted provided that the following conditions are met:
 *
 *   * Redistributions of source code must retain the above copyright notice,
 *     this list of conditions and the following disclaimer.
 *   * Redistributions in binary form must reproduce the above copyright notice,
 *     this list of conditions and the following disclaimer in the documentation
 *     and/or other materials provided with the distribution.
 *   * Neither the name of eZ Systems A.S. nor the names of its contributors may be
 *     used to endorse or promote products derived from this software without
 *     specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
 * THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

var wwlbar = {

	// Shortcuts:

	Ci: Components.interfaces,
	Cc: Components.classes,

	// Preference controls:
	enabled:   true,
	collapsed: false,

	listener: null,
	branch: null,
	tabs: [],

	// Configuration variables:
	servers: ["www.dermundo.com", "worldwidelexicon.appspot.com"],		// array of translation servers

	username: "",
	password: "",
	session: "",
	ip: "",

	tl: "en",
	version: "",

	bilingual:      false,
	colorize:      	true,
	overflow:      	true,
	allowMachine:   true,
	allowAnonymous: true,
	allowUnscored:  true,
	minScore:       0,
	autosidebar:    true,
	translateui:    true,
	resetlogin:     true,

	translated: false,	// just a first-run switch.

	// Color coding:
	colors: {"machine": 	 "#F8F8FF",
			 "humanLow": 	 "#FFFAFA",			// bad quality or suspicious
			 "humanUnknown": "#FFFFF0",			// unknown (unrated)
			 "humanHigh": 	 "#F0FFF0"},

	stoplist: [],

	stream: [],
	streamTime: null,

	strings: [["wwlbar.tip.click", "", ""],
			  ["wwlbar.tip.other", "", ""],

			  ["wwlbar.login.title",    "", ""],
			  ["wwlbar.login.header",   "", ""],
			  ["wwlbar.login.username", "", ""],
			  ["wwlbar.login.pass",     "", ""],
			  ["wwlbar.login.newuser",  "", ""],
			  ["wwlbar.login.cancel",   "", ""],

			  ["wwlbar.newuser.title",  "", ""],
			  ["wwlbar.newuser.header", "", ""],
			  ["wwlbar.newuser.email",  "", ""],
			  ["wwlbar.newuser.button", "", ""],
			  ["wwlbar.newuser.detail", "", ""],
			  ["wwlbar.cancel",         "", ""],

			  ["wwlbar.sidebar.title",  "", ""],

			  ["wwlbar.userdetails.title",       "", ""],
			  ["wwlbar.userdetails.header",      "", ""],
			  ["wwlbar.userdetails.firstname",   "", ""],
			  ["wwlbar.userdetails.lastname",    "", ""],
			  ["wwlbar.userdetails.description", "", ""],
			  ["wwlbar.userdetails.www",         "", ""],
			  ["wwlbar.userdetails.tags",        "", ""],
			  ["wwlbar.userdetails.languages",   "", ""],
			  ["wwlbar.userdetails.accept",      "", ""],

			  ["wwlbar.logout",         "", ""],
			  ["wwlbar.profile",        "", ""],
			  ["wwlbar.login",          "", ""],
			  ["wwlbar.community",      "", ""],

			  ["wwlbar.translate",      "", ""],
			  ["wwlbar.sl.tip",         "", ""],
			  ["wwlbar.tl.tip",         "", ""],
			  ["wwlbar.websearch.link", "", ""],
			  ["wwlbar.websearch.tip",  "", ""],
			  ["wwlbar.options",        "", ""],
			  ["wwlbar.sidebar.link",   "", ""],

			  ["wwlbar.bilingual",      "", ""],
			  ["wwlbar.colorize",       "", ""],
			  ["wwlbar.overflow",       "", ""],
			  ["wwlbar.machine",        "", ""],
			  ["wwlbar.anonymous",      "", ""],
			  ["wwlbar.unscored",       "", ""],
			  ["wwlbar.score",          "", ""],
			  ["wwlbar.score.tip",      "", ""],
			  ["wwlbar.sidebar.check",  "", ""],
			  ["wwlbar.ui.check",       "", ""],
			  ["wwlbar.login.check",    "", ""],

			  ["wwlbar.options.add",       "", ""],
			  ["wwlbar.options.edit",      "", ""],
			  ["wwlbar.options.delete",    "", ""],
			  ["wwlbar.options.servertip", "", ""],

			  ["wwlbar.status.translating", "", ""],
			  ["wwlbar.status.human",       "", ""],
			  ["wwlbar.status.machine",     "", ""],
			  ["wwlbar.status.detecting",   "", ""],

			  ["wwlbar.state.enabled",  "", ""],
			  ["wwlbar.state.sleeping", "", ""],
			  ["wwlbar.state.disabled", "", ""],

			  ["wwlbar.help", "", ""],

			  ["wwlbar.dialog.source",      "", ""],
			  ["wwlbar.dialog.close",       "", ""],
			  ["wwlbar.dialog.translation", "", ""],
			  ["wwlbar.dialog.meta",        "", ""],
			  ["wwlbar.dialog.submit",      "", ""],
			  ["wwlbar.dialog.score",       "", ""],
			  ["wwlbar.dialog.vote",        "", ""],
			  ["wwlbar.dialog.up",          "", ""],
			  ["wwlbar.dialog.down",        "", ""],
			  ["wwlbar.dialog.block",       "", ""],

			  ["wwlbar.meta.header",       "", ""],
			  ["wwlbar.meta.title",        "", ""],
			  ["wwlbar.meta.ttitle",       "", ""],
			  ["wwlbar.meta.description",  "", ""],
			  ["wwlbar.meta.tdescription", "", ""],
			  ["wwlbar.meta.keywords",     "", ""],
			  ["wwlbar.meta.tkeywords",    "", ""],

			  ["wwlbar.host.title",   "", ""],
			  ["wwlbar.host.service", "", ""],
			  ["wwlbar.host.for",     "", ""],
			  ["wwlbar.host.url",     "", ""],
			  ["wwlbar.host.pair",    "", ""]
			 ],

	cache: [],		// translation cache

	// (De)initialization:

	init: function()
	{
		var that = this;

		// Utility class:
		function wwlbar_preference_listener(branch, callback)
		{
			branch.QueryInterface(that.Ci.nsIPrefBranch2);
			branch.addObserver("", this, false);

			branch.getChildList("", { }).forEach(function(name) { callback(branch, name); });

			this.unregister = function()
			{
				if(branch)
					branch.removeObserver("", this);
			};

			this.observe = function(subject, topic, data)
			{
				if(topic == "nsPref:changed")
					callback(branch, data);
			};
		}

		// Get extension's version:
		var em = this.Cc["@mozilla.org/extensions/manager;1"].getService(this.Ci.nsIExtensionManager);
		var addon = em.getItemForID("wwlbar@worldwidelexicon.org");
		this.version = addon.version;

		// Preferences setup:
		var prefservice  = this.Cc["@mozilla.org/preferences-service;1"].getService(this.Ci.nsIPrefService);
		this.branch = prefservice.getBranch("extensions.wwlbar.");

		// Get the browser locale:
		var tmp_branch = prefservice.getBranch("intl.");
		var locales = [];
		var locale = tmp_branch.getCharPref("accept_languages").split(",");

		if(typeof(locale) == "string")
		{
			if((locale_.indexOf("chrome") == -1) && (locale.indexOf("-") != -1))
				locales.push(locale.split("-")[0]);
		}
		else
		{
			for(var i = 0; i < locale.length; i++)
			{
				var locale_ = locale[i];

				if(locale_.indexOf("chrome") == -1)
				{
					if(locale_.indexOf("-") != -1)
						locale_ = locale_.split("-")[0];

					locales.push(locale_);
				}
			}
		}

		if(!locales.length)
			locales.push("en");

		var menu = document.getElementById("wwlbar-target-language-menu").menupopup, ml = menu.childNodes.length;
		for(var i = locales.length - 1; i >= 0; i--)
		{
			var iso = locales[i];

			// find the child node with value == locales[i]:
			for(var j = 0; j < ml; j++)
			{
				var child = menu.childNodes[j];
				if(child.value == iso)
				{
					menu.removeChild(child);
					menu.insertBefore(child, menu.firstChild);
					break;
				}
			}
		}

		this.setTargetLanguage(locales[0]);

		// Load the strings:
		var bundle = document.getElementById("wwlbar-strings").stringBundle;

		for(i = 0; i < this.strings.length; i++)
		{
			var element = this.strings[i];
			element[1] = element[2] = bundle.GetStringFromName(element[0]);
		}

		// Load the cache:

		// Setup unicode converter:
		var suniconvCID = "@mozilla.org/intl/scriptableunicodeconverter";
		var suniconvIID = this.Ci.nsIScriptableUnicodeConverter;

		var uniConv = this.Cc[suniconvCID].createInstance(suniconvIID);
		uniConv.charset = "UTF-8";

		// Parse string into DOM tree:
		var dom = this.loadXML("cache.xml");

		// Load all URLs from cache:
		var urls = dom.documentElement.childNodes;
		for(i = 0; i < urls.length; i++)
		{
			var element = urls[i];
			var unit = this.cache[decodeURIComponent(element.getAttribute("url"))] = [];

			for(var j = 0; j < element.childNodes.length; j++)
			{
				var cacheItem = element.childNodes[j];
				unit.push([uniConv.ConvertToUnicode(decodeURIComponent(cacheItem.getAttribute("original"))), uniConv.ConvertToUnicode(decodeURIComponent(cacheItem.getAttribute("translation"))), new Date(cacheItem.getAttribute("time")), cacheItem.getAttribute("tl")]);
			}
		}

		// Load the server info:
		this.reloadServers();

		// Preference listener setup:
		this.listener = new wwlbar_preference_listener(this.branch, function(branch, name)
		{
			switch(name)
			{
				case "enabled":

					var value = branch.getBoolPref(name);

					that.enabled = value;

					document.getElementById("wwlbar-translate-check").setAttribute("checked", value);

					document.getElementById("wwlbar-source-language-menu").setAttribute("disabled", !value);
					document.getElementById("wwlbar-target-language-label").setAttribute("disabled", !value);
					document.getElementById("wwlbar-target-language-menu").setAttribute("disabled", !value);
					document.getElementById("wwlbar-sidebar-label").setAttribute("disabled", !value);
					document.getElementById("wwlbar-websearch-label").setAttribute("disabled", !value);

					if(value)
						document.getElementById("wwlbar-websearch-field").removeAttribute("disabled");
					else
						document.getElementById("wwlbar-websearch-field").setAttribute("disabled", true);

					document.getElementById("wwlbar-headline").setAttribute("disabled", !value);
					document.getElementById("wwlbar-login-label").setAttribute("disabled", !value);
					document.getElementById("wwlbar-profile-label").setAttribute("disabled", !value);
					document.getElementById("wwlbar-options-button").setAttribute("disabled", !value);

					document.getElementById("wwlbar-status-menu").setAttribute("status", value ? "" : "disabled");
					document.getElementById("wwlbar-status-menu").setAttribute("label", that.getTranslatedUIstringByName("wwlbar.state." + (value ? "enabled" : "disabled")));

					if(value)
					{
						that.startStream();

						if(gBrowser.selectedBrowser.wwlbar_tab && !gBrowser.selectedBrowser.wwlbar_tab.textNodes.length)
							gBrowser.selectedBrowser.wwlbar_tab.parseDocument(gBrowser.selectedBrowser.contentDocument);
					}

					break;

				case "collapsed":
					var value = branch.getBoolPref(name);

					that.collapsed = value;
					document.getElementById("wwlbar-toolbar").collapsed = that.collapsed;
					document.getElementById("wwlbar-status-menu").setAttribute("status", value ? (that.enabled ? "sleeping" : "disabled") : (that.enabled ? "" : "disabled"));
					document.getElementById("wwlbar-status-menu").setAttribute("label", that.getTranslatedUIstringByName("wwlbar.state." + (value ? (that.enabled ? "sleeping" : "disabled") : (that.enabled ? "enabled" : "disabled"))));
					break;

				case "bilingual":

					that.bilingual = branch.getBoolPref(name);
					document.getElementById("wwlbar-bilingual-check").setAttribute("checked", that.bilingual);
					break;

				case "colorize":

					that.colorize = branch.getBoolPref(name);
					document.getElementById("wwlbar-colorize-check").setAttribute("checked", that.colorize);
					break;

				case "overflow":

					that.overflow = branch.getBoolPref(name);
					document.getElementById("wwlbar-overflow-check").setAttribute("checked", that.overflow);
					break;

				case "machine":

					that.allowMachine = branch.getBoolPref(name);
					document.getElementById("wwlbar-machine-check").setAttribute("checked", that.allowMachine);
					break;

				case "anonymous":

					that.allowAnonymous = branch.getBoolPref(name);
					document.getElementById("wwlbar-anonymous-check").setAttribute("checked", that.allowAnonymous);
					break;

				case "unscored":

					that.allowUnscored = branch.getBoolPref(name);
					document.getElementById("wwlbar-unscored-check").setAttribute("checked", that.allowUnscored);
					break;

				case "score":

					that.minScore = branch.getIntPref(name);
					document.getElementById("wwlbar-score-menu").selectedIndex = that.minScore;
					break;

				case "autosidebar":
					that.autosidebar = branch.getBoolPref(name);
					document.getElementById("wwlbar-sidebar-check").setAttribute("checked", that.autosidebar);
					break;

				case "translateui":
					that.translateui = branch.getBoolPref(name);
					document.getElementById("wwlbar-ui-check").setAttribute("checked", that.translateui);

					if(that.translateui && !that.translated)
					{
						that.translated = true;

						that.translateUIchunk(0);
					}
					break;

				case "resetlogin":
					that.resetlogin = branch.getBoolPref(name);
					document.getElementById("wwlbar-login-check").setAttribute("checked", that.resetlogin);
					break;
			}
		});

		var timer = setInterval(function()
		{
			if((gBrowser.docShell.busyFlags == 0) && !gBrowser.docShell.isExecutingOnLoadHandler && !gBrowser.docShell.isLoadingDocument && !gBrowser.mIsBusy)
			{
				clearInterval(timer);
			}
			else return;

			// Setup tab handler for the 1st existing tab:
			that.tabs[0] = new wwlbar_tab(gBrowser.selectedBrowser);
			that.setSourceLanguage(that.tabs[0].sl);

			// Setup tab event handlers:
			var container = gBrowser.tabContainer;
			container.addEventListener("TabOpen",   that.onTabAdded,    false);
			container.addEventListener("TabSelect", that.onTabSelected, false);
			container.addEventListener("TabClose",  that.onTabClosed,   false);
    
			that.observer = that.Cc["@mozilla.org/observer-service;1"].getService(that.Ci.nsIObserverService);
			that.observer.addObserver(that, "private-browsing", false);

			// Get current IP:
			setTimeout(function()
			{
				that.updateIP();
			},
			1000);
		},
		1000);
	},

	uninit: function()
	{
		this.observer.removeObserver(this, "private-browsing");  

		this.listener.unregister();

		var container = gBrowser.tabContainer;
		container.removeEventListener("TabOpen",   this.onTabAdded,    false);
		container.removeEventListener("TabSelect", this.onTabSelected, false);
		container.removeEventListener("TabClose",  this.onTabClosed,   false);

		for(var i = 0; i < this.tabs.length; i++)
			this.tabs[i].uninit();

		wwlbar.callService("/users/logout", 0, [], function(response, failed)
		{
			if(response && response.length)
			{
				that.session = "";
			}
		});
	},

	// Private browsing observer:
	observe: function(aSubject, aTopic, aData)
	{
		if(aTopic == "private-browsing")
			if(aData == "enter")
				wwlbar.branch.setBoolPref("enabled", false);
	},

	// Tabs handling:

	onTabAdded: function(event)
	{
		wwlbar.tabs.push(new wwlbar_tab(event.target.linkedBrowser));
		wwlbar.setSourceLanguage(brw.wwlbar_tab.sl);

		if(wwlbar.autosidebar)
			wwlbar.toggleSidebar(false);
	},

	onTabSelected: function(event)
	{
		var brw = gBrowser.selectedBrowser;

		wwlbar.setSourceLanguage(brw.wwlbar_tab.sl);

		var enable = !wwlbar.enabled || wwlbar.shouldTranslate(brw.contentDocument);

		if(wwlbar.autosidebar)
			wwlbar.toggleSidebar(!((brw.wwlbar_tab.sl == wwlbar.tl) || !enable));
	},

	onTabClosed: function(event)
	{
		var browser = event.target.linkedBrowser;
		for(var i = 0; i < wwlbar.tabs.length; i++)
		{
			if(wwlbar.tabs[i].browser == browser)
			{
				wwlbar.tabs[i].uninit();
				wwlbar.tabs.splice(i, 1);

				break;
			}
		}
	},

	// UI and options:
	switchToolbar: function(node)
	{
		var value = (node.getAttribute("checked") == "true");

		this.branch.setBoolPref("enabled", value);
	},

	setSourceLanguage: function(node)
	{
		var current_wwl = gBrowser.selectedBrowser.wwlbar_tab;

		if(typeof(node) == "string")
		{
			current_wwl.sl = node;

			var menu = document.getElementById("wwlbar-source-language-menu");
			var languages = menu.menupopup.children;

			for(var i = 0; i < languages.length; i++)
				if(languages[i].value == node)
					break;

			if(i != languages.length)
				menu.selectedIndex = i;
		}
		else
		{
			current_wwl.sl = node.value;

			// Retranslate the page:
			current_wwl.reparseDocument(current_wwl.browser.contentDocument, false);
		}
	},

	setTargetLanguage: function(node)
	{
		if(typeof(node) == "string")
		{
			this.tl = node;

			var menu = document.getElementById("wwlbar-target-language-menu");
			var languages = menu.menupopup.children;

			for(var i = 0; i < languages.length; i++)
				if(languages[i].value == node)
					break;

			if(i != languages.length)
				menu.selectedIndex = i;
		}
		else
		{
			this.tl = node.value;

			// Retranslate the page:
			gBrowser.selectedBrowser.wwlbar_tab.reparseDocument(gBrowser.selectedBrowser.contentDocument, false);
		}

		if(this.translated)
			this.translateUIchunk(0);
	},

	switchBilingual: function(node)
	{
		var value = (node.getAttribute("checked") == "true");

		this.branch.setBoolPref("bilingual", value);
	},

	switchColorize: function(node)
	{
		var value = (node.getAttribute("checked") == "true");

		this.branch.setBoolPref("colorize", value);
	},

	switchOverflow: function(node)
	{
		var value = (node.getAttribute("checked") == "true");

		this.branch.setBoolPref("overflow", value);
	},

	switchMachine: function(node)
	{
		var value = (node.getAttribute("checked") == "true");

		this.branch.setBoolPref("machine", value);
	},

	switchAnonymous: function(node)
	{
		var value = (node.getAttribute("checked") == "true");

		this.branch.setBoolPref("anonymous", value);
	},

	switchUnscored: function(node)
	{
		var value = (node.getAttribute("checked") == "true");

		this.branch.setBoolPref("unscored", value);
	},

	setMinimumScore: function(score)
	{
		this.branch.setIntPref("score", score);
	},

	switchAutoSidebar: function(node)
	{
		var value = (node.getAttribute("checked") == "true");

		this.branch.setBoolPref("autosidebar", value);
	},

	switchTranslateUI: function(node)
	{
		var value = (node.getAttribute("checked") == "true");

		this.branch.setBoolPref("translateui", value);
	},

	switchResetLogin: function(node)
	{
		var value = (node.getAttribute("checked") == "true");

		this.branch.setBoolPref("resetlogin", value);
	},

	toggleSidebar: function(showhide, user)
	{
		if(!wwlbar.enabled && !user)
			return;

		var brw = gBrowser.selectedBrowser;
		var sidebar = document.getElementById("sidebar");
		var sidebarShown = !document.getElementById("sidebar-box").hidden;

		// set up the onload handlers:
		if(!sidebarShown)
		{
			var wwlshowsidebar = function()
			{
				if(!document.getElementById("sidebar-box").hidden)
				{
					wwlbar.updateSidebar(wwlbar.servers[wwlbar.getServer(brw.contentDocument.location.href, brw.wwlbar_tab.sl, wwlbar.tl)], brw.wwlbar_tab.sl, brw.contentDocument.location.href);
				}

				sidebar.removeEventListener("SidebarFocused", wwlshowsidebar, false);
			};

			sidebar.addEventListener("SidebarFocused", wwlshowsidebar, false);
		}
		else wwlbar.updateSidebar(wwlbar.servers[wwlbar.getServer(brw.contentDocument.location.href, brw.wwlbar_tab.sl, wwlbar.tl)], brw.wwlbar_tab.sl, brw.contentDocument.location.href);

		// actual switching:
		if((typeof(showhide) == "undefined"))
			toggleSidebar("viewWWLSidebar");
		else
		{
			var sidebarOurs = (sidebar.contentWindow.location.href == "chrome://wwlbar/content/sidebar.xul")

			if((sidebarShown && sidebarOurs && !showhide) || (!sidebarShown && showhide))
				toggleSidebar("viewWWLSidebar");
			else
				if(sidebarShown && !sidebarOurs && showhide)
					toggleSidebar("viewWWLSidebar", true);
		}
	},

	openWebSearch: function(keyword)
	{
		if(!this.enabled)
			return;

		var url = "http://" + this.servers[0] + "/search?sl=" + gBrowser.selectedBrowser.wwlbar_tab.sl + "&tl=" + this.tl + "&q=" + encodeURIComponent(keyword);

		if(gBrowser.selectedBrowser.webNavigation.document.location.href.indexOf("about:") == 0)
			gBrowser.selectedBrowser.webNavigation.document.location.href = url;
		else
			gBrowser.selectedTab = gBrowser.addTab(url);
	},

	login: function()
	{
		var loginManager = this.Cc["@mozilla.org/login-manager;1"].getService(this.Ci.nsILoginManager);
		var nsLoginInfo = new Components.Constructor("@mozilla.org/login-manager/loginInfo;1", this.Ci.nsILoginInfo, "init");
		var that = this;

		if(!this.session.length)
		{
			var logins = loginManager.findLogins({}, "chrome://wwlbar/", "wwlbar-autologin", null);

			if(logins[0])
			{
				this.username = logins[0].username;
				this.password = logins[0].password;

				// Note: username and password will be appended automatically in "callService":
				wwlbar.callService("/users/auth", 0, [], function(response, failed)
				{
					if(response && response.length)
					{
						that.session = response;

						document.getElementById("wwlbar-login-label").value = that.getTranslatedUIstringByName("wwlbar.logout");
						document.getElementById("wwlbar-profile-label").value = that.getTranslatedUIstringByName("wwlbar.profile");
					}
					else
					{
						loginManager.removeLogin(logins[0]);
						that.password = "";
						alert("Either your user name or password are incorrect; please provide correct credentials.");

						setTimeout(function() { that.login(); }, 0);
						return;
					}
				});
			}
			else
			{
				var retObj = {action: "", username: this.username, password: "", strings: ((this.tl != "en") ? this.strings : null)};
				window.openDialog('chrome://wwlbar/content/login.xul', 'WWLlogin', 'centerscreen=yes,chrome=yes,modal=yes', retObj);

				if(retObj.action == "login")
				{
					this.username = retObj.username;
					this.password = retObj.password;

					var loginInfo = new nsLoginInfo("chrome://wwlbar/", "wwlbar-autologin", null, this.username, this.password, "username", "password");
					var logins = loginManager.findLogins({}, "chrome://wwlbar/", "wwlbar-autologin", null);

					// Note: username and password will be appended automatically in "callService":
					wwlbar.callService("/users/auth", 0, [], function(response, failed)
					{
						if(response && response.length)
						{
							if(logins[0])
							{
								loginManager.modifyLogin(logins[0], loginInfo);
							}
							else
							{
								loginManager.addLogin(loginInfo);
							}

							that.session = response;

							document.getElementById("wwlbar-login-label").value = that.getTranslatedUIstringByName("wwlbar.logout");
							document.getElementById("wwlbar-profile-label").value = that.getTranslatedUIstringByName("wwlbar.profile");
						}
						else
						{
							that.password = "";
							alert("Either your user name or password are incorrect; please provide correct credentials.");

							setTimeout(function() { that.login(); }, 0);
							return;
						}
					});
				}
				else if(retObj.action == "newuser")
				{
					// call the dialog for the new user creation:
					retObj = {action: "", username: "", password: "", email: "", detail: false, strings: ((this.tl != "en") ? this.strings : null)};
					window.openDialog('chrome://wwlbar/content/newuser.xul', 'WWLnewuser', 'centerscreen=yes,chrome=yes,modal=yes', retObj);

					if(retObj.action == "newuser")
					{
						this.username = retObj.username;
						this.password = retObj.password;

						wwlbar.callService("/users/new", 0, [["email", retObj.email]], function(response, failed)
						{
							if(response.length)
							{
								wwlbar.callGetService("/users/validate", 0, [["k", response]], function(response, failed)
								{
									if(response && response.length)
									{
										var loginInfo = new nsLoginInfo("chrome://wwlbar/", "wwlbar-autologin", null, that.username, that.password, "username", "password");
										var logins = loginManager.findLogins({}, "chrome://wwlbar/", "wwlbar-autologin", null);
										if(logins[0])
										{
											loginManager.modifyLogin(logins[0], loginInfo);
										}
										else
										{
											loginManager.addLogin(loginInfo);
										}

										that.session = response;

										document.getElementById("wwlbar-login-label").value = that.getTranslatedUIstringByName("wwlbar.logout");
										document.getElementById("wwlbar-profile-label").value = that.getTranslatedUIstringByName("wwlbar.profile");

										if(retObj.detail)
										{
											retObj = {action: "", firstname: "", lastname: "", description: "", skype: "", facebook: "", www: "", tags: "", languages: "", strings: ((that.tl != "en") ? that.strings : null)};
											window.openDialog('chrome://wwlbar/content/userdetails.xul', 'WWLuserdetails', 'centerscreen=yes,chrome=yes,modal=yes', retObj);

											if(retObj.action == "userdetails")
											{
												var params = [["username", wwlbar.username], ["sid", wwlbar.md5(wwlbar.password)], ["redirect", "n"]];

												if(retObj.firstname.length)
													params.push(["firstname", retObj.firstname]);

												if(retObj.lastname.length)
													params.push(["lastname", retObj.lastname]);

												if(retObj.description.length)
													params.push(["description", retObj.description]);

												if(retObj.skype.length)
													params.push(["skype", retObj.skype]);

												if(retObj.facebook.length)
													params.push(["facebook", retObj.facebook]);

												if(retObj.www.length)
													params.push(["www", retObj.www]);

												if(retObj.tags.length)
													params.push(["tags", retObj.tags]);

												if(retObj.languages.length)
													params.push(["languages", retObj.languages]);

												wwlbar.callService("/profiles/" + that.username, 0, params, function(response, failed)
												{
													wwlbar.openProfile();
												});
											}
										}
									}
								});
							}
						});
					}
				}
			}
		}
		else
		{
			wwlbar.callService("/users/logout", 0, [], function(response, failed)
			{
				if(response && response.length)
				{
					that.username = "";
					that.password = "";
					that.session = "";

					document.getElementById("wwlbar-login-label").value = that.getTranslatedUIstringByName("wwlbar.login");
					document.getElementById("wwlbar-profile-label").value = that.getTranslatedUIstringByName("wwlbar.community");

					if(that.resetlogin)
					{
						var logins = loginManager.findLogins({}, "chrome://wwlbar/", "wwlbar-autologin", null);
						if(logins[0])
						{
							loginManager.removeLogin(logins[0]);
						}
					}
				}
			});
		}
	},

	help: function()
	{
		var url = "http://" + this.servers[0] + "/help/firefox";

		if(gBrowser.selectedBrowser.webNavigation.document.location.href.indexOf("about:") == 0)
			gBrowser.selectedBrowser.webNavigation.document.location.href = url;
		else
			gBrowser.selectedTab = gBrowser.addTab(url);
	},

	openProfile: function()
	{
		if(!this.enabled)
			return;

		var url = "http://" + this.servers[0] + "/profiles" + (this.username.length ? ("/" + this.username) : "") + "?tl=" + this.tl + (this.password.length ? ("&sid=" + this.md5(this.password)) : "");

		if(gBrowser.selectedBrowser.webNavigation.document.location.href.indexOf("about:") == 0)
			gBrowser.selectedBrowser.webNavigation.document.location.href = url;
		else
			gBrowser.selectedTab = gBrowser.addTab(url);
	},

	openOptions: function()
	{
		window.openDialog('chrome://wwlbar/content/options.xul', 'WWLoptions', 'centerscreen=yes,chrome=yes,modal=yes', {strings: this.strings});
	},

	// Sidebar operation:

	updateSidebar: function(server, sl, url)
	{
		var sidebarWindow = document.getElementById("sidebar").contentWindow;

		// Verify that our sidebar is open at this moment:
		if(sidebarWindow.location.href == "chrome://wwlbar/content/sidebar.xul")
			if(sidebarWindow.wwlbar && sidebarWindow.wwlbar.sidebar)
				sidebarWindow.wwlbar.sidebar.update(server, sl, this.tl, this.domain(url), "firefox." + this.version);
	},

	updateStatusbar: function(tab, action, index, chunk, isHuman, provider)
	{
		if(tab.browser == gBrowser.selectedBrowser)
		{
			var statusTextFld = document.getElementById("statusbar-display");
			if(action != -1)
			{
				switch(action)
				{
					case "translating":
						statusTextFld.label = this.getTranslatedUIstringByName("wwlbar.status.translating") + " " + index + " of " + (tab.textNodes.length - 1) + ((chunk == 0) ? "" : (" (" + chunk + ")")) + ", " + (isHuman ? this.getTranslatedUIstringByName("wwlbar.status.human") : (this.getTranslatedUIstringByName("wwlbar.status.machine") + " - " + provider)) + ".";
						break;

					case "detecting":
						statusTextFld.label = this.getTranslatedUIstringByName("wwlbar.status.detecting") + " " + index + " (" + provider + ").";
						break;
				}
			}
			else statusTextFld.label = "";
		}
	},

	updateIP: function()
	{
		var that = this;
		this.callExternal("http://www.tsql.de/ipxml.php", null, function(responseXML)
		{
			var elms = responseXML.getElementsByTagName("showmyip");
			if(elms.length)
			{
				var ip = elms[0].getAttribute("ip");

				if(ip && ip.length)
					that.ip = ip;
			}
		},
		"text/xml");
	},

	// Inner workings:

	callGetService: function(service, serverIndex, params, callback)
	{
		var query = "", parts = [];

		for(var i = 0; i < params.length; i++)
		{
			params[i][1] = encodeURIComponent(params[i][1]);

			parts.push(params[i].join("="));
		}

		query = parts.join("&");

		var http = new XMLHttpRequest();
		http.open("GET", "http://" + this.servers[serverIndex] + service + "?" + query, true);
		http.channel.loadFlags |= this.Ci.nsIRequest.LOAD_BYPASS_CACHE;

		http.onreadystatechange = function()
		{
			if(http.readyState == 4)
			{
				if(http.status == 200)
				{
					callback(http.responseText);
				}
				else
				{
					callback(http.responseText, true);
				}
			}
		};

		http.send();
	},

	callService: function(service, serverIndex, params, callback)
	{
		var secure = false;

		// If username and password are defined - use them:
		if(wwlbar.username.length &&
			((service == "/submit")    || (service == "/scores/vote")  || (service == "/users/auth") ||
			 (service == "/users/new") || (service == "/users/logout") || (service == "/users/validate") ||
			 (service == ("/profiles/" + this.username))))
		{
			secure = true;
			serverIndex = 1;

			params.push(["username", wwlbar.username]);
			params.push(["pw", wwlbar.password]);

			if(wwlbar.session.length)
				params.push(["session", wwlbar.session]);
		}

		if((service != "/submit") && (service != "/users/new"))
		{
			var query = "", parts = [];

			for(var i = 0; i < params.length; i++)
			{
				//params[i][1] = String(params[i][1]).replace(/ /g, "+");
				params[i][1] = encodeURIComponent(params[i][1]);

				parts.push(params[i].join("="));
			}

			query = parts.join("&");

			var http = new XMLHttpRequest();
			http.open("POST", (secure ? "https://" : "http://") + this.servers[serverIndex] + service, true);
			http.channel.loadFlags |= this.Ci.nsIRequest.LOAD_BYPASS_CACHE;

			http.setRequestHeader("Content-Type", "application/x-www-form-urlencoded; charset=utf-8");
			http.setRequestHeader("Content-Length", query.length);
			http.setRequestHeader("Accept-Charset", "UTF-8");

			http.onreadystatechange = function()
			{
				if(http.readyState == 4)
				{
					if(http.status == 200)
					{
						callback(http.responseText);
					}
					else
					{
						callback(http.responseText, true);
					}
				}
			};

			http.send(query);
		}
		else
		{
			// Create a shadow browser:
			var windowMediator = wwlbar.Cc['@mozilla.org/appshell/window-mediator;1'].getService(wwlbar.Ci.nsIWindowMediator);
			var _window = windowMediator.getMostRecentWindow("navigator:browser"); 

			var docroot = _window.document;
			var shadow = docroot.createElement('browser');
			shadow.setAttribute("collapsed", true);
			shadow.setAttribute("type", "content");

			// Insert the browser into the window, creating the doc shell.
			docroot.documentElement.appendChild(shadow);

			shadow.webNavigation.stop(wwlbar.Ci.nsIWebNavigation.STOP_NETWORK);

			// Allow JavaScript, but turn off auth dialogs for security and other things to reduce network load.
			shadow.docShell.allowJavascript    = false;
			shadow.docShell.allowAuth          = false;
			shadow.docShell.allowPlugins       = false;
			shadow.docShell.allowMetaRedirects = false;
			shadow.docShell.allowSubframes     = false;
			shadow.docShell.allowImages        = false;

			var submittted = false;
			shadow.addEventListener("DOMContentLoaded", function()
			{
				if(!submittted)
				{
					var form = shadow.contentDocument.getElementsByTagName("form")[0];

					for(var i = 0; i < params.length; i++)
					{
						var name = params[i][0];
						var value = params[i][1];

						for(var j = 0; j < form.elements.length; j++)
						{
							if(form.elements[j].name == name)
							{
								form.elements[j].value = value;
								break;
							}
						}
					}

					submittted = true;
					form.submit();
				}
				else
				{
					callback(shadow.contentDocument.body.textContent);
					docroot.documentElement.removeChild(shadow);
				}
			},
			false);

			shadow.webNavigation.loadURI((secure ? "https://" : "http://") + wwlbar.servers[serverIndex] + service, wwlbar.Ci.nsIWebNavigation.LOAD_FLAGS_BYPASS_CACHE, null, null, null);
		}
	},

	callExternal: function(url, params, callback, type)
	{
		var query = "", parts = [];

		if(params)
		{
			for(var i = 0; i < params.length; i++)
			{
				for(var j = 0; j < params[i].length; j++)
				{
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

		if(type)
			http.overrideMimeType(type);

		http.setRequestHeader("Content-Type", type || "application/x-www-form-urlencoded; charset=utf-8");
		http.setRequestHeader("Accept-Charset", "UTF-8");

		http.onreadystatechange = function()
		{
			if(http.readyState == 4)
			{
				if(http.status == 200)
				{
					callback((type && (type == "text/xml")) ? http.responseXML : http.responseText);
				}
				else
				{
					callback(http.responseText, false);
				}
			}
		};

		http.send();
	},

	md5: function(source)
	{
		// the following code is taken from: https://developer.mozilla.org/en/nsICryptoHash#Computing_the_Hash_of_a_String

		var converter = this.Cc["@mozilla.org/intl/scriptableunicodeconverter"].createInstance(this.Ci.nsIScriptableUnicodeConverter);
		converter.charset = "UTF-8";

		var ch = this.Cc["@mozilla.org/security/hash;1"].createInstance(this.Ci.nsICryptoHash);
		ch.init(ch.MD5);

		var result = {};
		var data = converter.convertToByteArray(source, result);

		ch.update(data, data.length);
		var hash = ch.finish(false);

		function toHexString(charCode)
		{
			return ("0" + charCode.toString(16)).slice(-2);
		}

		return [toHexString(hash.charCodeAt(i)) for (i in hash)].join("");
	},

	domain: function(url)
	{
		if(url.indexOf("http://") == 0)
			url = url.substr(7);
		else if(url.indexOf("https://") == 0)
			url = url.substr(8);

		var anchor = url.lastIndexOf("#");
		if(anchor != -1)
			url = url.substr(0, anchor);

		if(url.charAt(url.length - 1) == "/")
			url = url.substr(0, url.length - 1);

		return url;
	},

	shouldTranslate: function(doc)
	{
		if(!doc || !doc.location)
			return false;

		if(doc.location.protocol.indexOf("https") == 0)
			return false;

		// check if the URL of document is in the stop list:
		var url = doc.location.href;

		for(var i = 0; i < this.stoplist.length; i++)
			if(url.indexOf(this.stoplist[i]) != -1)
				return false;

		if(doc.documentElement && (doc.documentElement.textContent.indexOf("wwlapi=\"tr\"") != -1))
			return false;

		return true;
	},

	startStream: function(index)
	{
		if(!this.enabled || this.collapsed)
			return;

		if(typeof(index) == "undefined")
		{
			this.stream = [];
			this.streamTime = new Date().getTime();

			this.callGetService("/stream", 0, [["tl", this.tl], ["output", "json"], ["v", this.version]], function(response, failed)
			{
				if(!response || !response.length || failed)
					return;

				var ret = null;

				try
				{
					var nativeJSON = Components.classes["@mozilla.org/dom/json;1"].createInstance(Components.interfaces.nsIJSON);

					ret = nativeJSON.decode(response);
				}
				catch(e) { };

				if(ret && ret.records && ret.records.length)
				{
					for(var i = 0; i < ret.records.length; i++)
					{
						var item = ret.records[i].item;

						if(item && item.title && item.url && item.title.length && item.url.length)
							wwlbar.stream.push([(item.title.length < 40) ? item.title : (item.title.substr(0, 40) + "..."), (item.url.indexOf("http") == 0) ? item.url : ("http://" + item.url), "(recently translated)" + ((item.description && item.description.length) ? (" " + item.description) : "")]);
					}

					wwlbar.startStream(0);
				}
			});
		}
		else
		{
			if(index < wwlbar.stream.length)
			{
				this.fade("wwlbar-headline", 0, 100, 10, function()
				{
					document.getElementById("wwlbar-headline").value = wwlbar.stream[index][0];
					document.getElementById("wwlbar-headline").href = wwlbar.stream[index][1];
					document.getElementById("wwlbar-headline").tooltipText = wwlbar.stream[index][2];

					wwlbar.fade("wwlbar-headline", 100, 100, 10, function()
					{
						setTimeout(function()
						{
							wwlbar.startStream(index + 1);
						},
						6000);
					});
				});
			}
			else
			{
				if((new Date().getTime() - this.streamTime) < (1000 * 60 * 5))
					wwlbar.startStream(0);
				else
					wwlbar.startStream();
			}
		}
	},

	fade: function(id, destOp, rate, delta, callback)
	{
		var obj = document.getElementById(id);

		if(obj.timer) clearTimeout(obj.timer);

		var curOp = obj.style.opacity * 100.0;
		var direction = (curOp <= destOp) ? 1 : -1;

		delta  = Math.min(direction * (destOp - curOp), delta);
		curOp += direction * delta;

		obj.style.opacity = curOp / 100.0;

		if(curOp != destOp)
			obj.timer = setTimeout(function() { wwlbar.fade(id, destOp, rate, delta, callback); }, rate);
		else
		{
			if(callback)
				callback();
		}
	},

	translateUIchunk: function(index)
	{
		if(index == this.strings.length)
		{
			this.updateCache();

			this.translateLanguageMenu(document.getElementById("wwlbar-source-language-menu"), function()
			{
				wwlbar.translateLanguageMenu(document.getElementById("wwlbar-target-language-menu"));
			});

			return;
		}

		if(index > 25)
		{
			setTimeout(function()
			{
				document.getElementById("wwltip").openPopup(document.getElementById("wwlbar-login-label"), "after_end", 0, -15, false, false);

				setTimeout(function()
				{
					document.getElementById("wwltip").hidePopup();
				},
				10000);
			},
			1000);
		}

		var element = this.strings[index];

		if(this.tl != "en")
		{
			var cached = this.getFromCache("chrome://wwlbar", element[1], this.tl);

			if(cached.length)
			{
				element[2] = cached;
				this.updateUIchunk(element[0], element[2]);

				this.translateUIchunk(index + 1);
			}
			else
			{
				var params = [["v", "1.0"], ["q", element[1]], ["userip", this.ip]];

				var nextIndex = index + 1;
				var labels = [element[2]];
				var ids = [element[0]];

				// Look ahead:
				for(var i = nextIndex; i < length; i++)
				{
					var nextLabel = this.strings[i][1];

					if(!this.getFromCache("chrome://wwlbar", nextLabel, this.tl).length && ((labels.join(",").length + nextLabel.length) < 100))
					{
						labels.push(nextLabel);
						ids.push(this.strings[i][0]);
						params.push(["q", nextLabel]);

						++nextIndex;
					}
					else break;
				}

				params.push(["langpair", "en|" + this.tl]);

				this.callExternal("http://ajax.googleapis.com/ajax/services/language/translate?", params, function(response, failed)
				{
					var ret = null;

					try
					{
						var nativeJSON = Components.classes["@mozilla.org/dom/json;1"].createInstance(Components.interfaces.nsIJSON);

						ret = nativeJSON.decode(response);
					}
					catch(e) { }

					if(ret && ret.responseData)
					{
						if(ret.responseData.translatedText) // single item
						{
							element[2] = ret.responseData.translatedText;
							wwlbar.updateUIchunk(element[0], element[2]);

							wwlbar.storeInCache("chrome://wwlbar", element[1], element[2], wwlbar.tl);
						}
						else
						{
							for(i = 0; i < ret.responseData.length; i++)
							{
								var ret2 = ret.responseData[i];
								if(ret2 && ret2.responseData)
								{
									var translation = ret2.responseData.translatedText;
									wwlbar.strings[index + i][2] = translation;
									wwlbar.updateUIchunk(ids[i], translation);

									wwlbar.storeInCache("chrome://wwlbar", labels[i], translation, wwlbar.tl);
								}
							}
						}
					}

					wwlbar.translateUIchunk(nextIndex);
				});
			}
		}
		else
		{
			wwlbar.updateUIchunk(element[0], element[2]);
			wwlbar.translateUIchunk(index + 1);
		}
	},

	updateUIchunk: function(name, value)
	{
		switch(name)
		{
			case "wwlbar.tip.click":
				document.getElementById("wwltip-1").setAttribute("value", value);
				break;

			case "wwlbar.tip.other":
				document.getElementById("wwltip-3").setAttribute("value", value);
				break;

			case "wwlbar.translate":
				document.getElementById("wwlbar-translate-check").setAttribute("label", value);
				break;

			case "wwlbar.login":
				document.getElementById("wwltip-2").setAttribute("value", value);
				if(!this.session.length)
					document.getElementById("wwlbar-login-label").setAttribute("value", value);

				break;

			case "wwlbar.logout":
				if(this.session.length)
					document.getElementById("wwlbar-login-label").setAttribute("value", value);

				break;

			case "wwlbar.community":
				if(!this.session.length)
					document.getElementById("wwlbar-profile-label").setAttribute("value", value);

				break;

			case "wwlbar.profile":
				if(this.session.length)
					document.getElementById("wwlbar-profile-label").setAttribute("value", value);

				break;

			case "wwlbar.bilingual":
				document.getElementById("wwlbar-bilingual-check").setAttribute("label", value);
				break;

			case "wwlbar.colorize":
				document.getElementById("wwlbar-colorize-check").setAttribute("label", value);
				break;

			case "wwlbar.overflow":
				document.getElementById("wwlbar-overflow-check").setAttribute("label", value);
				break;

			case "wwlbar.sl.tip":
				document.getElementById("wwlbar-source-language-menu").setAttribute("tooltiptext", value);
				break;

			case "wwlbar.tl.tip":
				document.getElementById("wwlbar-target-language-menu").setAttribute("tooltiptext", value);
				break;

			case "wwlbar.multi":
				document.getElementById("wwlbar-source-language-menu").getItemAtIndex(0).setAttribute("label", value);
				break;

			case "wwlbar.options":
				document.getElementById("wwlbar-options-button").setAttribute("label", value);
				break;

			case "wwlbar.websearch.link":
				document.getElementById("wwlbar-websearch-label").setAttribute("value", value);
				break;

			case "wwlbar.websearch.tip":
				document.getElementById("wwlbar-websearch-field").setAttribute("tooltiptext", value);
				break;

			case "wwlbar.help":
				document.getElementById("wwlbar-help-label").setAttribute("value", value);
				break;

			case "wwlbar.machine":
				document.getElementById("wwlbar-machine-check").setAttribute("label", value);
				break;

			case "wwlbar.anonymous":
				document.getElementById("wwlbar-anonymous-check").setAttribute("label", value);
				break;

			case "wwlbar.unscored":
				document.getElementById("wwlbar-unscored-check").setAttribute("label", value);
				break;

			case "wwlbar.score":
				document.getElementById("wwlbar-score-label").setAttribute("value", value + ":");
				break;

			case "wwlbar.score.tip":
				document.getElementById("wwlbar-score-label").setAttribute("tooltiptext", value);
				break;

			case "wwlbar.sidebar.link":
				document.getElementById("wwlbar-sidebar-label").setAttribute("label", value);
				break;

			case "wwlbar.sidebar.check":
				document.getElementById("wwlbar-sidebar-check").setAttribute("label", value);
				break;

			case "wwlbar.ui.check":
				document.getElementById("wwlbar-ui-check").setAttribute("label", value);
				break;

			case "wwlbar.login.check":
				document.getElementById("wwlbar-login-check").setAttribute("label", value);
				break;

			case "wwlbar.state.enabled":
				var status = document.getElementById("wwlbar-status-menu");
				if(status.getAttribute("status") == "") status.setAttribute("label", value);
				break;

			case "wwlbar.state.sleeping":
				var status = document.getElementById("wwlbar-status-menu");
				if(status.getAttribute("status") == "sleeping") status.setAttribute("label", value);
				break;

			case "wwlbar.state.disabled":
				var status = document.getElementById("wwlbar-status-menu");
				if(status.getAttribute("status") == "disabled") status.setAttribute("label", value);
				break;
		}
	},

	getTranslatedUIstringByName: function(name)
	{
		for(var i = 0; i < this.strings.length; i++)
			if(this.strings[i][0] == name)
				return this.strings[i][2];

		return "";
	},

	translateLanguageMenu: function(menu, callback)
	{
		var length = menu.itemCount;

		var translateMenuItem = function(index)
		{
			if(index == length)
			{
				wwlbar.updateCache();

				if(callback)
					callback();

				return;
			}

			var item = menu.getItemAtIndex(index);
			var iso  = item.getAttribute("value");

			if(iso == "mlt")
				iso = "en"

			if(!item.hasAttribute("original"))
				item.setAttribute("original", item.getAttribute("label"));

			var labels = [item.getAttribute("original")];
			var isos   = [iso];

			var cached = wwlbar.getFromCache("chrome://wwlbar", labels[0], wwlbar.tl);
			if(cached.length)
			{
				item.setAttribute("label", cached);
				translateMenuItem(index + 1);
			}
			else
			{
				var nextIndex = index + 1;

				// Look ahead:
				for(var i = nextIndex; i < length; i++)
				{
					var nextItem = menu.getItemAtIndex(i);

					if(!nextItem.hasAttribute("original"))
						nextItem.setAttribute("original", nextItem.getAttribute("label"));

					var nextLabel = nextItem.getAttribute("original");

					if(!wwlbar.getFromCache("chrome://wwlbar", nextLabel, wwlbar.tl).length && ((labels.join(",").length + nextLabel.length) < 100))
					{
						labels.push(nextLabel);
						isos.push(nextItem.getAttribute("value"));

						++nextIndex;
					}
					else break;
				}

				var params = [["v", "1.0"], ["userip", wwlbar.ip]];

				for(i = 0; i < labels.length; i++)
				{
					params.push(["q", labels[i]]);
					params.push(["langpair", isos[i] + "|" + wwlbar.tl]);
				}

				wwlbar.callExternal("http://ajax.googleapis.com/ajax/services/language/translate?", params, function(response, failed)
				{
					var ret = null;

					try
					{
						var nativeJSON = Components.classes["@mozilla.org/dom/json;1"].createInstance(Components.interfaces.nsIJSON);

						ret = nativeJSON.decode(response);
					}
					catch(e) { }

					if(ret && ret.responseData)
					{
						if(ret.responseData.translatedText) // single item
						{
							var translation = ret.responseData.translatedText;
							item.setAttribute("label", translation);
							wwlbar.storeInCache("chrome://wwlbar", labels[0], translation, wwlbar.tl);
						}
						else
						{
							for(i = 0; i < ret.responseData.length; i++)
							{
								var ret2 = ret.responseData[i];
								if(ret2 && ret2.responseData)
								{
									var translation = ret2.responseData.translatedText;

									var nextItem = menu.getItemAtIndex(index + i);
									nextItem.setAttribute("label", translation);

									wwlbar.storeInCache("chrome://wwlbar", labels[i], translation, wwlbar.tl);
								}
							}
						}
					}

					setTimeout(function() { translateMenuItem(nextIndex); }, 50);
				});
			}
		};

		translateMenuItem(0);
	},

	// Status bar operation:

	cycleStatus: function()
	{
		this.branch.setBoolPref("collapsed", !this.collapsed);
	},

	// Cache operation:

	storeInCache: function(url, original, translation, tl)
	{
		var url_ = this.cache[this.domain(url)];
		if(!url_)
			url_ = this.cache[this.domain(url)] = [];

		for(var i = 0; i < url_.length; i++)
		{
			if((url_[i][0] == original) && (url_[i][3] == tl))
			{
				url_[i][1] = translation;
				url_[i][2] = new Date();
				break;
			}
		}

		if(i == url_.length)
			url_.push([original, translation, new Date(), tl]);
	},

	getFromCache: function(url, original, tl)
	{
		var url_ = this.cache[this.domain(url)];
		if(!url_)
			return "";

		for(var i = 0; i < url_.length; i++)
		{
			var element = url_[i];

			if((element[0] == original) && (element[3] == tl))
				if((new Date().getTime() - element[2].getTime()) < 172800000) // 1000 * 60* 60 * 48 = 172800000 = 2 days
					return element[1];
		}

		return "";
	},

	// Serialize cache back to disk file:
	updateCache: function()
	{
		// Setup unicode converter:
		var suniconvCID = "@mozilla.org/intl/scriptableunicodeconverter";
		var suniconvIID = this.Ci.nsIScriptableUnicodeConverter;

		var uniConv = this.Cc[suniconvCID].createInstance(suniconvIID);
		uniConv.charset = "UTF-8";

		// Construct the XMLstring out of the cache:
		var string = [];
		string.push("<?xml version=\"1.0\" ?><root>");

		for(var i in this.cache)
		{
			string.push("<unit url=\"" + encodeURIComponent(i) + "\">");

			for(var j = 0; j < this.cache[i].length; j++)
			{
				var cacheItem = this.cache[i][j];
				string.push("<element original=\"" + encodeURIComponent(uniConv.ConvertFromUnicode(cacheItem[0])) + "\" translation=\"" + encodeURIComponent(uniConv.ConvertFromUnicode(cacheItem[1])) + "\" time=\"" + cacheItem[2].toGMTString() + "\" tl=\"" + cacheItem[3] + "\" />");
			}

			string.push("</unit>");
		}

		string.push("</root>");
		string = string.join("");

		// Path to the cache file:
		const id = "wwlbar@worldwidelexicon.org";

		var cache = this.Cc["@mozilla.org/extensions/manager;1"]
						.getService(this.Ci.nsIExtensionManager)
						.getInstallLocation(id)
						.getItemLocation(id); 

		cache.append("cache.xml");

		// Write the file:
		var fostream = this.Cc["@mozilla.org/network/file-output-stream;1"].createInstance(this.Ci.nsIFileOutputStream);

		try
		{
			fostream.init(cache, 0x02 | 0x08 | 0x20, 0666, 0);
			fostream.write(string, string.length);
			fostream.close();
		}
		catch(e) { }
	},

	// Server handling:
	getServer: function(docUrl, sl, tl)
	{
		for(var i = 2; i < this.servers.length; i++)
		{
			if(this.servers[i].type == "pair")
			{
				if((this.servers[i].sl == sl) && (this.servers[i].tl == tl))
					return i;
			}
			else
			{
				if(this.domain(this.servers[i].url).indexOf(this.domain(docUrl)) != -1)
					return i;
			}
		}

		return 0;
	},

	reloadServers: function()
	{
		var suniconvCID = "@mozilla.org/intl/scriptableunicodeconverter";
		var suniconvIID = this.Ci.nsIScriptableUnicodeConverter;

		var uniConv = this.Cc[suniconvCID].createInstance(suniconvIID);
		uniConv.charset = "UTF-8";

		var dom = this.loadXML("servers.xml");

		var servers = dom.documentElement.childNodes;
		for(var i = 0; i < servers.length; i++)
		{
			var server = servers[i];

			this.servers.push({service: uniConv.ConvertToUnicode(server.getAttribute("service")),
							   type:    server.getAttribute("type"),
							   sl:      server.getAttribute("sl"),
							   tl:      server.getAttribute("tl"),
							   url:     server.getAttribute("url")});
		}
	},

	// Utilities:
	loadXML: function(name)
	{
		// Find the cache file:
		const id = "wwlbar@worldwidelexicon.org";

		var file = this.Cc["@mozilla.org/extensions/manager;1"]
						.getService(this.Ci.nsIExtensionManager)
						.getInstallLocation(id)
						.getItemLocation(id); 

		file.append(name);

		// Open an input stream from file
		var istream = this.Cc["@mozilla.org/network/file-input-stream;1"].createInstance(this.Ci.nsIFileInputStream);
		istream.init(file, 0x01, 0444, 0);
		istream.QueryInterface(this.Ci.nsILineInputStream);

		// read lines into array
		var line = {}, lines = [], hasmore;
		do
		{
			hasmore = istream.readLine(line);
			lines.push(line.value); 
		}
		while(hasmore);

		istream.close();

		var xml = lines.join("");
		xml = xml.substr(xml.indexOf("<"));

		// Parse string into DOM tree:
		return (new DOMParser()).parseFromString(xml, "text/xml");
	}
};

// 'wwlbar_tab' - holds per-tab information and handles specific tab:

function wwlbar_tab(browser)
{
	this.init(browser);
}

wwlbar_tab.prototype = {

	browser: null,		// browser object this object is bound to

	sl: "en",			// source language for this tab

	meta: [],			// metadata for the page ([0] - title, [1] - description, [2] - array of keywords)
	textNodes: [],		// array of text nodes on the page
	originals: [],		// array of original text contents of text nodes on the page
	translations: [],	// array of metadata for each of the translatable nodes

	timer: null,		// timer for the translation overlay
	helper: null,		// helper node in the current document

	// constructor:
	init: function(browser, active)
	{
		this.browser = browser;
		this.browser.wwlbar_tab = this; // attach this 'wwlbar_tab' object to the browser

		this.browser.addEventListener("DOMContentLoaded", this, false);
	},

	uninit: function()
	{
		// proper garbage collection:
		this.browser.removeEventListener("DOMContentLoaded", this, false);
	},

	handleEvent: function(event)
	{
		switch(event.type)
		{
			case "DOMContentLoaded":
			{
				var doc = event.originalTarget;
				var brw = gBrowser.getBrowserForDocument(doc);

				for(var i = 0; i < wwlbar.tabs.length; i++)
				{
					var tab = wwlbar.tabs[i];
					if(brw == tab.browser)
					{
						tab.meta = [];
						tab.textNodes = [];
						tab.originals = [];
						tab.translations = [];

						if(doc.location.href == brw.contentDocument.location.href)
						{
							if(!wwlbar.enabled || !wwlbar.shouldTranslate(doc))
							{
								if(wwlbar.autosidebar)
									wwlbar.toggleSidebar(false);

								wwlbar.branch.setBoolPref("enabled", false);
							}
							else tab.parseDocument(doc);
						}

						break;
					}
				}

				break;
			}
		}
	},

	detectLanguage: function(doc, callback)
	{
		if(!wwlbar.enabled || !wwlbar.shouldTranslate(doc))
		{
			if(wwlbar.autosidebar)
				wwlbar.toggleSidebar(false);

			wwlbar.branch.setBoolPref("enabled", false);
			return;
		}

		// Get the document locale, if possible:
		if(doc.documentElement.hasAttribute("lang"))
		{
			var locale = doc.documentElement.getAttribute("lang");

			if(locale.indexOf("-") != -1)
				locale = locale.split("-")[0];

			wwlbar.setSourceLanguage(locale);
		}
		else if(doc.documentElement.hasAttribute("xml:lang"))
		{
			var locale = doc.documentElement.getAttribute("xml:lang");

			if(locale.indexOf("-") != -1)
				locale = locale.split("-")[0];

			wwlbar.setSourceLanguage(locale);
		}
		else wwlbar.setSourceLanguage(wwlbar.tl);

		if((this.sl != wwlbar.tl) || (doc.location.href.indexOf("about:") == 0))
		{
			if(callback)
				callback(doc);
		}
		else
		{
			var that = this;

			// Make a call to the translation server:
			var host = wwlbar.domain(doc.location.host);
			wwlbar.updateStatusbar(that, "detecting", host, 0, true, "WWL");

			wwlbar.callService("/language", 0, [["domain", host]], function(response)
			{
				if(response && (response.indexOf("disable") != -1))
				{
					for(var i = 0; i < wwlbar.stoplist.length; i++)
						if(wwlbar.stoplist[i] == host)
							break;

					if(i == wwlbar.stoplist.length)
						wwlbar.stoplist.push(host);

					wwlbar.updateStatusbar(that, -1);
					wwlbar.setSourceLanguage(wwlbar.tl);
					return;
				}
				else if(response && (response.length > 0) && (response.length < 5))
				{
					// translation server returned a legimate response:
					wwlbar.setSourceLanguage(response);
				}

				if(that.sl != wwlbar.tl)
				{
					wwlbar.updateStatusbar(that, -1);

					if(callback)
						callback(doc);
				}
				else
				{
					// Initial parsing of the document:
					var treeWalker = that.getTreeWalkerFromDoc(doc);
					var text = "";

					while(treeWalker.nextNode())
					{
						var tmp = treeWalker.currentNode.textContent;

						if(text.length < tmp.length)
							text = tmp;
					}

					var limit = 85;

					if(text.length > limit)
					{
						var dot = text.indexOf(".", 0);
						if((dot == -1) || (dot > limit))
							dot = text.indexOf(";", 0);
						if((dot == -1) || (dot > limit))
							dot = text.indexOf(",", 0);
						if((dot == -1) || (dot > limit))
							dot = text.indexOf(" ", 0 + Math.floor(limit / 2));
						if(dot == -1)
							dot = text.indexOf(" ", 0);
						if(dot == -1)
							dot = limit;

						text = text.substr(0, dot + 1);
					}

					if(text.length)
					{
						// Make a call to Google translation API, language detection:
						wwlbar.updateStatusbar(that, "detecting", host, 0, true, "Google");
						wwlbar.callExternal("http://ajax.googleapis.com/ajax/services/language/detect?", [["v", "1.0"], ["userip", wwlbar.ip], ["q", text]], function(response)
						{
							var ret = null;

							try
							{
								var nativeJSON = Components.classes["@mozilla.org/dom/json;1"].createInstance(Components.interfaces.nsIJSON);

								ret = nativeJSON.decode(response);
							}
							catch(e) { }

							var lang = ret.responseData.language;

							if(lang.indexOf("-") != -1)
								lang = lang.split("-")[0];

							wwlbar.setSourceLanguage(lang);
							wwlbar.updateStatusbar(that, -1);

							if(that.sl != wwlbar.tl)
								if(callback)
									callback(doc);
						});
					}
				}
			});
		}
	},

	parseDocument: function(doc)
	{
		var that = this;
		this.detectLanguage(doc, function() { that.extractTextNodes(doc, that.sl == "mlt"); });
	},

	reparseDocument: function(doc, multilingual)
	{
		if(this.sl == wwlbar.tl)
			return;

		if(this.sl == "mlt")
			multilingual = true;

		if(!this.textNodes.length)
			this.extractTextNodes(doc, multilingual);
		else
		{
			for(var i = 0; i < this.textNodes.length; i++)
				this.restoreTextNode(i);

			this.meta = [];
			this.textNodes = [];
			this.originals = [];
			this.translations = [];

			this.extractTextNodes(doc, multilingual);
		}
	},

	getTreeWalkerFromDoc: function(doc)
	{
		function nodeIsScript(node)
		{
			while(node)
			{
				if(node.tagName && ((node.tagName.toLowerCase() == "script") || (node.tagName.toLowerCase() == "noscript")))
					return true;

				node = node.parentNode;
			}

			return false;
		}

		function nodeIsStyle(node)
		{
			while(node)
			{
				if(node.tagName && (node.tagName.toLowerCase() == "style"))
					return true;

				node = node.parentNode;
			}

			return false;
		}

		function textIsInvalid(text)
		{
			if(text.length == 0)
				return true;

			var text_ = text.replace(/(^\s+)|(\s+$)/g, "");
			if(text_.length == 0)
				return true;

			if(text_.replace(/[\d\s\[\]\(\)\.\{\}\+\-=\\\/%&:,\?|!~]/g, "").length == 0)
				return true;

			return false
		}

		var treeWalker = document.createTreeWalker(doc.body, NodeFilter.SHOW_TEXT, { acceptNode: function(node)
		{
			var fail = (node.parentNode == null);
			if(!fail)
				fail = nodeIsScript(node);
			if(!fail)
				fail = nodeIsStyle(node);
			if(!fail)
				fail = textIsInvalid(node.textContent);

			return fail ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT;
		}},
		false);

		return treeWalker;
	},

	extractTextNodes: function(doc, multilingual)
	{
		function nodeHasParent(node, parentTag)
		{
			parentTag = parentTag.toLowerCase();

			while(node && node.parentNode && node.parentNode.tagName)
			{
				if(node.parentNode.tagName.toLowerCase() == parentTag)
					return true;

				node = node.parentNode;
			}

			return false;
		}

		if(!wwlbar.enabled || !wwlbar.shouldTranslate(doc))
		{
			if(wwlbar.autosidebar)
				wwlbar.toggleSidebar(false);

			wwlbar.branch.setBoolPref("enabled", false);
			return;
		}

		if(wwlbar.autosidebar)
			wwlbar.toggleSidebar(true);
		else
			wwlbar.updateSidebar(wwlbar.servers[wwlbar.getServer(doc.location.href, this.sl, wwlbar.tl)], this.sl, doc.location.href);

		this.helper = doc.getElementById("wwl_tmp_node");
		if(this.helper)
			doc.body.removeChild(this.helper);

		var div = doc.getElementById("wwl_action_node");
		if(div)
			doc.body.removeChild(div);

		// Metadata extraction:
		if(doc.title)
			this.meta[0] = doc.title;

		var meta = doc.getElementsByTagName("meta");
		for(var i = 0; i < meta.length; i++)
		{
			var name = meta[i].getAttribute("name");

			if(name == "description")
				this.meta[1] = meta[i].getAttribute("content");
			else if(name == "keywords")
				this.meta[2] = meta[i].getAttribute("content").split(",");
		}

		// Page parsing:
		var treeWalker = this.getTreeWalkerFromDoc(doc);

		var priority1Nodes = [], priority2Nodes = [], otherNodes = [];
		var priority1Texts = [], priority2Texts = [], otherTexts = [];
		var priorityIndex = 0;

		while(treeWalker.nextNode())
		{
			var text = treeWalker.currentNode.textContent;
			if(text && text.length)
			{
				var isTag = (nodeHasParent(treeWalker.currentNode, "h1") || nodeHasParent(treeWalker.currentNode, "h2") || nodeHasParent(treeWalker.currentNode, "h3") ||
							 nodeHasParent(treeWalker.currentNode, "h4") || nodeHasParent(treeWalker.currentNode, "h5") || nodeHasParent(treeWalker.currentNode, "h6"));

				if(isTag && (priorityIndex++ < 10))
				{
					priority1Nodes.push(treeWalker.currentNode);
					priority1Texts.push(text);
				}
				else if(isTag || (text.split(" ").length > 4))
				{
					priority2Nodes.push(treeWalker.currentNode);
					priority2Texts.push(text);
				}
				else
				{
					otherNodes.push(treeWalker.currentNode);
					otherTexts.push(text);
				}

				this.translations.push([false, null, 0, false]);	// translated, guid, avg score, human translation
			}
		}

		this.textNodes = priority1Nodes.concat(priority2Nodes).concat(otherNodes);
		this.originals = priority1Texts.concat(priority2Texts).concat(otherTexts);

		if(!this.textNodes.length)
			return;

		wwlbar.branch.setBoolPref("collapsed", false);

		for(var i = 0; i < this.textNodes.length; i++)
		{
			var node = this.textNodes[i];
			var parent = node.parentNode;

			if((parent.childNodes.length == 1) && (parent.childNodes[0] == node))
				continue;

			var span = doc.createElement("wwl");

			span.textContent = this.originals[i];
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

		var that = this;

		// Create a hidden span element to render escaped text info HTML:
		if(!this.helper)
		{
			this.helper = doc.createElement("span");
			this.helper.style.display = "none";
			this.helper.id = "wwl_tmp_node";
		}

		doc.body.appendChild(this.helper);

		// Create a div to house the translation and voting interface:
		if(div)
		{
			doc.body.appendChild(div);
		}
		else
		{
			div = doc.createElement("wwl");
			div.id = "wwl_action_node";
			div.style.display = "none";
			div.style.position = "absolute";
			div.style.top = "0px";
			div.style.left = "0px";
			div.style.width = "350px";
			div.style.height = "352px";
			div.style.padding = "3px";
			div.style.backgroundColor = "#EEEEEE";
			div.style.border = "1px solid gray";
			div.style.textAlign = "left";
			div.style.zIndex = "9999";
			div.style.fontSize = "14px";
			div.style.fontFamily = "Tahoma Arial";
			div.style.fontWeight = "300";
			div.innerHTML = "<table style=\"color:#404040;margin:0px;padding:0px;border:0px;border-collapse:collapse;width:100%;height:294px;background:transparent none;\"><tr><td>" + wwlbar.getTranslatedUIstringByName("wwlbar.dialog.source") + ":</td><td style=\"text-align:right\"><input id=\"wwl_close_translation\" type=\"image\" title=\"" + wwlbar.getTranslatedUIstringByName("wwlbar.dialog.close") + "\" src=\"http://worldwidelexicon.appspot.com/image/button-close.png\" width=\"12px\" height=\"12px\"></input></td></tr><tr><td colspan=\"2\"><textarea readonly=\"true\" style=\"background-color: #F2F2F2; border: 1px solid #888; color: black; font-size: 13px; width: 348px; height: 120px; margin: 0px; padding: 0px;\"></textarea></td></tr><tr><td colspan=\"2\">" + wwlbar.getTranslatedUIstringByName("wwlbar.dialog.translation") + ":</td></tr><tr><td colspan=\"2\"><textarea style=\"background-color: #F2F2F2; border: 1px solid #888; color: black; font-size: 13px; width: 348px; height: 120px; margin: 0px; padding: 0px;\"></textarea><span style=\"display: none\"></span></td></tr><tr><td><input type=\"checkbox\" id=\"wwl_translate_meta\">&nbsp;" + wwlbar.getTranslatedUIstringByName("wwlbar.dialog.meta") + "</input></td><td style=\"text-align:right; padding-top:5px\"><input id=\"wwl_submit_translation\" type=\"image\" title=\"" + wwlbar.getTranslatedUIstringByName("wwlbar.dialog.submit") + "\" src=\"http://worldwidelexicon.appspot.com/image/button-save.png\" width=\"16px\" height=\"16px\"></input></td></tr><tr><td colspan=\"2\"><hr style=\"margin:3px 0px;padding:0px;\" /></td></tr><tr><td>" + wwlbar.getTranslatedUIstringByName("wwlbar.dialog.score") + ":</td><td id=\"wwl_avg_score\" style=\"text-align:right\">N/A</td></tr><tr><td>" + wwlbar.getTranslatedUIstringByName("wwlbar.dialog.vote") + ":</td><td style=\"text-align:right\"><span style=\"margin: 0px 5px 0px 10px\"><input type=\"image\" id=\"wwl_score_up\" title=\"" + wwlbar.getTranslatedUIstringByName("wwlbar.dialog.up") + "\" src=\"http://worldwidelexicon.appspot.com/image/button-up.png\" width=\"16px\" height=\"16px\"></input></span>&nbsp;<span style=\"margin: 0px 5px 0px 10px\"><input type=\"image\" id=\"wwl_score_down\" title=\"" + wwlbar.getTranslatedUIstringByName("wwlbar.dialog.down") + "\" src=\"http://worldwidelexicon.appspot.com/image/button-down.png\" width=\"16px\" height=\"16px\"></input></span>&nbsp;<span style=\"margin: 0px 5px 0px 10px\"><input type=\"image\" id=\"wwl_score_block\" title=\"" + wwlbar.getTranslatedUIstringByName("wwlbar.dialog.block") + "\" src=\"http://worldwidelexicon.appspot.com/image/button-block.png\" width=\"16px\" height=\"16px\"></input></span></td></tr></table>";

			doc.body.appendChild(div);

			// Attach events to the overlay:

			div.addEventListener("mouseover", function()
			{
				if(that.timer)
				{
					clearTimeout(that.timer);
					that.timer = 0;
				}
			},
			false);

			div.addEventListener("mouseout", function()
			{
				that.timer = setTimeout(function()
				{
					if(!div.firstChild.rows[1].cells[0].firstChild.focused && !div.firstChild.rows[3].cells[0].firstChild.focused)
					{
						div.style.display = "none";

						that.timer = 0;
					}
				},
				500);
			},
			false);

			// Attach events to the overlay elements:

			div.firstChild.rows[1].cells[0].firstChild.addEventListener("focus", function()
			{
				this.focused = true;
			},
			false);
			div.firstChild.rows[1].cells[0].firstChild.addEventListener("blur", function()
			{
				this.focused = false;
			},
			false);

			div.firstChild.rows[3].cells[0].firstChild.addEventListener("focus", function()
			{
				this.focused = true;
			},
			false);
			div.firstChild.rows[3].cells[0].firstChild.addEventListener("blur", function()
			{
				this.focused = false;
			},
			false);

			// Submit translation:
			var submit = doc.getElementById("wwl_submit_translation");
			submit.addEventListener("click", function()
			{
				var tt = div.firstChild.rows[3].cells[0].firstChild.value;
				wwlbar.callService("/submit", 0, [["url",    wwlbar.domain(doc.location.href)],
												  ["domain", wwlbar.domain(doc.location.host)],
												  ["sl",     that.sl],
												  ["tl",     wwlbar.tl],
												  ["st",     div.firstChild.rows[1].cells[0].firstChild.value],
												  ["tt",     tt],
												  ["output", "text"]
												 ],
									function(response, failed)
									{
										// Update the text node:
										that.restoreTextNode(div.wwlIndex);
										that.updateTextNode(div.wwlIndex, that.textNodes[div.wwlIndex], tt, "humanUnknown");

										div.style.display = "none";

										//
										if(((that.meta[0] && that.meta[0].length) || (that.meta[1] && that.meta[1].length) || (that.meta[2] && that.meta[2].length)) && doc.getElementById("wwl_translate_meta").checked)
										{
											var retObj = {action: "", url: doc.location.href, sl: that.sl, tl: wwlbar.tl, t: that.meta[0] || "", tt: "", d: that.meta[1] || "", td: "", k: that.meta[2] || "", tk: "", strings: ((wwlbar.tl != "en") ? wwlbar.strings : null)};
											window.openDialog('chrome://wwlbar/content/meta.xul', 'WWLmeta', 'centerscreen=yes,chrome=yes,modal=yes', retObj);

											if(retObj.action == "meta")
											{
												var params = [["url", wwlbar.domain(doc.location.href)], ["domain", wwlbar.domain(doc.location.host)]];

												if(that.meta[0] && that.meta[0].length)
												{
													params.push(["title", that.meta[0]]);

													if(retObj.tt.length)
														params.push(["ttitle", retObj.tt]);
												}

												if(that.meta[1] && that.meta[1].length)
												{
													params.push(["description", that.meta[1]]);

													if(retObj.td.length)
														params.push(["tdescription", retObj.td]);
												}

												if(that.meta[2] && that.meta[2].length)
												{
													params.push(["keywords", that.meta[2]]);

													if(retObj.tk.length)
														params.push(["tkeywords", retObj.tk]);
												}

												wwlbar.callService("/submit", 0, params, function()
												{
													setTimeout(function()
													{
														var url = "http://" + wwlbar.servers[0] + "/p?" + (wwlbar.username.length ? (wwlbar.username + "&") : "") + "tl=" + wwlbar.tl + (wwlbar.password.length ? ("&sid=" + wwlbar.md5(wwlbar.password)) : "") + "&url=" + encodeURIComponent(doc.location.href);

														if(gBrowser.selectedBrowser.webNavigation.document.location.href.indexOf("about:") == 0)
															gBrowser.selectedBrowser.webNavigation.document.location.href = url;
														else
															gBrowser.selectedTab = gBrowser.addTab(url);
													},
													500);
												});
											}
										}
									}
								);
			},
			false);

			// Scoring:
			var up = doc.getElementById("wwl_score_up");
			up.addEventListener("click", function()
			{
				if(!up.disabled)
				wwlbar.callService("/scores/vote", 0, [["guid", div.firstChild.rows[3].cells[0].childNodes[1].textContent],
													   ["votetype", "up"]
													  ],
									function(response, failed)
									{
										div.style.display = "none";
									}
								);
			},
			false);

			var down = doc.getElementById("wwl_score_down");
			down.addEventListener("click", function()
			{
				if(!down.disabled)
				wwlbar.callService("/scores/vote", 0 [["guid", div.firstChild.rows[3].cells[0].childNodes[1].textContent],
													  ["votetype", "down"]
												     ],
									function(response, failed)
									{
										div.style.display = "none";
									}
								);
			},
			false);

			var block = doc.getElementById("wwl_score_block");
			block.addEventListener("click", function()
			{
				if(!block.disabled)
				wwlbar.callService("/scores/vote", 0, [["guid", div.firstChild.rows[3].cells[0].childNodes[1].textContent],
													   ["votetype", "block"]
													  ],
									function(response, failed)
									{
										div.style.display = "none";
									}
								);
			},
			false);

			// Close dialog:
			var close = doc.getElementById("wwl_close_translation");
			close.addEventListener("click", function()
			{
				div.style.display = "none";
			},
			false);
		}

		this.translateDocument(doc, multilingual);
	},

	// Retrieves the (human-made) translations for the current page:
	translateDocument: function(doc, multilingual)
	{
		if(!wwlbar.enabled)
			return;

		var that = this;
		wwlbar.callService("/q", wwlbar.getServer(this.browser.contentDocument.location.href, this.sl, wwlbar.tl),
													 [["sl",  this.sl],
													  ["tl",  wwlbar.tl],
													  ["url", wwlbar.domain(this.browser.contentDocument.location.href)],
													  ["allow_anonymous", wwlbar.allowAnonymous ? "y" : "n"],
													  ["allow_machine",   "n"],
													  ["allow_unscored",  wwlbar.allowUnscored  ? "y" : "n"],
													  ["minimum_score",   wwlbar.minScore],
													  ["output", "json"]
													 ],
							function(response, failed)
							{
								if(failed)
								{
									if(wwlbar.allowMachine)
										that.translateChunk(0, 0, "", 0, (multilingual == true), "");
								}
								else
								{
									var obj = null;

									try
									{
										var nativeJSON = Components.classes["@mozilla.org/dom/json;1"].createInstance(Components.interfaces.nsIJSON);

										obj = nativeJSON.decode(response);
									}
									catch(e) { }

									if(obj.records && obj.records[0].tx)
									{
										// Scan the response array, leave only the highest-rated translations:
										for(var i = obj.records.length - 1; i >= 0; i--)
										{
											if(!obj.records[i].tx) continue;

											var st = obj.records[i].tx.st;

											for(var j = i - 1; j >= 0; j--)
											{
												if(obj.records[j].tx.st == st)
												{
													// the record with "proz." in the translator's name takes precedence:
													if(obj.records[i].tx.username.toLowerCase().indexOf("proz.") == 0)
													{
														obj.records.splice(j, 1);
														i = obj.records.length - 1;
														break;
													}
													else if(obj.records[j].tx.username.toLowerCase().indexOf("proz.") == 0)
													{
														obj.records.splice(i, 1);
														i = obj.records.length - 1;
														break;
													}

													// Of 2 unscored translations, the latest one takes precedence:
													if(!obj.records[j].tx.avgscore && !obj.records[i].tx.avgscore)
													{
														obj.records.splice(j, 1);
														i = obj.records.length - 1;
														break;
													}

													// Of scored and unscored translations, the scored takes precedence if score is > 0:
													if(obj.records[j].tx.avgscore && !obj.records[i].tx.avgscore)
													{
														obj.records.splice((parseFloat(obj.records[j].tx.avgscore) > 0) ? i : j, 1);
														i = obj.records.length - 1;
														break;
													}

													// The same:
													if(!obj.records[j].tx.avgscore && obj.records[i].tx.avgscore)
													{
														obj.records.splice((parseFloat(obj.records[i].tx.avgscore) > 0) ? j : i, 1);
														i = obj.records.length - 1;
														break;
													}

													// Of 2 scored translations, the highest scored takes precedence:
													if(obj.records[j].tx.avgscore && obj.records[i].tx.avgscore)
													{
														obj.records.splice((parseFloat(obj.records[i].tx.avgscore) < parseFloat(obj.records[j].tx.avgscore)) ? i : j, 1)
														i = obj.records.length - 1;
														break;
													}
												}
											}
										}

										// Make the actual translation:
										for(i = 0; i < obj.records.length; i++)
										{
											var entry = obj.records[i].tx;

											if(entry && (entry.sl == that.sl) && (entry.tl == wwlbar.tl))
											{
												var st = entry.st;
												var tt = entry.tt;

												// find the source text for this translation:
												for(var j = 0; j < that.originals.length; j++)
												{
													if((that.originals[j] == st) && (that.translations[j][0] == false))
													{
														index = j;

														// Store data:
														that.translations[j][0] = true;
														that.translations[j][1] = entry.guid;
														var score = that.translations[j][2] = (typeof(entry.avgscore) == "undefined") ? null : parseInt(entry.avgscore, 10);
														var human = that.translations[j][3] = true;

														if(st != tt)
														{
															wwlbar.updateStatusbar(that, "translating", j, 0, true);
															that.updateTextNode(j, that.textNodes[j], tt, ((human && (score != null)) ? (((score >= 4) || (entry.username.toLowerCase().indexOf("proz.") == 0)) ? "humanHigh" : "humanLow") : "humanUnknown"));
														}
													}
												}
											}
										}
									}

									if(wwlbar.allowMachine)
										that.translateChunk(0, 0, "", 0, (multilingual == true), "");
								}
							}
						);
	},

	// Retrieves the (probably machine-made) translations for the current page, by index of the text node:
	translateChunk: function(index, chunk, prevTranslation, prevLength, detectEach, prevLanguage)
	{
		if(!wwlbar.enabled || (index == this.translations.length))
		{
			if(index == this.translations.length)
			{
				// cycle through all the untranslated text chunks and attach events to them:
				for(var i = 0; i < this.translations.length; i++)
				{
					if(!this.translations[i][0])
					{
						var node = this.textNodes[i];
						node = node.tagName ? node : node.parentNode;

						this.attachShowOverlay(node, "", i);
					}
				}
			}

			wwlbar.updateStatusbar(this, -1);
			wwlbar.updateCache();

			return;
		}

		var doc  = this.browser.contentDocument;
		var node = this.textNodes[index];

		if(this.translations[index][0]) 	// already translated
		{
			this.translateChunk(index + 1, 0, "", 0, detectEach, prevLanguage);
			return;
		}

		var cache = wwlbar.getFromCache(doc.location.href, this.originals[index], wwlbar.tl);
		if(cache.length)
		{
			if(!chunk && (cache != this.originals[index]))
				if(!(wwlbar.bilingual && !node.tagName && !node.parentNode))
					this.updateTextNode(index, node, cache, "machine");

			this.translateChunk(index + 1, 0, "", 0, detectEach, prevLanguage);
			return;
		}

		wwlbar.updateStatusbar(this, "translating", index, chunk, false, "Google");

		var limit = 70;
		var text = this.originals[index];

		if(text.length > limit)
		{
		    if(prevLength > 0)
				text = text.substring(prevLength);

			text = text.match(new RegExp("^([\\s\\S]{1," + (limit - 1) + "}[.;,(]|[\\s\\S]{1," + (limit - 1) + "}\\s|[\\s\\S]{0," + limit + "})", "m"))[0];

			prevLength += text.length;

			if(prevLength < this.originals[index].length)
				chunk++;
			else
				chunk = prevLength = 0;
		}
		else
		{
			chunk = prevLength = 0;
		}

		var match = text.match(/^(\s*)([\s\S]*?)(\s*)$/m);
		var prespace = [match[1]];
		var text = [match[2]];
		var postspace = [match[3]];

		var that = this;

		setTimeout(function()
		{
			if(detectEach && !prevLanguage.length)
			{
				wwlbar.callExternal("http://ajax.googleapis.com/ajax/services/language/detect?", [["v", "1.0"], ["userip", wwlbar.ip], ["q", text[0]]], function(response)
				{
					var ret = null;

					try
					{
						var nativeJSON = Components.classes["@mozilla.org/dom/json;1"].createInstance(Components.interfaces.nsIJSON);

						ret = nativeJSON.decode(response);
					}
					catch(e) { }

					var lang = ret.responseData.language;

					if(lang.indexOf("-") != -1)
						lang = lang.split("-")[0];

					that.translateChunk(index, 0, "", 0, detectEach, lang);
				});
			}
			else
			{
				var lang = (prevLanguage.length ? prevLanguage : that.sl);
				if(lang != wwlbar.tl)
				{
					if(text[0].length == 0)
					{
						// after whitespace stripping, we may have no text to translate.
						// todo: tidy up the duplicated code here.
						var translation = prevTranslation + prespace[0] + postspace[0];

						// this updateTextNode triggers when the last chunk contains only whitespace.
						if(!chunk && (translation != that.originals[index]))
						{
							if(!(wwlbar.bilingual && !node.tagName && !node.parentNode))
							{
								that.updateTextNode(index, node, translation, "machine");
								wwlbar.storeInCache(doc.location.href, that.originals[index], translation, wwlbar.tl);
							}
						}

						that.translateChunk(index + ((chunk == 0) ? 1 : 0), chunk, ((chunk == 0) ? "" : translation), prevLength, detectEach, (chunk == 0) ? "" : prevLanguage);
					}
					else
					{
						var params = [["v", "1.0"], ["userip", wwlbar.ip]];
						params.push(["q", text[0]]);

						// Look ahead for other small text chunks:
						var nextIndex = index + 1;

						if(!chunk && !prevTranslation.length)
						{
							while(nextIndex < that.originals.length)
							{
								var next = that.originals[nextIndex];

								if(!wwlbar.getFromCache(doc.location.href, next, wwlbar.tl).length && (next.length < limit && ((text.join("").length + next.length) < limit)))
								{
									var _match = next.match(/^(\s*)([\s\S]*?)(\s*)$/m);
									prespace.push(_match[1]);
									text.push(_match[2]);
									postspace.push(_match[3]);

									params.push(["q", _match[2]]);
									++nextIndex;
								}
								else break;
							}
						}

						params.push(["langpair", (prevLanguage.length ? prevLanguage : that.sl) + "|" + wwlbar.tl]);

						wwlbar.callExternal("http://ajax.googleapis.com/ajax/services/language/translate?", params, function(response, failed)
						{
							// if we have no translation, restore the old text.
							var ret = null;

							try
							{
								var nativeJSON = Components.classes["@mozilla.org/dom/json;1"].createInstance(Components.interfaces.nsIJSON);

								ret = nativeJSON.decode(response);
							}
							catch(e) { }

							var translation = "";
							if(ret && ret.responseData && ret.responseData.translatedText) // single item
							{
								node = that.textNodes[index];
								translation = text[0];

								if(ret.responseData.translatedText && ret.responseData.translatedText.length)
								{
									// restore whitespace, and any previous chunks:
									translation = prevTranslation + prespace[0] + ret.responseData.translatedText + postspace[0];
								}

								if(!chunk)
								{
									if(translation != that.originals[index])
									{
										if(!(wwlbar.bilingual && !node.tagName && !node.parentNode))
										{
											that.updateTextNode(index, node, translation, "machine");
											wwlbar.storeInCache(doc.location.href, that.originals[index], translation, wwlbar.tl);

											that.translations[index][0] = true;
										}
									}
								}
							}
							else
							{
								if(ret.responseData)
								{
									for(i = 0; i < ret.responseData.length; i++)
									{
										var ret2 = ret.responseData[i];
										translation = text[i];

										if(ret2 && ret2.responseData && ret2.responseData.translatedText)
										{
											// restore whitespace, and any previous chunk
											translation = prespace[i] + ret2.responseData.translatedText + postspace[i];
										}

										node = that.textNodes[index + i];
										if(translation != that.originals[index + i])
										{
											if(!(wwlbar.bilingual && !node.tagName && !node.parentNode))
											{
												that.updateTextNode(index + i, node, translation, "machine");
												wwlbar.storeInCache(doc.location.href, that.originals[index + i], translation, wwlbar.tl);

												that.translations[index + i][0] = true;
											}
										}
									}
								}
							}

							that.translateChunk(((chunk == 0) ? nextIndex : index), chunk, ((chunk == 0) ? "" : translation), prevLength, detectEach, (chunk == 0) ? "" : prevLanguage);
						});
					}
				}
				else that.translateChunk(index + 1, 0, "", 0, detectEach, "");
			}
		},
		/*Math.floor(Math.random() * 750) + 250*/100);
	},

	// Utility methods for translation overlay:
	attachShowOverlay: function(node, translation, index)
	{
		if(!node || !node.addEventListener) return;

		var that = this;
		var doc = this.browser.contentDocument;

		node.addEventListener("mouseover", function(event)
		{
			if(that.timer)
			{
				clearTimeout(that.timer);
				that.timer = 0;
			}

			var initX = 0, initY = 0, ct_ = node;
			if(ct_.offsetParent)
			{
				while (ct_.offsetParent)
				{
					initX += ct_.offsetLeft;
					initY += ct_.offsetTop;

					ct_ = ct_.offsetParent;
				}
			}
			else if (ct_.x)
			{
				initX += ct_.x;
				initY += ct_.y;
			}

			var overlay = doc.getElementById("wwl_action_node");

			that.timer = setTimeout(function()
			{
				if(that.translations[index][3])
				{
					doc.getElementById("wwl_score_up").disabled = false;
					doc.getElementById("wwl_score_up").src = "http://worldwidelexicon.appspot.com/image/button-up.png";

					doc.getElementById("wwl_score_down").disabled = false;
					doc.getElementById("wwl_score_down").src = "http://worldwidelexicon.appspot.com/image/button-down.png";

					doc.getElementById("wwl_score_block").disabled = false;
					doc.getElementById("wwl_score_block").src = "http://worldwidelexicon.appspot.com/image/button-block.png";
				}
				else
				{
					doc.getElementById("wwl_score_up").disabled = true;
					doc.getElementById("wwl_score_up").src = "http://worldwidelexicon.appspot.com/image/button-up-disabled.png";

					doc.getElementById("wwl_score_down").disabled = true;
					doc.getElementById("wwl_score_down").src = "http://worldwidelexicon.appspot.com/image/button-down-disabled.png";

					doc.getElementById("wwl_score_block").disabled = true;
					doc.getElementById("wwl_score_block").src = "http://worldwidelexicon.appspot.com/image/button-block-disabled.png";
				}

				overlay.wwlIndex = index;

				overlay.firstChild.rows[1].cells[0].firstChild.value = that.originals[index];
				overlay.firstChild.rows[3].cells[0].firstChild.value = translation;
				overlay.firstChild.rows[3].cells[0].childNodes[1].textContent = that.translations[index][1];

				doc.getElementById("wwl_avg_score").textContent = (that.translations[index][2] || "N/A");

				overlay.style.display = "block";
				overlay.style.top = initY + (((event.clientY + overlay.offsetHeight) > that.browser.clientHeight) ? (-1 * overlay.offsetHeight) : node.offsetHeight) + "px";
				overlay.style.left = initX + (((initX + overlay.offsetWidth) < doc.body.scrollWidth) ? 0 : (node.offsetWidth - overlay.offsetWidth)) + "px";

				that.timer = 0;
			},
			1000);
		},
		false);

		node.addEventListener("mouseout", function()
		{
			if(that.timer)
			{
				clearTimeout(that.timer);
				that.timer = 0;
			}
			else
			{
				that.timer = setTimeout(function()
				{
					var overlay = doc.getElementById("wwl_action_node");
					overlay.style.display = "none";

					that.timer = 0;
				},
				500);
			}
		},
		false);
	},

	restoreTextNode: function(index)
	{
		var node = this.textNodes[index];
		var parent = node.parentNode;

		if(node.nodeType == 3)
		{
			parent.textContent = this.originals[index];
			this.textNodes[index] = parent.firstChild;
		}
		else
		{
			var txt = node.ownerDocument.createTextNode(this.originals[index]);

			parent.replaceChild(txt, node);
			this.textNodes[index] = txt;
		}
	},

	updateTextNode: function(index, node, newText, color)
	{
		this.helper.innerHTML = newText;
		newText = this.helper.textContent;

		if(wwlbar.overflow)
		{
			if(node.tagName)
			{
				node.style.overflow = "auto";
			}
			else
			{
				node.parentNode.style.overflow = "auto";
			}
		}

		if(wwlbar.bilingual)
		{
			var span = this.browser.contentDocument.createElement("wwl");

			span.innerHTML = "&nbsp;(" + newText + ")";
			span.style.display = "inline";
			span.style.position = "static";
			span.style.float = "none";
			span.style.margin = "0px";
			span.style.padding = "0px";
			if(wwlbar.colorize)
			{
				if(color)
					span.style.backgroundColor = wwlbar.colors[color];

				span.style.color = "black";
			}
			span.style.border = "0px";

			if(node.tagName)
			{
				node.appendChild(span);
			}
			else
			{
				node.parentNode.appendChild(span);
			}

			this.attachShowOverlay(span, newText, index);
		}
		else
		{
			node.textContent = newText;

			if(node.tagName)
			{
				if(wwlbar.colorize)
				{
					if(color)
						node.style.backgroundColor = wwlbar.colors[color];

					node.style.color = "black";
				}

				this.attachShowOverlay(node, newText, index);
			}
			else
			{
				if(wwlbar.colorize)
				{
					if(color)
						node.parentNode.style.backgroundColor = wwlbar.colors[color];

					node.parentNode.style.color = "black";
				}

				this.attachShowOverlay(node.parentNode, newText, index);
			}
		}
	}
};

window.addEventListener("load",   function() { wwlbar.init();  }, false);
window.addEventListener("unload", function() { wwlbar.uninit() }, false);