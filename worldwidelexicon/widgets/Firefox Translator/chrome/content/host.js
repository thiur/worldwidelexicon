if(!wwlbar) { var wwlbar = {}; }

wwlbar.host = {

	returnObj: null,

	load: function()
	{
		this.returnObj = window.arguments[0];

		var wm = Components.classes["@mozilla.org/appshell/window-mediator;1"].getService(Components.interfaces.nsIWindowMediator);
		var browserWindow = wm.getMostRecentWindow("navigator:browser");

		var strings = browserWindow.wwlbar.strings;

		if(strings)
		{
			document.getElementById("wwl_host").setAttribute("title", this.getTranslatedUIstringByName(strings, "wwlbar.host.title"));
			document.getElementById("wwl-label-header").value = this.getTranslatedUIstringByName(strings, "wwlbar.host.service");
			document.getElementById("wwl-label-for").value = this.getTranslatedUIstringByName(strings, "wwlbar.host.for");
			document.getElementById("wwl-radio-url").label = this.getTranslatedUIstringByName(strings, "wwlbar.host.url");
			document.getElementById("wwl-radio-pair").label = this.getTranslatedUIstringByName(strings, "wwlbar.host.pair");
			document.getElementById("wwl-label-url").value = this.getTranslatedUIstringByName(strings, "wwlbar.host.url");
			document.getElementById("wwl-label-pair").value = this.getTranslatedUIstringByName(strings, "wwlbar.host.pair");

			document.documentElement.getButton("accept").label = this.getTranslatedUIstringByName(strings, "wwlbar.userdetails.accept");
			document.documentElement.getButton("cancel").label = this.getTranslatedUIstringByName(strings, "wwlbar.cancel");
		}

		document.getElementById("wwl-host-service").value = this.returnObj.service;
		document.getElementById("wwl-type").selectedIndex = (this.returnObj.type == "pair") ? 1 : 0;

		this.radio();

		document.getElementById("wwl-host-url").value = this.returnObj.url;

		var source = document.getElementById("wwlbar-host-source-language");
		var target = document.getElementById("wwlbar-host-target-language");

		if(this.returnObj.sl.length)
		{
			for(var i = 0; i < source.itemCount; i++)
			{
				if(source.getItemAtIndex(i).value == this.returnObj.sl)
				{
					source.selectedIndex = i;
					break;
				}
			}

			for(var i = 0; i < target.itemCount; i++)
			{
				if(target.getItemAtIndex(i).value == this.returnObj.tl)
				{
					target.selectedIndex = i;
					break;
				}
			}
		}

		browserWindow.wwlbar.translateLanguageMenu(source, function()
		{
			browserWindow.wwlbar.translateLanguageMenu(target);
		});
	},

	save: function()
	{
		this.returnObj.service = document.getElementById("wwl-host-service").value;
		this.returnObj.type = (document.getElementById("wwl-type").selectedIndex == 0) ? "url" : "pair";
		this.returnObj.sl = (this.returnObj.type == "pair") ? document.getElementById("wwlbar-host-source-language").selectedItem.value : "";
		this.returnObj.tl = (this.returnObj.type == "pair") ? document.getElementById("wwlbar-host-target-language").selectedItem.value : "";
		this.returnObj.url = (this.returnObj.type != "pair") ? document.getElementById("wwl-host-url").value : "";
		this.returnObj.value = "ok";
	},

	radio: function()
	{
		var ispair = (document.getElementById("wwl-type").selectedIndex == 1);

		if(ispair)
		{
			document.getElementById("wwl-label-url").setAttribute("disabled", true);
			document.getElementById("wwl-host-url").setAttribute("disabled", true);
		}
		else
		{
			document.getElementById("wwl-label-url").removeAttribute("disabled");
			document.getElementById("wwl-host-url").removeAttribute("disabled");
		}

		document.getElementById("wwl-label-pair").setAttribute("disabled", !ispair);
		document.getElementById("wwlbar-host-source-language").setAttribute("disabled", !ispair);
		document.getElementById("wwlbar-host-target-language").setAttribute("disabled", !ispair);
		document.getElementById("wwlbar-host-arrow").setAttribute("disabled", !ispair);
	},

	getTranslatedUIstringByName: function(strings, name)
	{
		for(var i = 0; i < strings.length; i++)
			if(strings[i][0] == name)
				return strings[i][2];

		return "";
	}
}