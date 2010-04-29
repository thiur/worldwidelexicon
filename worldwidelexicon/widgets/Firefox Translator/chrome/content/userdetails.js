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

wwlbar.userdetails = {

	returnObj: null,

	onload: function()
	{
		this.returnObj = window.arguments[0];

		var strings = this.returnObj.strings;

		if(strings)
		{
			document.getElementById("wwl-userdetails-dialog").setAttribute("title", this.getTranslatedUIstringByName(strings, "wwlbar.userdetails.title"));
			document.getElementById("userdetails-header").value = this.getTranslatedUIstringByName(strings, "wwlbar.userdetails.header");
			document.getElementById("userdetails-firstname").value = this.getTranslatedUIstringByName(strings, "wwlbar.userdetails.firstname");
			document.getElementById("userdetails-lastname").value = this.getTranslatedUIstringByName(strings, "wwlbar.userdetails.lastname");
			document.getElementById("userdetails-description").value = this.getTranslatedUIstringByName(strings, "wwlbar.userdetails.description");
			document.getElementById("userdetails-www").value = this.getTranslatedUIstringByName(strings, "wwlbar.userdetails.www");
			document.getElementById("userdetails-tags").value = this.getTranslatedUIstringByName(strings, "wwlbar.userdetails.tags");
			document.getElementById("userdetails-languages").value = this.getTranslatedUIstringByName(strings, "wwlbar.userdetails.languages");

			document.documentElement.getButton("accept").label = this.getTranslatedUIstringByName(strings, "wwlbar.userdetails.accept");
			document.documentElement.getButton("cancel").label = this.getTranslatedUIstringByName(strings, "wwlbar.cancel");
		}

		var l1 = document.getElementById("userdetails-language-1");
		var l2 = document.getElementById("userdetails-language-2");
		var l3 = document.getElementById("userdetails-language-3");

		var wm = Components.classes["@mozilla.org/appshell/window-mediator;1"].getService(Components.interfaces.nsIWindowMediator);
		var browserWindow = wm.getMostRecentWindow("navigator:browser");

		browserWindow.wwlbar.translateLanguageMenu(l1, function()
		{
			browserWindow.wwlbar.translateLanguageMenu(l2, function()
			{
				browserWindow.wwlbar.translateLanguageMenu(l3);
			});
		});
	},

	accept: function()
	{
		this.returnObj.action = "userdetails";
		this.returnObj.firstname = document.getElementById("wwl-firstname").value;
		this.returnObj.lastname = document.getElementById("wwl-lastname").value;
		this.returnObj.description = document.getElementById("wwl-description").value;
		this.returnObj.skype = document.getElementById("wwl-skype").value;
		this.returnObj.facebook = document.getElementById("wwl-facebook").value;
		this.returnObj.www = document.getElementById("wwl-www").value;
		this.returnObj.tags = document.getElementById("wwl-tags").value;

		var l1 = document.getElementById("userdetails-language-1").selectedItem.label;
		var l2 = document.getElementById("userdetails-language-2").selectedItem.label;
		var l3 = document.getElementById("userdetails-language-3").selectedItem.label;

		this.returnObj.languages = l1 + "," + l2 + "," + l3;
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
	}
};