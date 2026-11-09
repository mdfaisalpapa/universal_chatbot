frappe.listview_settings["Bot Deployment"] = {
    onload: function(listview) {
        listview.page.add_inner_button(__("✨ Quick Create Bot"), function() {
            if (window.UniversalChatbot && window.UniversalChatbot.open_bot_wizard) {
                window.UniversalChatbot.open_bot_wizard(function(res) {
                    listview.refresh();
                });
            } else {
                frappe.msgprint(__("Bot Wizard is loading, please try again in a moment."));
            }
        }).addClass("btn-primary");
    }
};
