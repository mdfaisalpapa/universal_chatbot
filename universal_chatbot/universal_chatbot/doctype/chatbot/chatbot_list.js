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
        listview.page.add_inner_button(__("📥 Import Bot Package"), function() {
            openImportBotPackageDialog(function() {
                listview.refresh();
            });
        });

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

function openImportBotPackageDialog(onSuccess) {
    let fileContent = null;

    const d = new frappe.ui.Dialog({
        title: __("📥 Import Complete Bot Package"),
        fields: [
            {
                label: __("Bot Package JSON File"),
                fieldname: "package_file",
                fieldtype: "Attach",
                reqd: 0,
                description: __("Upload an exported .json bot package file."),
                onchange: function() {
                    const fileUrl = d.get_value("package_file");
                    if (fileUrl) {
                        fetch(fileUrl)
                            .then(res => res.text())
                            .then(text => {
                                fileContent = text;
                                d.set_value("package_json_preview", text.substring(0, 500) + (text.length > 500 ? "..." : ""));
                                try {
                                    const parsed = JSON.parse(text);
                                    if (parsed.bot && parsed.bot.bot_name && !d.get_value("target_bot_slug")) {
                                        d.set_value("target_bot_slug", parsed.bot.bot_name);
                                    }
                                } catch (e) {
                                    // ignore parse error in preview
                                }
                            })
                            .catch(err => {
                                frappe.msgprint(__("Error reading file: {0}", [err.message]));
                            });
                    }
                }
            },
            {
                label: __("Or Paste Package JSON Directly"),
                fieldname: "package_json_raw",
                fieldtype: "Code",
                options: "JSON",
                description: __("Optionally paste the complete JSON payload directly.")
            },
            {
                fieldname: "col_break_1",
                fieldtype: "Column Break"
            },
            {
                label: __("Target Bot Slug / Identifier"),
                fieldname: "target_bot_slug",
                fieldtype: "Data",
                description: __("Slug for the newly provisioned bot (e.g. resident_support). Leave blank to use bot name from package.")
            },
            {
                label: __("Overwrite Existing Bot & Channels"),
                fieldname: "overwrite",
                fieldtype: "Check",
                default: 0,
                description: __("If checked, existing bot definition, flows, and deployments with matching names will be safely updated.")
            },
            {
                label: __("Payload Preview"),
                fieldname: "package_json_preview",
                fieldtype: "Small Text",
                read_only: 1
            }
        ],
        primary_action_label: __("Import & Provision Bot"),
        primary_action: function() {
            const rawJson = d.get_value("package_json_raw");
            const finalPayload = (rawJson && rawJson.trim()) ? rawJson.trim() : fileContent;

            if (!finalPayload) {
                frappe.msgprint(__("Please attach a valid Bot Package .json file or paste JSON content."));
                return;
            }

            frappe.call({
                method: "universal_chatbot.flow.bot_export_import.import_bot_package",
                args: {
                    package_json: finalPayload,
                    target_bot_slug: d.get_value("target_bot_slug") || null,
                    overwrite: d.get_value("overwrite") ? 1 : 0
                },
                freeze: true,
                freeze_message: __("Importing bot, integrations, flows, and omnichannel deployments..."),
                callback: function(r) {
                    if (r.message && r.message.status === "success") {
                        d.hide();
                        frappe.msgprint({
                            title: __("Bot Imported Successfully"),
                            indicator: "green",
                            message: `
                                <div style="font-size:13px;">
                                    <strong>${r.message.message}</strong>
                                    <ul style="margin-top:8px; padding-left:18px;">
                                        <li>${__("Integrations")}: <strong>${r.message.integrations_count}</strong></li>
                                        <li>${__("Actions")}: <strong>${r.message.actions_count}</strong></li>
                                        <li>${__("Flows")}: <strong>${r.message.flows_count}</strong></li>
                                        <li>${__("Deployments")}: <strong>${r.message.deployments_count}</strong></li>
                                    </ul>
                                </div>
                            `
                        });
                        if (onSuccess) onSuccess();
                        frappe.set_route("Form", "Chatbot", r.message.bot_name);
                    }
                }
            });
        }
    });

    d.show();
}

