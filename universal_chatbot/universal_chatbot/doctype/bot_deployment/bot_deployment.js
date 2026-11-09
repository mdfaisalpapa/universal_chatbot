// Copyright (c) 2026, Universal Chatbot and contributors
// For license information, please see license.txt

frappe.ui.form.on("Bot Deployment", {
    setup: function(frm) {
        frm.set_query("channel", function() {
            if (frm.doc.chatbot) {
                return {
                    filters: {
                        chatbot: frm.doc.chatbot
                    }
                };
            }
            return {};
        });
    },

    refresh: function(frm) {
        // ✨ Quick Create Bot action on Bot Deployment view and edit pages
        frm.add_custom_button(__("✨ Quick Create Bot"), function() {
            if (window.UniversalChatbot && window.UniversalChatbot.open_bot_wizard) {
                const initial = {
                    bot_slug: frm.doc.chatbot || "",
                    is_existing: !!frm.doc.chatbot
                };
                window.UniversalChatbot.open_bot_wizard(function(res) {
                    frm.reload_doc();
                }, initial);
            } else {
                frappe.msgprint(__("Bot Wizard is loading, please try again in a moment."));
            }
        });

        if (!frm.is_new() && frm.doc.channel) {
            frm.add_custom_button(__("View Channel"), function() {
                frappe.set_route("Form", "Bot Channel", frm.doc.channel);
            });
        }
    }
});
