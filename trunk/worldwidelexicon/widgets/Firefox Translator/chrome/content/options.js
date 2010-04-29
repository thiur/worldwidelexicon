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

wwlbar.options = {

	initialize: function()
	{
		var wm = Components.classes["@mozilla.org/appshell/window-mediator;1"].getService(Components.interfaces.nsIWindowMediator);
		var browserWindow = wm.getMostRecentWindow("navigator:browser");
		var strings = browserWindow.wwlbar.strings;

		if(strings)
		{
			document.getElementById("wwl-bilingual-check").setAttribute("label", this.getTranslatedUIstringByName(strings, "wwlbar.bilingual"));
			document.getElementById("wwl-colorize-check").setAttribute("label", this.getTranslatedUIstringByName(strings, "wwlbar.colorize"));
			document.getElementById("wwl-overflow-check").setAttribute("label", this.getTranslatedUIstringByName(strings, "wwlbar.overflow"));
			document.getElementById("wwl-machine-check").setAttribute("label", this.getTranslatedUIstringByName(strings, "wwlbar.machine"));
			document.getElementById("wwl-anonymous-check").setAttribute("label", this.getTranslatedUIstringByName(strings, "wwlbar.anonymous"));
			document.getElementById("wwl-unscored-check").setAttribute("label", this.getTranslatedUIstringByName(strings, "wwlbar.unscored"));
			document.getElementById("wwl-min-score-label").setAttribute("value", this.getTranslatedUIstringByName(strings, "wwlbar.score"));
			document.getElementById("wwl-sidebar-check").setAttribute("label", this.getTranslatedUIstringByName(strings, "wwlbar.sidebar.check"));
			document.getElementById("wwl-ui-check").setAttribute("label", this.getTranslatedUIstringByName(strings, "wwlbar.ui.check"));
			document.getElementById("wwl-login-check").setAttribute("label", this.getTranslatedUIstringByName(strings, "wwlbar.login.check"));

			document.getElementById("wwlbar_servers_menu_item1").setAttribute("label", this.getTranslatedUIstringByName(strings, "wwlbar.options.add"));
			document.getElementById("wwlbar_servers_menu_item2").setAttribute("label", this.getTranslatedUIstringByName(strings, "wwlbar.options.edit"));
			document.getElementById("wwlbar_servers_menu_item3").setAttribute("label", this.getTranslatedUIstringByName(strings, "wwlbar.options.delete"));
			document.getElementById("wwl-server-tip").setAttribute("value", this.getTranslatedUIstringByName(strings, "wwlbar.options.servertip"));

			document.documentElement.getButton("accept").label = this.getTranslatedUIstringByName(strings, "wwlbar.userdetails.accept");
			document.documentElement.getButton("cancel").label = this.getTranslatedUIstringByName(strings, "wwlbar.cancel");
		}

		// Load server data:

		const id = "wwlbar@worldwidelexicon.org";

		var path = Components.classes["@mozilla.org/extensions/manager;1"]
							.getService(Components.interfaces.nsIExtensionManager)
							.getInstallLocation(id)
							.getItemLocation(id); 

		path.append("servers.xml");

		var istream = Components.classes["@mozilla.org/network/file-input-stream;1"].createInstance(Components.interfaces.nsIFileInputStream);
		istream.init(path, 0x01, 0444, 0);
		istream.QueryInterface(Components.interfaces.nsILineInputStream);

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

		var dom = (new DOMParser()).parseFromString(xml, "text/xml");
		var entries = dom.documentElement.childNodes;
		var el = entries.length;

		var list = document.getElementById("wwl_servers");

		for(var j = 0; j < el; j++)
		{
			var entry = entries[j];

			var item = document.createElement('listitem');
			var cell1 = document.createElement('listcell');
			var cell2 = document.createElement('listcell');

			item.setAttribute('id', "wwlbar_item_" + j);
			cell1.setAttribute('id', "wwlbar_cell_1_" + j);
			cell2.setAttribute('id', "wwlbar_cell_2_" + j);

			cell1.setAttribute('label', entry.getAttribute("service"));
			cell2.setAttribute('label', (entry.getAttribute("type") == "pair") ? "Language pair" : "URL");

			item.setAttribute('wwl_type', entry.getAttribute("type"));
			item.setAttribute('wwl_sl',   entry.getAttribute("sl"));
			item.setAttribute('wwl_tl',   entry.getAttribute("tl"));
			item.setAttribute('wwl_url',  entry.getAttribute("url"));

			item.appendChild(cell1);
			item.appendChild(cell2);
			list.appendChild(item);
		}
	},

	getTranslatedUIstringByName: function(strings, name)
	{
		for(var i = 0; i < strings.length; i++)
			if(strings[i][0] == name)
				return strings[i][2];

		return "";
	},

	servers_check: function(event)
	{
		var id = event.explicitOriginalTarget.id;

		if((id.indexOf("wwlbar_item_") != -1) || (id.indexOf("wwlbar_cell_") != -1))
		{
			document.getElementById("wwlbar_servers_menu_item2").setAttribute("disabled", false);
			document.getElementById("wwlbar_servers_menu_item3").setAttribute("disabled", false);
		}
		else
		{
			document.getElementById("wwlbar_servers_menu_item2").setAttribute("disabled", true);
			document.getElementById("wwlbar_servers_menu_item3").setAttribute("disabled", true);
		}
	},

	servers_menu_add: function(event)
	{
		var returnObj = {value: "", service: "", type: "", sl: "", tl: "", url: ""};
		window.openDialog('chrome://wwlbar/content/host.xul', 'WWLNewHost', 'centerscreen=yes,chrome=yes,modal=yes', returnObj);

		if(returnObj && (returnObj.value == "ok"))
		{
			var list = document.getElementById("wwl_servers");

			var item = document.createElement('listitem');
			var cell1 = document.createElement('listcell');
			var cell2 = document.createElement('listcell');

			item.setAttribute('id', "wwlbar_item_" + list.childNodes.length);
			cell1.setAttribute('id', "wwlbar_cell_1_" + list.childNodes.length);
			cell2.setAttribute('id', "wwlbar_cell_2_" + list.childNodes.length);

			cell1.setAttribute('label', returnObj.service);
			cell2.setAttribute('label', (returnObj.type == "pair") ? "Language pair" : "URL");

			item.setAttribute('wwl_type', returnObj.type);
			item.setAttribute('wwl_sl',   returnObj.sl);
			item.setAttribute('wwl_tl',   returnObj.tl);
			item.setAttribute('wwl_url',  returnObj.url);

			item.appendChild(cell1);
			item.appendChild(cell2);
			list.appendChild(item);

			list.ensureElementIsVisible(item);
		}
	},

	servers_menu_edit: function(event)
	{
		var list = document.getElementById("wwl_servers");
		var index = list.selectedIndex;
		var item = list.getItemAtIndex(index);
		var cell1 = item.firstChild;
		var cell2 = item.childNodes[1];

		var returnObj = {value: "", service: cell1.getAttribute("label"), type: item.getAttribute("wwl_type"), sl: item.getAttribute("wwl_sl"), tl: item.getAttribute("wwl_tl"), url: item.getAttribute("wwl_url")};
		window.openDialog('chrome://wwlbar/content/host.xul', 'WWLNewHost', 'centerscreen=yes,chrome=yes,modal=yes', returnObj);

		if(returnObj && (returnObj.value == "ok"))
		{
			cell1.setAttribute('label', returnObj.service);
			cell2.setAttribute('label', (returnObj.type == "pair") ? "Language pair" : "URL");

			item.setAttribute('wwl_type', returnObj.type);
			item.setAttribute('wwl_sl',   returnObj.sl);
			item.setAttribute('wwl_tl',   returnObj.tl);
			item.setAttribute('wwl_url',  returnObj.url);
		}
	},

	servers_menu_delete: function(event)
	{
		var list = document.getElementById("wwl_servers");
		if(list.childNodes.length <= 1) return;

		var index = list.selectedIndex;
		var next = (index == -1) ? 0 : index;

		list.removeChild(list.childNodes[index + 1]);
	},

	finish: function()
	{
		const id = "wwlbar@worldwidelexicon.org";

		var path = Components.classes["@mozilla.org/extensions/manager;1"]
							.getService(Components.interfaces.nsIExtensionManager)
							.getInstallLocation(id)
							.getItemLocation(id); 

		path.append("servers.xml");

		var list = document.getElementById("wwl_servers");

		var str = "<?xml version=\"1.0\" ?><list>";

		for(var i = 1; i < list.childNodes.length; i++)
		{
			var item = list.childNodes[i];
			str += "<entry service=\"" + item.firstChild.getAttribute("label") + "\" type=\"" + item.getAttribute("wwl_type") + "\" sl=\"" + item.getAttribute("wwl_sl") + "\" tl=\"" + item.getAttribute("wwl_tl") + "\" url=\"" + item.getAttribute("wwl_url") + "\" />";
		}

		str += "</list>";

		var fostream = Components.classes["@mozilla.org/network/file-output-stream;1"].createInstance(Components.interfaces.nsIFileOutputStream);

		try
		{
			fostream.init(path, 0x02 | 0x08 | 0x20, 0664, 0);
			fostream.write(str, str.length);
			fostream.close();
		}
		catch(e) { }

		var wm = Components.classes["@mozilla.org/appshell/window-mediator;1"].getService(Components.interfaces.nsIWindowMediator);

		// reference to the main browser window:
		var browserWindow = wm.getMostRecentWindow("navigator:browser");

		browserWindow.wwlbar.reloadServers();
	}
};