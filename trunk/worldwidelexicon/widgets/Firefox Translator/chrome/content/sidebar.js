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

wwlbar.sidebar = {

	initialize: function()
	{
		var frame = document.getElementById("wwl-stats-frame");
		frame.style.height = frame.parentNode.scrollHeight + "px";

		var wm = Components.classes["@mozilla.org/appshell/window-mediator;1"].getService(Components.interfaces.nsIWindowMediator);
		var browserWindow = wm.getMostRecentWindow("navigator:browser");
		browserWindow.document.getElementById("sidebar-title").value = browserWindow.wwlbar.getTranslatedUIstringByName("wwlbar.sidebar.title");
	},

	update: function(server, sl, tl, url, v)
	{
		var wm = Components.classes["@mozilla.org/appshell/window-mediator;1"].getService(Components.interfaces.nsIWindowMediator);
		var browserWindow = wm.getMostRecentWindow("navigator:browser");
		browserWindow.document.getElementById("sidebar-title").value = browserWindow.wwlbar.getTranslatedUIstringByName("wwlbar.sidebar.title");

		var frame = document.getElementById("wwl-stats-frame");

		if(!url || (url.indexOf("about:") == 0))
		{
			frame.contentDocument.location = "about:blank";
			return;
		}

		frame.contentDocument.body.innerHTML = "Loading...";
		frame.contentDocument.location = "http://" + server + "/sidebar?sl=" + sl + "&tl=" + tl + "&url=" + url + "&v=" + v;
	}
};