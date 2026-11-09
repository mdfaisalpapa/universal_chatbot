frappe.listview_settings["Chatbot"] = {
    button: {
        show: function(doc) {
            return true;
        },
        get_label: function() {
            return __("✏️ Edit");
        },
        get_description: function(doc) {
            return __("Edit Bot & Channels in Guided Wizard");
        },
        action: function(doc) {
            if (window.UniversalChatbot && window.UniversalChatbot.open_bot_editor) {
                window.UniversalChatbot.open_bot_editor(doc.name, function() {
                    // refresh or stay
                });
            } else {
                frappe.set_route("Form", "Chatbot", doc.name);
            }
        }
    },
    onload: function(listview) {
        listview.page.add_inner_button(__("✨ New Bot Wizard"), function() {
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
