// Chatbot Flow form script
frappe.ui.form.on("Chatbot Flow", {
    refresh: function(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__("Visual Flow Designer"), function() {
                if (window.UniversalChatbot && window.UniversalChatbot.open_flow_designer) {
                    window.UniversalChatbot.open_flow_designer(frm.doc.name, frm);
                } else {
                    frappe.msgprint(__("Visual Flow Designer assets are not loaded yet."));
                }
            }).addClass("btn-primary");
        }
    }
});
