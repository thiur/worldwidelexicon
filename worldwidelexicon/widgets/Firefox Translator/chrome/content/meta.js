/* Worldwide Lexicon translation memory developed by Brian S McConnell.
 * Firefox add-on developed by Dmitriy Khudorozhkov.
 *
 * (c) 2009 Worldwide Lexicon Inc. All rights reserved.
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
 *      specific prior written permission.
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

if(!wwlbar) { var wwlbar = {}; }

wwlbar.meta = {

	returnObj: null,

	url: "",
	sl: "",
	tl: "",

	onload: function()
	{
		this.returnObj = window.arguments[0];

		var strings = this.returnObj.strings;

		if(strings)
		{
			document.getElementById("wwl-meta-dialog").setAttribute("title", this.getTranslatedUIstringByName(strings, "wwlbar.meta.header"));
			document.getElementById("meta-title").value        = this.getTranslatedUIstringByName(strings, "wwlbar.meta.title");
			document.getElementById("meta-ttitle").value       = this.getTranslatedUIstringByName(strings, "wwlbar.meta.ttitle");
			document.getElementById("meta-description").value  = this.getTranslatedUIstringByName(strings, "wwlbar.meta.description");
			document.getElementById("meta-tdescription").value = this.getTranslatedUIstringByName(strings, "wwlbar.meta.tdescription");
			document.getElementById("meta-keywords").value     = this.getTranslatedUIstringByName(strings, "wwlbar.meta.keywords");
			document.getElementById("meta-tkeywords").value    = this.getTranslatedUIstringByName(strings, "wwlbar.meta.tkeywords");
			document.documentElement.getButton("accept").label = this.getTranslatedUIstringByName(strings, "wwlbar.userdetails.accept");
			document.documentElement.getButton("cancel").label = this.getTranslatedUIstringByName(strings, "wwlbar.cancel");
		}

		document.getElementById("wwl-meta-title").value       = this.returnObj.t;
		document.getElementById("wwl-meta-description").value = this.returnObj.d;
		document.getElementById("wwl-meta-keywords").value    = this.returnObj.k;

		this.sl  = this.returnObj.sl;
		this.tl  = this.returnObj.tl;
		this.url = this.returnObj.url;
		this.originals = [this.returnObj.t, this.returnObj.d, this.returnObj.k];

		this.translateChunk(0, 0, "", 0, false, "");
	},

	accept: function()
	{
		var tt = document.getElementById("wwl-meta-ttitle").value;
		var td = document.getElementById("wwl-meta-tdescription").value;
		var tk = document.getElementById("wwl-meta-tkeywords").value;

		this.returnObj.action = "meta";
		this.returnObj.tt = tt;
		this.returnObj.td = td;
		this.returnObj.tk = tk;
	},

	cancel: function()
	{
		this.returnObj.action = "cancel";
	},

	getTranslatedUIstringByName: function(strings, name)
	{
		for(var i = 0; i < strings.length; i++)
			if(strings[i][0] == name)
				return strings[i][2];

		return "";
	},

	// text chunk translation - taken (with changes) from the overlay.js:

	translateChunk: function(index, chunk, prevTranslation, prevLength, detectEach, prevLanguage)
	{
		function translateByIndex(index, translation)
		{
			switch(index)
			{
				case 0:
					document.getElementById("wwl-meta-ttitle").value = translation;
					break;

				case 1:
					document.getElementById("wwl-meta-tdescription").value = translation;
					break;

				case 2:
					document.getElementById("wwl-meta-tkeywords").value = translation;
					break;
			}
		}

		var wm = Components.classes["@mozilla.org/appshell/window-mediator;1"].getService(Components.interfaces.nsIWindowMediator);
		var browserWindow = wm.getMostRecentWindow("navigator:browser");
		var wwlbar_ = browserWindow.wwlbar;

		if(index == this.originals.length)
		{
			wwlbar_.updateCache();
			return;
		}

		var cache = wwlbar_.getFromCache(this.url, this.originals[index]);
		if(cache.length)
		{
			translateByIndex(index, cache);
			this.translateChunk(index + 1, 0, "", 0, detectEach, prevLanguage);
			return;
		}

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
		var prespace = match[1];
		var text = match[2]
		var postspace = match[3];

		var that = this;

		setTimeout(function()
		{
			if(detectEach && !prevLanguage.length)
			{
				wwlbar_.callExternal("http://ajax.googleapis.com/ajax/services/language/detect?", [["v", "1.0"], ["q", text]], function(response)
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
						var lang = ret.responseData.language;

						if(lang.indexOf("-") != -1)
							lang = lang.split("-")[0];
					}

					that.translateChunk(index, 0, "", 0, detectEach, lang);
				});
			}
			else
			{
				var lang = (prevLanguage.length ? prevLanguage : that.sl);
				if(lang != that.tl)
				{
				    if(text.length == 0)
					{
						// after whitespace stripping, we may have no text to translate.
						// todo: tidy up the duplicated code here.
						var translation = prevTranslation + prespace + postspace;

						// this updateTextNode triggers when the last chunk contains only whitespace.
						if(!chunk && (translation != that.originals[index]))
						{
							translateByIndex(index, translation);
							wwlbar_.storeInCache(doc.location.href, that.originals[index], translation);
						}

						that.translateChunk(index + ((chunk == 0) ? 1 : 0), chunk, ((chunk == 0) ? "" : translation), prevLength, detectEach, (chunk == 0) ? "" : prevLanguage);
					}
					else
					{
						wwlbar_.callExternal("http://ajax.googleapis.com/ajax/services/language/translate?", [["v", "1.0"], ["q", text], ["langpair", (prevLanguage.length ? prevLanguage : that.sl) + "|" + that.tl]], function(response, failed)
						{
							// if we have no translation, restore the old text.
							var translation = text;
							var ret = null;

							try
							{
								var nativeJSON = Components.classes["@mozilla.org/dom/json;1"].createInstance(Components.interfaces.nsIJSON);

								ret = nativeJSON.decode(response);
							}
							catch(e) { }

							if(ret && ret.responseData && ret.responseData.translatedText && ret.responseData.translatedText.length)
								translation = ret.responseData.translatedText;

							// restore whitespace, and any previous chunk
							translation = prevTranslation + prespace + translation + postspace;

							if(!chunk && (translation != that.originals[index]))
							{
								translateByIndex(index, translation);
								wwlbar_.storeInCache(doc.location.href, that.originals[index], translation);
							}

							that.translateChunk(index + ((chunk == 0) ? 1 : 0), chunk, ((chunk == 0) ? "" : translation), prevLength, detectEach, (chunk == 0) ? "" : prevLanguage);
						});
					}
				}
				else that.translateChunk(index + 1, 0, "", 0, detectEach, "");
			}
		},
		100);
	}
};