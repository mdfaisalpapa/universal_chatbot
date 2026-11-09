// Chatbot Flow form script (View and Edit pages)
frappe.ui.form.on("Chatbot Flow", {
    refresh: function(frm) {
        // ✨ Quick Create Bot wizard button accessible on Chatbot Flow view and edit pages
        frm.add_custom_button(__("✨ Quick Create Bot"), function() {
            if (window.UniversalChatbot && window.UniversalChatbot.open_bot_wizard) {
                const initial = {
                    bot_slug: frm.doc.bot || "",
                    is_existing: !!frm.doc.bot
                };
                window.UniversalChatbot.open_bot_wizard(function(res) {
                    frm.reload_doc();
                }, initial);
            } else {
                frappe.msgprint(__("Bot Wizard is loading, please try again in a moment."));
            }
        });

        if (!frm.is_new()) {
            frm.add_custom_button(__("🎨 Visual Flow Designer"), function() {
                if (window.UniversalChatbot && window.UniversalChatbot.open_flow_designer) {
                    window.UniversalChatbot.open_flow_designer(frm.doc.name, frm);
                } else {
                    frappe.msgprint(__("Visual Flow Designer assets are not loaded yet."));
                }
            }).addClass("btn-primary");
        }
    }
});
