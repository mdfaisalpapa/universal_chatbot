// Copyright (c) 2026, Universal Chatbot and contributors
// For license information, please see license.txt

frappe.ui.form.on("Bot Channel", {
    setup: function(frm) {
        frm.set_query("deployment", function() {
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
        // ✨ Quick Create Bot action on Bot Channel view and edit pages
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

        if (!frm.is_new() && frm.doc.deployment) {
            frm.add_custom_button(__("Open Deployment"), function() {
                frappe.set_route("Form", "Bot Deployment", frm.doc.deployment);
            });
        }

        // Auto-detect deployment if empty on edit page
        if (!frm.doc.deployment && frm.doc.chatbot && !frm.is_new()) {
            frappe.db.get_value("Bot Deployment", { channel: frm.doc.name }, "name").then(r => {
                if (r && r.message && r.message.name) {
                    frm.set_value("deployment", r.message.name);
                }
            });
        }
    },

    chatbot: function(frm) {
        if (frm.doc.chatbot && !frm.doc.deployment) {
            frappe.db.get_value("Bot Deployment", { chatbot: frm.doc.chatbot, channel: frm.doc.name }, "name").then(r => {
                if (r && r.message && r.message.name) {
                    frm.set_value("deployment", r.message.name);
                }
            });
        }
    }
});
