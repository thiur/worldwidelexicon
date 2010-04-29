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

wwlbar.newuser = {

	returnObj: null,

	onload: function()
	{
		this.returnObj = window.arguments[0];

		var strings = this.returnObj.strings;

		if(strings)
		{
			document.getElementById("wwl-newuser-dialog").setAttribute("title", this.getTranslatedUIstringByName(strings, "wwlbar.newuser.title"));
			document.getElementById("new-header").value   = this.getTranslatedUIstringByName(strings, "wwlbar.newuser.header");
			document.getElementById("new-username").value = this.getTranslatedUIstringByName(strings, "wwlbar.login.username");
			document.getElementById("new-password").value = this.getTranslatedUIstringByName(strings, "wwlbar.login.pass");
			document.getElementById("new-email").value    = this.getTranslatedUIstringByName(strings, "wwlbar.newuser.email");
			document.getElementById("wwl-detail").label   = this.getTranslatedUIstringByName(strings, "wwlbar.newuser.detail");
			document.documentElement.getButton("extra1").label = this.getTranslatedUIstringByName(strings, "wwlbar.newuser.button");
			document.documentElement.getButton("cancel").label = this.getTranslatedUIstringByName(strings, "wwlbar.cancel");
		}
	},

	accept: function()
	{
		var user = document.getElementById("wwl-user-name").value;
		var pass = document.getElementById("wwl-pass").value;
		var mail = document.getElementById("wwl-email").value;

		if(!user.length || !pass.length || !mail.length)
		{
			alert("Please enter the non-empty username, password and e-mail.");
			return false;
		}

		if(pass.length < 8)
		{
			alert("Your password is non-secure - please type-in a longer one (8 characters or more).");
			return false;
		}

		var that = this;

		// Check if username is available:
		var wm = Components.classes["@mozilla.org/appshell/window-mediator;1"].getService(Components.interfaces.nsIWindowMediator);
		var browserWindow = wm.getMostRecentWindow("navigator:browser");
		browserWindow.wwlbar.callGetService("/users/check", 0, [["username", user]], function(response, failed)
		{
			if(response == "y")
			{
				that.returnObj.action = "newuser";
				that.returnObj.username = user;
				that.returnObj.password = pass;
				that.returnObj.email = mail;
				that.returnObj.detail = document.getElementById("wwl-detail").checked;

				window.close();
			}
			else
			{
				alert("The username you selected is already registered, please select another one.");
			}
		});
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