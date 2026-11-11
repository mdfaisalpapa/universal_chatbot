frappe.ui.form.on("Chatbot", {
    refresh: function(frm) {
        if (!frm.is_new()) {
            // Central Management Hub: Render in logical user journey order:
            // 1. Integrations -> 2. Conversation Flows -> 3. Omnichannel Deployments
            renderIntegrationManagement(frm);
            renderFlowManagement(frm);
            renderChannelManagement(frm);
        } else {
            // New bot: Offer Guided Setup Wizard
            frm.add_custom_button(__("✨ Guided Bot Setup"), function() {
                if (window.UniversalChatbot && window.UniversalChatbot.open_bot_wizard) {
                    window.UniversalChatbot.open_bot_wizard(function(res) {
                        if (res && res.bot_slug) {
                            frappe.set_route("Form", "Chatbot", res.bot_slug);
                        }
                    });
                }
            }).addClass("btn-primary");
        }
    }
});

function openBotEditor(frm) {
    if (!frm) frm = window.cur_frm;
    const doc = frm ? frm.doc : null;
    const botSlug = doc ? (doc.bot_name || doc.name) : "";
    if (window.UniversalChatbot && window.UniversalChatbot.open_bot_editor) {
        window.UniversalChatbot.open_bot_editor(doc || botSlug, function() {
            if (frm && frm.reload_doc) {
                frm.reload_doc();
            } else {
                renderFlowManagement(frm);
                renderChannelManagement(frm);
                renderIntegrationManagement(frm);
            }
        });
    } else {
        frappe.msgprint(__("Bot Editor is loading, please try again in a moment."));
    }
}

/**
 * =========================================================================
 * 1. FLOW MANAGEMENT DASHBOARD (Central Flow Hub)
 * =========================================================================
 */
function renderFlowManagement(frm) {
    if (!frm || !frm.doc || !frm.doc.name) return;
    const botSlug = frm.doc.name;

    const $wrapper = (frm.fields_dict.flow_management_html && frm.fields_dict.flow_management_html.$wrapper) || null;
    if (!$wrapper) return;

    frappe.call({
        method: "universal_chatbot.api.v1.wizard.get_bot_flows",
        args: { bot_slug: botSlug },
        callback: function(r) {
            const flows = r.message || [];
            let rowsHtml = "";

            if (flows.length === 0) {
                rowsHtml = `
                    <tr>
                        <td colspan="6" style="text-align:center; padding: 28px 12px; color: #64748b;">
                            <div style="font-size: 24px; margin-bottom: 6px;">🎨</div>
                            <div style="font-size: 13px; font-weight: 600; color: #334155;">${__("No conversation flows found")}</div>
                            <div style="font-size: 12px; color: #94a3b8; margin-top: 2px;">Create your first flow to design custom logic with the visual node canvas.</div>
                            <button type="button" class="btn btn-primary btn-xs btn-create-flow-modal" style="margin-top: 10px;">
                                <i class="fa fa-plus"></i> ${__("+ Create Starter Flow")}
                            </button>
                        </td>
                    </tr>
                `;
            } else {
                flows.forEach(function(f) {
                    const statusBadge = f.status === "Published"
                        ? `<span class="badge badge-success" style="font-size:10px;">${__("Published")}</span>`
                        : (f.status === "Archived"
                            ? `<span class="badge badge-light" style="font-size:10px;">${__("Archived")}</span>`
                            : `<span class="badge badge-warning" style="font-size:10px;">${__("Draft")}</span>`);

                    const primaryBadge = f.is_primary
                        ? `<span class="badge badge-primary" style="font-size:10px; margin-left:6px;"><i class="fa fa-star text-warning"></i> ${__("Primary Flow")}</span>`
                        : "";

                    rowsHtml += `
                        <tr style="border-bottom: 1px solid #f1f5f9;">
                            <td style="vertical-align: middle; padding: 12px 10px;">
                                <div style="font-weight: 600; font-size: 13px; color: #1e293b;">
                                    ${escapeHtml(f.title || f.flow_name)}
                                    ${primaryBadge}
                                </div>
                                <div style="font-size: 11px; color: #64748b; font-family: monospace; margin-top: 2px;">
                                    ${escapeHtml(f.name)}
                                </div>
                                ${f.description ? `<div style="font-size: 11px; color: #475569; margin-top: 2px;">${escapeHtml(f.description)}</div>` : ''}
                            </td>
                            <td style="vertical-align: middle; padding: 12px 10px;">
                                ${statusBadge}
                            </td>
                            <td style="vertical-align: middle; padding: 12px 10px; font-size: 12px; color: #475569;">
                                <code>v${escapeHtml(f.version)}</code>
                            </td>
                            <td style="vertical-align: middle; padding: 12px 10px; font-size: 12px; color: #475569;">
                                <span class="badge badge-light" style="border: 1px solid #cbd5e1; font-weight: 500;">
                                    ${f.node_count} ${f.node_count === 1 ? __("node") : __("nodes")}
                                </span>
                            </td>
                            <td style="vertical-align: middle; padding: 12px 10px; font-size: 11px; color: #64748b;">
                                ${escapeHtml(f.modified)}
                            </td>
                            <td style="vertical-align: middle; padding: 12px 10px; text-align: right; white-space: nowrap;">
                                <button type="button" class="btn btn-primary btn-xs btn-open-flow-canvas" data-flow="${escapeHtml(f.name)}" title="${__("Open Visual Flow Canvas")}" style="margin-right:4px;">
                                    <i class="fa fa-paint-brush"></i> ${__("🎨 Open Designer")}
                                </button>
                                <button type="button" class="btn btn-default btn-xs btn-export-flow-action" data-flow="${escapeHtml(f.name)}" title="${__("Export Flow JSON")}" style="margin-right:4px;">
                                    <i class="fa fa-download"></i> ${__("Export")}
                                </button>
                                <button type="button" class="btn btn-default btn-xs btn-edit-flow-props" data-flow="${escapeHtml(f.name)}" title="${__("Edit Flow Properties")}" style="margin-right:4px;">
                                    <i class="fa fa-pencil"></i> ${__("Properties")}
                                </button>
                                <button type="button" class="btn btn-default btn-xs text-danger btn-delete-flow-record" data-flow="${escapeHtml(f.name)}" title="${__("Delete Flow")}">
                                    <i class="fa fa-trash"></i>
                                </button>
                            </td>
                        </tr>
                    `;
                });
            }

            const containerHtml = `
                <div class="flow-management-dashboard" style="background:#fff; border:1px solid #e2e8f0; border-radius:8px; padding:16px; margin-bottom:16px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; border-bottom:1px solid #f1f5f9; padding-bottom:10px;">
                        <div>
                            <span style="font-weight:700; font-size:15px; color:#1e293b;">💬 Conversation Flows & Visual Logic</span>
                            <span style="font-size:12px; color:#64748b; margin-left:8px;">Manage branching paths and launch the Visual Flow Designer</span>
                        </div>
                        <div style="display:flex; gap:6px;">
                            <button type="button" class="btn btn-default btn-xs btn-import-flow-modal">
                                <i class="fa fa-upload"></i> ${__("Import Flow")}
                            </button>
                            <button type="button" class="btn btn-primary btn-xs btn-create-flow-modal">
                                <i class="fa fa-plus"></i> ${__("+ Create New Flow")}
                            </button>
                        </div>
                    </div>

                    <div class="table-responsive" style="margin: 0;">
                        <table class="table table-hover" style="margin-bottom:0; font-size:12px;">
                            <thead>
                                <tr style="background:#f8fafc; color:#475569; border-bottom:1px solid #e2e8f0;">
                                    <th style="font-weight:600; width:35%;">${__("Flow Name / ID")}</th>
                                    <th style="font-weight:600; width:12%;">${__("Status")}</th>
                                    <th style="font-weight:600; width:10%;">${__("Version")}</th>
                                    <th style="font-weight:600; width:10%;">${__("Canvas Nodes")}</th>
                                    <th style="font-weight:600; width:15%;">${__("Last Modified")}</th>
                                    <th style="font-weight:600; text-align:right; width:18%;">${__("Actions")}</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${rowsHtml}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;

            $wrapper.html(containerHtml);

            // Wire "+ Create New Flow"
            $wrapper.find(".btn-create-flow-modal").off("click").on("click", function() {
                openCreateFlowDialog(frm);
            });

            // Wire "Import Flow"
            $wrapper.find(".btn-import-flow-modal").off("click").on("click", function() {
                openImportFlowDialog(frm);
            });

            // Wire "Export Flow"
            $wrapper.find(".btn-export-flow-action").off("click").on("click", function() {
                const flowName = $(this).data("flow");
                frappe.call({
                    method: "universal_chatbot.flow.export_import.export_flow_json",
                    args: { flow_name: flowName },
                    freeze: true,
                    freeze_message: __("Exporting Flow..."),
                    callback: function(r) {
                        if (r.message) {
                            const jsonStr = JSON.stringify(r.message, null, 2);
                            const blob = new Blob([jsonStr], { type: "application/json" });
                            const url = URL.createObjectURL(blob);
                            const a = document.createElement("a");
                            a.href = url;
                            a.download = `${flowName}_export.json`;
                            document.body.appendChild(a);
                            a.click();
                            document.body.removeChild(a);
                            URL.revokeObjectURL(url);
                            frappe.show_alert({ message: __("Flow exported successfully"), indicator: "green" });
                        }
                    }
                });
            });

            // Wire "🎨 Open Flow Designer"
            $wrapper.find(".btn-open-flow-canvas").off("click").on("click", function() {
                const flowName = $(this).data("flow");
                if (window.UniversalChatbot && window.UniversalChatbot.open_flow_designer) {
                    window.UniversalChatbot.open_flow_designer(flowName, frm);
                } else {
                    frappe.set_route("Form", "Chatbot Flow", flowName);
                }
            });

            // Wire "Edit Properties"
            $wrapper.find(".btn-edit-flow-props").off("click").on("click", function() {
                const flowName = $(this).data("flow");
                const flowObj = flows.find(f => f.name === flowName) || { name: flowName };
                openEditFlowPropertiesDialog(frm, flowObj);
            });

            // Wire "Delete"
            $wrapper.find(".btn-delete-flow-record").off("click").on("click", function() {
                const flowName = $(this).data("flow");
                frappe.confirm(
                    __("Are you sure you want to permanently delete flow <strong>{0}</strong>? All canvas nodes in this flow will be removed.", [flowName]),
                    function() {
                        frappe.call({
                            method: "universal_chatbot.api.v1.wizard.delete_chatbot_flow",
                            args: { flow_name: flowName },
                            freeze: true,
                            freeze_message: __("Deleting flow..."),
                            callback: function(res) {
                                if (res.message && res.message.status === "success") {
                                    frappe.show_alert({ message: res.message.message, indicator: "green" });
                                    // Refresh dashboard without page reload
                                    renderFlowManagement(frm);
                                    if (frm.doc.primary_flow === flowName) {
                                        frm.doc.primary_flow = "";
                                        frm.refresh_field("primary_flow");
                                    }
                                }
                            }
                        });
                    }
                );
            });
        }
    });
}

function openImportFlowDialog(frm) {
    const botSlug = frm.doc.name;
    const d = new frappe.ui.Dialog({
        title: __("📥 Import Conversation Flow JSON"),
        fields: [
            {
                fieldname: "flow_file",
                fieldtype: "Attach",
                label: __("Upload Flow JSON File"),
                description: __("Select an exported .json conversation flow schema.")
            },
            {
                fieldname: "flow_json_text",
                fieldtype: "Code",
                label: __("Or Paste Flow JSON"),
                options: "JSON"
            },
            {
                fieldname: "overwrite",
                fieldtype: "Check",
                label: __("Overwrite Existing Flow Nodes & Variables"),
                default: 1
            }
        ],
        primary_action_label: __("Import Flow"),
        primary_action: function(vals) {
            const applyImport = function(content) {
                if (!content || !content.trim()) {
                    frappe.msgprint(__("Please upload a file or paste JSON content."));
                    return;
                }
                frappe.call({
                    method: "universal_chatbot.flow.export_import.import_flow_json",
                    args: {
                        flow_json: content,
                        bot_slug: botSlug,
                        overwrite: vals.overwrite ? 1 : 0
                    },
                    freeze: true,
                    freeze_message: __("Importing flow..."),
                    callback: function(res) {
                        if (res.message && res.message.status === "success") {
                            d.hide();
                            frappe.show_alert({ message: res.message.message, indicator: "green" });
                            renderFlowManagement(frm);
                        }
                    }
                });
            };

            if (vals.flow_file) {
                fetch(vals.flow_file)
                    .then(response => response.text())
                    .then(text => applyImport(text))
                    .catch(err => {
                        frappe.msgprint(__("Failed to read file: {0}", [err.message]));
                    });
            } else {
                applyImport(vals.flow_json_text);
            }
        }
    });
    d.show();
}

function openCreateFlowDialog(frm) {
    const d = new frappe.ui.Dialog({
        title: __("✨ Create New Conversation Flow"),
        fields: [
            {
                fieldtype: "Data",
                fieldname: "flow_title",
                label: __("Flow Title / Label"),
                reqd: 1,
                placeholder: __("e.g. Apartment Maintenance Inquiry")
            },
            {
                fieldtype: "Data",
                fieldname: "flow_name",
                label: __("Flow Slug / ID"),
                description: __("Alphanumeric identifier (auto-generated if left empty)."),
                placeholder: __("e.g. maintenance_inquiry")
            },
            {
                fieldtype: "Small Text",
                fieldname: "description",
                label: __("Description"),
                placeholder: __("Brief summary of this conversation logic branch...")
            },
            {
                fieldtype: "Check",
                fieldname: "set_as_primary",
                label: __("⭐ Set as Primary Flow for this Chatbot"),
                default: 0
            }
        ],
        primary_action_label: __("Create Flow & Open Canvas"),
        primary_action: function() {
            const values = d.get_values();
            if (!values) return;

            const title = (values.flow_title || "").trim();
            let slug = (values.flow_name || "").trim();
            if (!slug) {
                slug = title.toLowerCase().replace(/[^a-z0-9_]+/g, "_").replace(/^_+|_+$/g, "");
            }

            frappe.call({
                method: "universal_chatbot.api.v1.wizard.create_chatbot_flow",
                args: {
                    bot_slug: frm.doc.name,
                    flow_name: slug,
                    title: title,
                    description: values.description || "",
                    set_as_primary: values.set_as_primary ? 1 : 0
                },
                freeze: true,
                freeze_message: __("Scaffolding new flow canvas..."),
                callback: function(r) {
                    if (r.message && r.message.status === "success") {
                        d.hide();
                        frappe.show_alert({
                            message: __("✓ Flow '{0}' created successfully!", [r.message.flow_name]),
                            indicator: "green"
                        });

                        if (values.set_as_primary) {
                            frm.doc.primary_flow = r.message.flow_name;
                            frm.refresh_field("primary_flow");
                        }

                        // Re-render dashboard automatically
                        renderFlowManagement(frm);

                        // Launch Visual Flow Designer immediately
                        if (window.UniversalChatbot && window.UniversalChatbot.open_flow_designer) {
                            window.UniversalChatbot.open_flow_designer(r.message.flow_name, frm);
                        } else {
                            frappe.set_route("Form", "Chatbot Flow", r.message.flow_name);
                        }
                    }
                }
            });
        },
        secondary_action_label: __("Cancel"),
        secondary_action: function() {
            d.hide();
        }
    });

    // Auto-slugify
    if (d.fields_dict.flow_title && d.fields_dict.flow_title.$input) {
        d.fields_dict.flow_title.$input.on("input", function() {
            const val = $(this).val() || "";
            const s = val.toLowerCase().replace(/[^a-z0-9_]+/g, "_").replace(/^_+|_+$/g, "");
            d.set_value("flow_name", s);
        });
    }

    d.show();
}

function openEditFlowPropertiesDialog(frm, flow) {
    const d = new frappe.ui.Dialog({
        title: __("✏️ Edit Flow: {0}", [flow.flow_name]),
        fields: [
            {
                fieldtype: "Data",
                fieldname: "flow_name_display",
                label: __("Flow ID"),
                default: flow.name,
                read_only: 1
            },
            {
                fieldtype: "Select",
                fieldname: "status",
                label: __("Status"),
                options: ["Draft", "Published", "Archived"],
                default: flow.status || "Draft",
                reqd: 1
            },
            {
                fieldtype: "Data",
                fieldname: "version",
                label: __("Version"),
                default: flow.version || "1.0.0"
            },
            {
                fieldtype: "Small Text",
                fieldname: "description",
                label: __("Description"),
                default: flow.description || ""
            },
            {
                fieldtype: "Check",
                fieldname: "set_as_primary",
                label: __("⭐ Primary Flow for this Chatbot"),
                default: flow.is_primary ? 1 : 0
            }
        ],
        primary_action_label: __("Save Properties"),
        primary_action: function() {
            const values = d.get_values();
            if (!values) return;

            frappe.call({
                method: "universal_chatbot.api.v1.wizard.update_chatbot_flow_properties",
                args: {
                    flow_name: flow.name,
                    description: values.description || "",
                    status: values.status,
                    version: values.version,
                    set_as_primary: values.set_as_primary ? 1 : 0
                },
                freeze: true,
                freeze_message: __("Updating flow properties..."),
                callback: function(r) {
                    if (r.message && r.message.status === "success") {
                        d.hide();
                        frappe.show_alert({
                            message: __("✓ Flow properties updated!"),
                            indicator: "green"
                        });

                        if (values.set_as_primary) {
                            frm.doc.primary_flow = flow.name;
                        } else if (frm.doc.primary_flow === flow.name) {
                            frm.doc.primary_flow = "";
                        }
                        frm.refresh_field("primary_flow");

                        renderFlowManagement(frm);
                    }
                }
            });
        },
        secondary_action_label: __("Cancel"),
        secondary_action: function() {
            d.hide();
        }
    });

    d.show();
}

/**
 * =========================================================================
 * 2. CHANNEL & DEPLOYMENT MANAGEMENT DASHBOARD (Central Channel Hub)
 * =========================================================================
 */
function renderChannelManagement(frm) {
    if (!frm || !frm.doc || !frm.doc.name) return;
    const botSlug = frm.doc.name;

    const $wrapper = (frm.fields_dict.channel_management_html && frm.fields_dict.channel_management_html.$wrapper)
        || (frm.fields_dict.omnichannel_hub_html && frm.fields_dict.omnichannel_hub_html.$wrapper)
        || null;

    if (!$wrapper) return;

    frappe.call({
        method: "universal_chatbot.api.v1.wizard.get_bot_config",
        args: { bot_slug: botSlug },
        callback: function(r) {
            if (!r.message) return;
            const cfg = r.message;
            const ch = cfg.channels || {};
            const wa = ch.whatsapp || {};
            const tg = ch.telegram || {};
            const web = ch.web_widget || ch.web || {};

            const waDep = (cfg.deployments || []).find(d => d.channel_type === "WhatsApp");
            const tgDep = (cfg.deployments || []).find(d => d.channel_type === "Telegram");
            const webDep = (cfg.deployments || []).find(d => d.channel_type === "Web Widget");

            const hasWeb = !!web.name;
            const hasWa = !!wa.name;
            const hasTg = !!tg.name;

            const html = `
                <div class="channel-management-dashboard" style="background:#fff; border:1px solid #e2e8f0; border-radius:8px; padding:16px; margin-bottom:16px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; border-bottom:1px solid #f1f5f9; padding-bottom:10px;">
                        <div>
                            <span style="font-weight:700; font-size:15px; color:#1e293b;">🌐 Omnichannel Deployments & Channels</span>
                            <span style="font-size:12px; color:#64748b; margin-left:8px;">Live webhook connections, tokens, and embed keys</span>
                        </div>
                        <button type="button" class="btn btn-default btn-xs btn-add-channel-modal">
                            <i class="fa fa-plug text-primary"></i> ${__("+ Add / Configure Connection")}
                        </button>
                    </div>

                    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:12px;">
                        <!-- Web Widget Card -->
                        <div style="border:1px solid ${hasWeb && web.is_enabled ? '#bbf7d0' : '#e2e8f0'}; background:${hasWeb && web.is_enabled ? '#f0fdf4' : '#fafafa'}; border-radius:6px; padding:12px; position:relative;">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                                <div style="display:flex; align-items:center; gap:6px;">
                                    <strong style="font-size:13px; color:#1e293b;">🌐 Web Chat Widget</strong>
                                </div>
                                <div style="display:flex; align-items:center; gap:6px;">
                                    <span class="badge ${hasWeb && web.is_enabled ? 'badge-success' : 'badge-light'}" style="font-size:10px;">
                                        ${hasWeb ? (web.is_enabled ? __('Active') : __('Disabled')) : __('Not Connected')}
                                    </span>
                                    ${hasWeb ? `
                                        <button type="button" class="btn btn-link btn-xs text-danger btn-delete-channel" data-channel="${escapeHtml(web.name)}" title="${__("Delete Web Channel")}" style="padding:0; margin-left:4px; font-size:12px;">
                                            <i class="fa fa-times-circle"></i>
                                        </button>
                                    ` : ''}
                                </div>
                            </div>
                            <div style="font-size:11px; color:#475569; margin-bottom:8px;">
                                Allowed: <code>${webDep ? (webDep.allowed_domains || '*') : '*'}</code>
                            </div>
                            ${hasWeb && webDep && webDep.embed_script ? `
                                <button type="button" class="btn btn-default btn-xs btn-copy-text" data-text="${escapeHtml(webDep.embed_script)}" style="width:100%; font-size:11px;">
                                    <i class="fa fa-code"></i> ${__("Copy Embed Script")}
                                </button>
                            ` : `
                                <button type="button" class="btn btn-default btn-xs btn-add-channel-modal" style="width:100%; font-size:11px;">
                                    <i class="fa fa-plus"></i> ${__("Connect Web Widget")}
                                </button>
                            `}
                        </div>

                        <!-- WhatsApp Card -->
                        <div style="border:1px solid ${hasWa && wa.is_enabled ? '#bbf7d0' : '#e2e8f0'}; background:${hasWa && wa.is_enabled ? '#f0fdf4' : '#fafafa'}; border-radius:6px; padding:12px; position:relative;">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                                <div style="display:flex; align-items:center; gap:6px;">
                                    <strong style="font-size:13px; color:#1e293b;">📱 WhatsApp (Meta API)</strong>
                                </div>
                                <div style="display:flex; align-items:center; gap:6px;">
                                    <span class="badge ${hasWa && wa.is_enabled ? 'badge-success' : 'badge-light'}" style="font-size:10px;">
                                        ${hasWa ? (wa.is_enabled ? __('Active') : __('Disabled')) : __('Not Connected')}
                                    </span>
                                    ${hasWa ? `
                                        <button type="button" class="btn btn-link btn-xs text-danger btn-delete-channel" data-channel="${escapeHtml(wa.name)}" title="${__("Delete WhatsApp Channel")}" style="padding:0; margin-left:4px; font-size:12px;">
                                            <i class="fa fa-times-circle"></i>
                                        </button>
                                    ` : ''}
                                </div>
                            </div>
                            <div style="font-size:11px; color:#475569; margin-bottom:8px;">
                                Phone ID: <code>${wa.whatsapp_phone_number_id || 'Not configured'}</code>
                            </div>
                            ${hasWa && waDep && waDep.webhook_url ? `
                                <button type="button" class="btn btn-default btn-xs btn-copy-text" data-text="${escapeHtml(waDep.webhook_url)}" style="width:100%; font-size:11px;">
                                    <i class="fa fa-link"></i> ${__("Copy Webhook URL")}
                                </button>
                            ` : `
                                <button type="button" class="btn btn-default btn-xs btn-add-channel-modal" style="width:100%; font-size:11px;">
                                    <i class="fa fa-plus"></i> ${__("Connect WhatsApp")}
                                </button>
                            `}
                        </div>

                        <!-- Telegram Card -->
                        <div style="border:1px solid ${hasTg && tg.is_enabled ? '#bbf7d0' : '#e2e8f0'}; background:${hasTg && tg.is_enabled ? '#f0fdf4' : '#fafafa'}; border-radius:6px; padding:12px; position:relative;">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                                <div style="display:flex; align-items:center; gap:6px;">
                                    <strong style="font-size:13px; color:#1e293b;">✈️ Telegram Bot</strong>
                                </div>
                                <div style="display:flex; align-items:center; gap:6px;">
                                    <span class="badge ${hasTg && tg.is_enabled ? 'badge-success' : 'badge-light'}" style="font-size:10px;">
                                        ${hasTg ? (tg.is_enabled ? __('Active') : __('Disabled')) : __('Not Connected')}
                                    </span>
                                    ${hasTg ? `
                                        <button type="button" class="btn btn-link btn-xs text-danger btn-delete-channel" data-channel="${escapeHtml(tg.name)}" title="${__("Delete Telegram Channel")}" style="padding:0; margin-left:4px; font-size:12px;">
                                            <i class="fa fa-times-circle"></i>
                                        </button>
                                    ` : ''}
                                </div>
                            </div>
                            <div style="font-size:11px; color:#475569; margin-bottom:8px;">
                                Token: <code>${tg.telegram_bot_token ? '••••••••' : 'Not configured'}</code>
                            </div>
                            ${hasTg && tgDep && tgDep.webhook_url ? `
                                <button type="button" class="btn btn-default btn-xs btn-copy-text" data-text="${escapeHtml(tgDep.webhook_url)}" style="width:100%; font-size:11px;">
                                    <i class="fa fa-link"></i> ${__("Copy Webhook URL")}
                                </button>
                            ` : `
                                <button type="button" class="btn btn-default btn-xs btn-add-channel-modal" style="width:100%; font-size:11px;">
                                    <i class="fa fa-plus"></i> ${__("Connect Telegram")}
                                </button>
                            `}
                        </div>
                    </div>
                </div>
            `;

            $wrapper.html(html);

            // Wire copy buttons
            $wrapper.find(".btn-copy-text").off("click").on("click", function() {
                const text = $(this).data("text");
                navigator.clipboard.writeText(text);
                frappe.show_alert({ message: __("Copied to clipboard!"), indicator: "green" });
            });

            // Wire "+ Add Connection" / "Connect Channel"
            $wrapper.find(".btn-add-channel-modal").off("click").on("click", function() {
                if (window.UniversalChatbot && window.UniversalChatbot.open_channel_wizard) {
                    window.UniversalChatbot.open_channel_wizard(frm.doc, function() {
                        renderChannelManagement(frm);
                    });
                } else {
                    openBotEditor(frm);
                }
            });

            // Wire "Delete Channel"
            $wrapper.find(".btn-delete-channel").off("click").on("click", function() {
                const channelName = $(this).data("channel");
                frappe.confirm(
                    __("Are you sure you want to disconnect and delete channel <strong>{0}</strong>? Its active deployment and webhook URL will be deleted.", [channelName]),
                    function() {
                        frappe.call({
                            method: "universal_chatbot.api.v1.wizard.delete_bot_channel",
                            args: { channel_name: channelName },
                            freeze: true,
                            freeze_message: __("Deleting channel deployment..."),
                            callback: function(res) {
                                if (res.message && res.message.status === "success") {
                                    frappe.show_alert({ message: res.message.message, indicator: "green" });
                                    renderChannelManagement(frm);
                                }
                            }
                        });
                    }
                );
            });
        }
    });
}

function escapeHtml(text) {
    return (text || "").toString().replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

/**
 * =========================================================================
 * 3. INTEGRATION MANAGEMENT DASHBOARD (Central REST & Action Hub)
 * =========================================================================
 */
function renderIntegrationManagement(frm) {
    if (!frm || !frm.doc || !frm.doc.name) return;
    const botSlug = frm.doc.name;

    const $wrapper = (frm.fields_dict.integration_management_html && frm.fields_dict.integration_management_html.$wrapper) || null;
    if (!$wrapper) return;

    frappe.call({
        method: "universal_chatbot.api.v1.wizard.get_bot_integrations",
        args: { bot_slug: botSlug },
        callback: function(r) {
            const integrations = r.message || [];
            let cardsHtml = "";

            if (integrations.length === 0) {
                cardsHtml = `
                    <div style="grid-column: 1 / -1; text-align:center; padding: 28px 12px; color: #64748b; background:#f8fafc; border: 1px dashed #cbd5e1; border-radius:6px;">
                        <div style="font-size: 24px; margin-bottom: 6px;">🔌</div>
                        <div style="font-size: 13px; font-weight: 600; color: #334155;">${__("No REST Integrations Configured")}</div>
                        <div style="font-size: 12px; color: #94a3b8; margin-top: 2px;">Connect external ERPNext instances or third-party APIs to enable dynamic database lookups.</div>
                        <button type="button" class="btn btn-primary btn-xs btn-add-integration-modal" style="margin-top: 10px;">
                            <i class="fa fa-plus"></i> ${__("+ Configure New Integration")}
                        </button>
                    </div>
                `;
            } else {
                integrations.forEach(function(integ) {
                    const statusBadge = integ.status === "Active"
                        ? `<span class="badge badge-success" style="font-size:10px;">${__("Active")}</span>`
                        : `<span class="badge badge-warning" style="font-size:10px;">${escapeHtml(integ.status)}</span>`;

                    const botUsageBadge = integ.is_used_by_bot
                        ? `<span class="badge badge-primary" style="font-size:10px; margin-left:6px;"><i class="fa fa-link"></i> ${__("Used in Flows")}</span>`
                        : `<span class="badge badge-light" style="font-size:10px; margin-left:6px; color:#64748b;">${__("Available")}</span>`;

                    let actionsPills = "";
                    if (integ.actions && integ.actions.length > 0) {
                        actionsPills = integ.actions.map(function(act) {
                            return `
                                <span class="badge ${act.is_used ? 'badge-info' : 'badge-light'}" style="font-size:10px; font-family:monospace; margin-right:4px; margin-bottom:4px; display:inline-block;" title="${escapeHtml(act.operation)}">
                                    ⚡ ${escapeHtml(act.action_name)} ${act.is_used ? '★' : ''}
                                </span>
                            `;
                        }).join("");
                    } else {
                        actionsPills = `<span style="font-size:11px; color:#94a3b8; font-style:italic;">${__("No actions defined")}</span>`;
                    }

                    cardsHtml += `
                        <div class="integration-card" style="border:1px solid ${integ.is_used_by_bot ? '#bfdbfe' : '#e2e8f0'}; background:${integ.is_used_by_bot ? '#f8fafc' : '#fff'}; border-radius:8px; padding:16px; margin-bottom:12px; box-shadow: 0 1px 2px 0 rgba(0,0,0,0.05);">
                            <!-- Header / Summary Row -->
                            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px;">
                                <div>
                                    <div style="display:flex; align-items:center; gap:6px;">
                                        <strong style="font-size:14px; color:#0f172a;">⚡ ${escapeHtml(integ.integration_name)}</strong>
                                        ${botUsageBadge}
                                        ${statusBadge}
                                    </div>
                                    <div style="font-size:12px; color:#64748b; font-family:monospace; margin-top:3px;">
                                        <span class="badge badge-light" style="border:1px solid #cbd5e1; font-weight:500;">${escapeHtml(integ.integration_type)}</span>
                                        <span style="margin-left:6px;">${escapeHtml(integ.base_url)}</span>
                                    </div>
                                </div>
                                <div style="display:flex; align-items:center; gap:6px;">
                                    <button type="button" class="btn btn-default btn-xs btn-toggle-integ-details" data-target="#integ-details-${escapeHtml(integ.name)}" style="font-size:11px;">
                                        <i class="fa fa-chevron-down"></i> ${__("Actions & Endpoints")} (${integ.actions_count})
                                    </button>
                                    <button type="button" class="btn btn-default btn-xs btn-edit-integration" data-integration="${escapeHtml(integ.name)}" title="${__("Edit Integration Configuration")}" style="font-size:11px;">
                                        <i class="fa fa-pencil text-primary"></i> ${__("Edit")}
                                    </button>
                                    <button type="button" class="btn btn-default btn-xs text-danger btn-delete-integration" data-integration="${escapeHtml(integ.name)}" title="${__("Delete Integration")}" style="font-size:11px;">
                                        <i class="fa fa-trash"></i>
                                    </button>
                                </div>
                            </div>

                            <!-- Meta details row -->
                            <div style="font-size:11px; color:#475569; display:flex; align-items:center; gap:16px; background:#f1f5f9; padding:6px 10px; border-radius:4px; margin-bottom:10px;">
                                <span><strong>Auth Type:</strong> <code>${escapeHtml(integ.auth_type)}</code></span>
                                <span><strong>API Key / User:</strong> <code>${integ.api_key_masked || 'None'}</code></span>
                                <span><strong>Credentials:</strong> ${integ.has_credentials ? '<span class="text-success"><i class="fa fa-check-circle"></i> Configured</span>' : '<span class="text-muted">None</span>'}</span>
                                <span><strong>Timeout:</strong> ${integ.timeout}s</span>
                            </div>

                            <!-- Collapsible Actions & Endpoints Panel -->
                            <div id="integ-details-${escapeHtml(integ.name)}" class="integ-actions-collapse" style="border-top:1px dashed #cbd5e1; padding-top:10px; margin-top:8px;">
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                                    <span style="font-size:12px; font-weight:600; color:#334155;">
                                        <i class="fa fa-cogs text-primary" style="margin-right:4px;"></i> ${__("Configured Actions & Endpoints")}
                                    </span>
                                    <div style="display:flex; gap:6px;">
                                        <button type="button" class="btn btn-default btn-xs btn-discover-actions-modal" data-integration="${escapeHtml(integ.name)}" data-type="${escapeHtml(integ.integration_type)}" style="font-size:11px;">
                                            <i class="fa fa-magic text-info"></i> ${__("🔍 Auto-Discover Actions")}
                                        </button>
                                        <button type="button" class="btn btn-default btn-xs btn-add-action-modal" data-integration="${escapeHtml(integ.name)}" style="font-size:11px;">
                                            <i class="fa fa-plus text-primary"></i> ${__("+ Add Action / Endpoint")}
                                        </button>
                                    </div>
                                </div>

                                <div class="table-responsive" style="margin: 0; background:#fff; border:1px solid #e2e8f0; border-radius:4px;">
                                    <table class="table table-sm table-hover" style="margin-bottom:0; font-size:11px;">
                                        <thead>
                                            <tr style="background:#f8fafc; color:#475569;">
                                                <th style="width:25%; font-weight:600;">${__("Action Name")}</th>
                                                <th style="width:10%; font-weight:600;">${__("Method")}</th>
                                                <th style="width:28%; font-weight:600;">${__("Operation / API Method")}</th>
                                                <th style="width:12%; font-weight:600;">${__("Used in Flows")}</th>
                                                <th style="width:25%; text-align:right; font-weight:600;">${__("Actions")}</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            ${integ.actions && integ.actions.length > 0 ? integ.actions.map(function(act) {
                                                const methodColor = act.method === 'GET' ? 'badge-success' : (act.method === 'POST' ? 'badge-primary' : (act.method === 'DELETE' ? 'badge-danger' : 'badge-warning'));
                                                let inSchemaObj = {};
                                                let outMapObj = {};
                                                try {
                                                    inSchemaObj = typeof act.input_schema === 'string' ? JSON.parse(act.input_schema || "{}") : (act.input_schema || {});
                                                } catch(e) {}
                                                try {
                                                    outMapObj = typeof act.output_mapping === 'string' ? JSON.parse(act.output_mapping || "{}") : (act.output_mapping || {});
                                                } catch(e) {}

                                                const paramList = (inSchemaObj && inSchemaObj.properties) ? Object.keys(inSchemaObj.properties) : [];
                                                const outList = Object.keys(outMapObj || {});

                                                return `
                                                    <tr>
                                                        <td style="vertical-align:middle; font-weight:600; font-family:monospace; color:#1e293b;">
                                                            <div>⚡ ${escapeHtml(act.action_name)}</div>
                                                            ${paramList.length > 0 ? `
                                                                <div style="font-size:10px; color:#64748b; font-weight:normal; margin-top:3px;">
                                                                    <span class="text-muted">Params:</span> <code>${paramList.map(p => escapeHtml(p)).join(', ')}</code>
                                                                </div>
                                                            ` : ''}
                                                            ${outList.length > 0 ? `
                                                                <div style="font-size:10px; color:#15803d; font-weight:normal; margin-top:2px;">
                                                                    <span class="text-muted">Returns:</span> <code>${outList.slice(0, 4).map(o => escapeHtml(o)).join(', ')}${outList.length > 4 ? '...' : ''}</code>
                                                                </div>
                                                            ` : ''}
                                                        </td>
                                                        <td style="vertical-align:middle;">
                                                            <span class="badge ${methodColor}" style="font-size:9px; font-family:monospace;">${escapeHtml(act.method || 'POST')}</span>
                                                        </td>
                                                        <td style="vertical-align:middle; font-family:monospace; color:#475569;">
                                                            <code>${escapeHtml(act.operation)}</code>
                                                        </td>
                                                        <td style="vertical-align:middle;">
                                                            ${act.is_used ? '<span class="badge badge-primary" style="font-size:9px;"><i class="fa fa-check"></i> Yes</span>' : '<span class="badge badge-light" style="font-size:9px; color:#94a3b8;">No</span>'}
                                                        </td>
                                                        <td style="vertical-align:middle; text-align:right; white-space:nowrap;">
                                                            <button type="button" class="btn btn-default btn-xs btn-test-single-action" data-integration="${escapeHtml(integ.name)}" data-action-name="${escapeHtml(act.action_name)}" title="${__("Test Dry Run on this Action")}" style="margin-right:3px;">
                                                                <i class="fa fa-play text-success"></i> ${__("Test")}
                                                            </button>
                                                            <button type="button" class="btn btn-default btn-xs btn-edit-single-action" data-integration="${escapeHtml(integ.name)}" data-action="${escapeHtml(act.name)}" title="${__("Edit Action & Schema")}" style="margin-right:3px;">
                                                                <i class="fa fa-pencil text-primary"></i> ${__("Edit")}
                                                            </button>
                                                            <button type="button" class="btn btn-default btn-xs text-danger btn-delete-single-action" data-action="${escapeHtml(act.name)}" data-action-name="${escapeHtml(act.action_name)}" title="${__("Delete Action")}">
                                                                <i class="fa fa-trash"></i>
                                                            </button>
                                                        </td>
                                                    </tr>
                                                `;
                                            }).join("") : `
                                                <tr>
                                                    <td colspan="5" style="text-align:center; padding:12px; color:#94a3b8;">
                                                        ${__("No actions configured for this integration yet. Click '+ Add Action' or '🔍 Auto-Discover Actions' above.")}
                                                    </td>
                                                </tr>
                                            `}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    `;
                });
            }

            const html = `
                <div class="integration-management-dashboard" style="background:#fff; border:1px solid #e2e8f0; border-radius:8px; padding:16px; margin-bottom:16px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; border-bottom:1px solid #f1f5f9; padding-bottom:10px;">
                        <div>
                            <span style="font-weight:700; font-size:15px; color:#1e293b;">⚡ REST Integrations & External Actions</span>
                            <span style="font-size:12px; color:#64748b; margin-left:8px;">ERPNext, custom API connectors, credentials, and actions</span>
                        </div>
                        <button type="button" class="btn btn-default btn-xs btn-add-integration-modal">
                            <i class="fa fa-plus text-primary"></i> ${__("+ New REST Integration")}
                        </button>
                    </div>

                    <div style="display:flex; flex-direction:column; gap:12px;">
                        ${cardsHtml}
                    </div>
                </div>
            `;

            $wrapper.html(html);

            // Wire collapsible toggles
            $wrapper.find(".btn-toggle-integ-details").off("click").on("click", function() {
                const target = $(this).data("target");
                const $targetEl = $wrapper.find(target);
                $targetEl.slideToggle(200);
                const $icon = $(this).find("i");
                if ($icon.hasClass("fa-chevron-down")) {
                    $icon.removeClass("fa-chevron-down").addClass("fa-chevron-up");
                } else {
                    $icon.removeClass("fa-chevron-up").addClass("fa-chevron-down");
                }
            });

            // Wire "+ New REST Integration"
            $wrapper.find(".btn-add-integration-modal").off("click").on("click", function() {
                openIntegrationDialog(frm);
            });

            // Wire "Edit Config" modal dialog (in-place modal, no redirect!)
            $wrapper.find(".btn-edit-integration").off("click").on("click", function() {
                const iname = $(this).data("integration");
                const integObj = integrations.find(i => i.name === iname);
                openIntegrationDialog(frm, integObj);
            });

            // Wire "🔍 Auto-Discover Actions"
            $wrapper.find(".btn-discover-actions-modal").off("click").on("click", function() {
                const iname = $(this).data("integration");
                const integType = $(this).data("type");
                const integObj = integrations.find(i => i.name === iname);
                openDiscoverActionsDialog(frm, iname, integType, integObj);
            });

            // Wire "+ Add Action / Endpoint"
            $wrapper.find(".btn-add-action-modal").off("click").on("click", function() {
                const iname = $(this).data("integration");
                openSingleActionDialog(frm, iname);
            });

            // Wire "Edit Action & Schema"
            $wrapper.find(".btn-edit-single-action").off("click").on("click", function() {
                const iname = $(this).data("integration");
                const aname = $(this).data("action");
                const integObj = integrations.find(i => i.name === iname);
                const actObj = (integObj && integObj.actions) ? integObj.actions.find(a => a.name === aname) : null;
                openSingleActionDialog(frm, iname, actObj);
            });

            // Wire "Delete Action"
            $wrapper.find(".btn-delete-single-action").off("click").on("click", function() {
                const fullActionName = $(this).data("action");
                const actionLabel = $(this).data("action-name") || fullActionName;
                frappe.confirm(
                    __("Are you sure you want to delete action <strong>{0}</strong>?", [actionLabel]),
                    function() {
                        frappe.call({
                            method: "universal_chatbot.api.v1.wizard.delete_integration_action",
                            args: { action_name: fullActionName },
                            freeze: true,
                            freeze_message: __("Deleting action..."),
                            callback: function(res) {
                                if (res.message && res.message.status === "success") {
                                    frappe.show_alert({ message: res.message.message, indicator: "green" });
                                    renderIntegrationManagement(frm);
                                }
                            }
                        });
                    }
                );
            });

            // Wire "Test Action" (per-action test dry run)
            $wrapper.find(".btn-test-single-action").off("click").on("click", function() {
                const iname = $(this).data("integration");
                const aname = $(this).data("action-name");
                const integObj = integrations.find(i => i.name === iname);
                openTestActionDialog(frm, integObj, aname);
            });

            // Wire "Delete Integration"
            $wrapper.find(".btn-delete-integration").off("click").on("click", function() {
                const iname = $(this).data("integration");
                frappe.confirm(
                    __("Are you sure you want to delete integration <strong>{0}</strong>? All linked credentials and actions will be permanently removed.", [iname]),
                    function() {
                        frappe.call({
                            method: "universal_chatbot.api.v1.wizard.delete_chatbot_integration",
                            args: { integration_name: iname },
                            freeze: true,
                            freeze_message: __("Deleting integration..."),
                            callback: function(res) {
                                if (res.message && res.message.status === "success") {
                                    frappe.show_alert({ message: res.message.message, indicator: "green" });
                                    renderIntegrationManagement(frm);
                                }
                            }
                        });
                    }
                );
            });
        }
    });
}

function openIntegrationDialog(frm, existingData) {
    const isEdit = !!existingData;
    const d = new frappe.ui.Dialog({
        title: isEdit ? __("✏️ Edit REST Integration: {0}", [existingData.integration_name]) : __("⚡ Configure New REST Integration"),
        fields: [
            {
                fieldname: "integration_name",
                fieldtype: "Data",
                label: __("Integration Name / Identifier"),
                reqd: 1,
                read_only: isEdit ? 1 : 0,
                default: existingData ? existingData.integration_name : "",
                placeholder: __("e.g. society_erp_connector")
            },
            {
                fieldname: "integration_type",
                fieldtype: "Select",
                label: __("Integration Type"),
                options: "Frappe REST\nGeneric REST",
                default: existingData ? existingData.integration_type : "Frappe REST",
                reqd: 1
            },
            {
                fieldname: "base_url",
                fieldtype: "Data",
                label: __("Target Server Base URL"),
                reqd: 1,
                default: existingData ? existingData.base_url : "http://kvc3.local:8000",
                placeholder: __("e.g. https://erp.mycompany.com:8000")
            },
            {
                fieldname: "status",
                fieldtype: "Select",
                label: __("Status"),
                options: "Active\nInactive\nTesting",
                default: existingData ? existingData.status : "Active"
            },
            {
                fieldname: "timeout",
                fieldtype: "Int",
                label: __("Timeout (Seconds)"),
                default: existingData ? (existingData.timeout || 15) : 15
            },
            {
                fieldtype: "Section Break",
                label: __("Authentication & Security")
            },
            {
                fieldname: "auth_type",
                fieldtype: "Select",
                label: __("Authentication Type"),
                options: "Token\nBearer\nBasic\nNone",
                default: existingData ? existingData.auth_type : "Token"
            },
            {
                fieldname: "api_key",
                fieldtype: "Data",
                label: __("API Key / Username"),
                default: existingData ? (existingData.api_key_masked ? existingData.api_key : "") : "",
                placeholder: __("e.g. 6ca76ae1fbfc2fc")
            },
            {
                fieldname: "api_secret",
                fieldtype: "Password",
                label: __("API Secret / Token"),
                placeholder: isEdit ? __("Leave blank to keep existing secret") : __("Enter token secret")
            }
        ],
        primary_action_label: isEdit ? __("Save Integration Changes") : __("Create Integration"),
        primary_action: function(vals) {
            frappe.call({
                method: "universal_chatbot.api.v1.wizard.save_chatbot_integration",
                args: {
                    integration_name: vals.integration_name,
                    integration_type: vals.integration_type,
                    base_url: vals.base_url,
                    status: vals.status,
                    timeout: vals.timeout || 15,
                    auth_type: vals.auth_type,
                    api_key: vals.api_key,
                    api_secret: vals.api_secret
                },
                freeze: true,
                freeze_message: __("Saving Integration..."),
                callback: function(res) {
                    if (res.message && res.message.status === "success") {
                        d.hide();
                        frappe.show_alert({ message: res.message.message, indicator: "green" });
                        renderIntegrationManagement(frm);
                    }
                }
            });
        }
    });
    d.show();
}

function openSingleActionDialog(frm, integrationName, existingAction) {
    const isEdit = !!existingAction;
    const d = new frappe.ui.Dialog({
        title: isEdit ? __("✏️ Edit Action: {0}", [existingAction.action_name]) : __("⚡ Add Action / Endpoint to {0}", [integrationName]),
        fields: [
            {
                fieldname: "action_name",
                fieldtype: "Data",
                label: __("Action Name (Called by Flow)"),
                reqd: 1,
                read_only: isEdit ? 1 : 0,
                default: existingAction ? existingAction.action_name : "",
                placeholder: __("e.g. get_maintenance_dues")
            },
            {
                fieldname: "method",
                fieldtype: "Select",
                label: __("HTTP Method"),
                options: "GET\nPOST\nPUT\nDELETE\nPATCH",
                default: existingAction ? (existingAction.method || "POST") : "POST",
                reqd: 1
            },
            {
                fieldname: "operation",
                fieldtype: "Data",
                label: __("Endpoint / API Method"),
                reqd: 1,
                default: existingAction ? existingAction.operation : "/api/method/",
                placeholder: __("e.g. /api/method/society_erp.api.get_maintenance_dues")
            },
            {
                fieldtype: "Section Break",
                label: __("Payload Schema & Variable Mapping")
            },
            {
                fieldname: "input_schema",
                fieldtype: "Code",
                label: __("Input Schema (JSON)"),
                options: "JSON",
                default: existingAction ? (typeof existingAction.input_schema === 'string' ? existingAction.input_schema : JSON.stringify(existingAction.input_schema, null, 2)) : '{\n  "type": "object",\n  "required": ["flat_number"],\n  "properties": {\n    "flat_number": {"type": "string"}\n  }\n}'
            },
            {
                fieldname: "output_mapping",
                fieldtype: "Code",
                label: __("Output Mapping (JSON)"),
                options: "JSON",
                default: existingAction ? (typeof existingAction.output_mapping === 'string' ? existingAction.output_mapping : JSON.stringify(existingAction.output_mapping, null, 2)) : '{\n  "owner_name": "owner_name",\n  "flat_details": "flat_details",\n  "outstanding_amount": "outstanding_amount"\n}'
            }
        ],
        primary_action_label: isEdit ? __("Update Action") : __("Add Action"),
        primary_action: function(vals) {
            frappe.call({
                method: "universal_chatbot.api.v1.wizard.save_integration_action",
                args: {
                    integration: integrationName,
                    action_name: vals.action_name,
                    method: vals.method || "POST",
                    operation: vals.operation,
                    input_schema: vals.input_schema,
                    output_mapping: vals.output_mapping
                },
                freeze: true,
                freeze_message: __("Saving Action..."),
                callback: function(res) {
                    if (res.message && res.message.status === "success") {
                        d.hide();
                        frappe.show_alert({ message: res.message.message, indicator: "green" });
                        renderIntegrationManagement(frm);
                    }
                }
            });
        }
    });
    d.show();
}

function openTestActionDialog(frm, integObj, defaultActionName) {
    if (!integObj || !integObj.actions || integObj.actions.length === 0) {
        frappe.msgprint(__("This integration has no registered actions to test. Add an action first."));
        return;
    }

    const actionOptions = integObj.actions.map(a => a.action_name).join("\n");
    const chosenAction = defaultActionName || integObj.actions[0].action_name;
    const d = new frappe.ui.Dialog({
        title: __("🧪 Test Dry Run: {0} ({1})", [chosenAction, integObj.integration_name]),
        fields: [
            {
                fieldname: "action_name",
                fieldtype: "Select",
                label: __("Action Name"),
                options: actionOptions,
                default: chosenAction,
                reqd: 1
            },
            {
                fieldname: "sample_parameters",
                fieldtype: "Code",
                label: __("Test Parameters (JSON)"),
                options: "JSON",
                default: JSON.stringify({ flat_number: "TB2-203" }, null, 2)
            },
            {
                fieldtype: "Section Break",
                label: __("Execution Output")
            },
            {
                fieldname: "result_output",
                fieldtype: "Code",
                label: __("Live API Response"),
                options: "JSON",
                read_only: 1
            }
        ],
        primary_action_label: __("Execute Dry Run"),
        primary_action: function(vals) {
            let params = {};
            try {
                params = vals.sample_parameters ? JSON.parse(vals.sample_parameters) : {};
            } catch (e) {
                frappe.msgprint(__("Invalid JSON parameters: {0}", [e.message]));
                return;
            }

            frappe.call({
                method: "universal_chatbot.api.v1.flow_designer.test_integration_action",
                args: {
                    action_name: vals.action_name,
                    sample_parameters: JSON.stringify(params)
                },
                freeze: true,
                freeze_message: __("Executing test call..."),
                callback: function(res) {
                    if (res.message && res.message.status === "success") {
                        d.set_value("result_output", JSON.stringify(res.message.result, null, 2));
                        frappe.show_alert({ message: __("Action executed successfully!"), indicator: "green" });
                    } else {
                        d.set_value("result_output", JSON.stringify(res.message || {}, null, 2));
                        frappe.msgprint({
                            title: __("Execution Failed"),
                            indicator: "red",
                            message: res.message ? res.message.message : __("Error executing action")
                        });
                    }
                }
            });
        }
    });
    d.show();
}

/**
 * =========================================================================
 * 4. AUTO-DISCOVERY & SCHEMA INTROSPECTION DIALOG
 * =========================================================================
 */
function openDiscoverActionsDialog(frm, integrationName, integrationType, integObj) {
    const isFrappe = (integrationType || "").indexOf("Frappe") !== -1;
    let discoveredCandidates = [];

    const d = new frappe.ui.Dialog({
        title: __("🔍 Auto-Discover API Actions: {0}", [integrationName]),
        fields: [
            {
                fieldname: "source_type",
                fieldtype: "Select",
                label: __("Introspection Source"),
                options: "Frappe RPC / Python Module\nFrappe DocType\nOpenAPI / Swagger Spec",
                default: isFrappe ? "Frappe RPC / Python Module" : "OpenAPI / Swagger Spec",
                reqd: 1,
                change: function() {
                    const st = d.get_value("source_type");
                    if (st === "Frappe RPC / Python Module") {
                        d.set_df_property("identifier_or_url", "label", __("Python Module Path (with whitelisted API methods)"));
                        d.set_df_property("identifier_or_url", "placeholder", __("e.g. society_erp.api"));
                        d.set_df_property("identifier_or_url", "description", __("Scans the module for @frappe.whitelist() methods and extracts parameter schemas."));
                        d.set_value("identifier_or_url", "society_erp.api");
                    } else if (st === "Frappe DocType") {
                        d.set_df_property("identifier_or_url", "label", __("DocType Name"));
                        d.set_df_property("identifier_or_url", "placeholder", __("e.g. Customer, Sales Order, Item, Flat Maintenance"));
                        d.set_df_property("identifier_or_url", "description", __("Enter the DocType name on the remote Frappe/ERPNext instance to introspect."));
                        d.set_value("identifier_or_url", "Customer");
                    } else {
                        d.set_df_property("identifier_or_url", "label", __("OpenAPI / Swagger Spec URL or Path"));
                        d.set_df_property("identifier_or_url", "placeholder", __("e.g. /openapi.json or https://api.example.com/v1/swagger.json"));
                        d.set_df_property("identifier_or_url", "description", __("Relative path from base URL or full absolute URL to OpenAPI/Swagger JSON."));
                        d.set_value("identifier_or_url", "/openapi.json");
                    }
                }
            },
            {
                fieldname: "identifier_or_url",
                fieldtype: "Data",
                label: isFrappe ? __("Python Module Path (with whitelisted API methods)") : __("OpenAPI / Swagger Spec URL or Path"),
                placeholder: isFrappe ? __("e.g. society_erp.api") : __("e.g. /openapi.json"),
                description: isFrappe ? __("Scans the module for @frappe.whitelist() methods and extracts parameter schemas.") : __("Relative or full URL to OpenAPI JSON."),
                default: isFrappe ? "society_erp.api" : "/openapi.json",
                reqd: 1
            },
            {
                fieldtype: "Button",
                label: __("⚡ Introspect & Fetch Actions"),
                click: function() {
                    const st = d.get_value("source_type");
                    const ident = (d.get_value("identifier_or_url") || "").trim();
                    if (!ident) {
                        frappe.msgprint(__("Please enter a target Module, DocType, or OpenAPI URL."));
                        return;
                    }

                    let srcKey = "frappe";
                    if (st === "Frappe RPC / Python Module") {
                        srcKey = "rpc";
                    } else if (st === "OpenAPI / Swagger Spec") {
                        srcKey = "openapi";
                    }
                    frappe.call({
                        method: "universal_chatbot.api.v1.wizard.discover_remote_actions",
                        args: {
                            integration_name: integrationName,
                            source_type: srcKey,
                            identifier_or_url: ident
                        },
                        freeze: true,
                        freeze_message: __("Introspecting remote schema..."),
                        callback: function(res) {
                            if (res.message && res.message.status === "success") {
                                discoveredCandidates = res.message.candidates || [];
                                renderCandidatesTable(discoveredCandidates);
                            } else {
                                frappe.msgprint({
                                    title: __("Discovery Failed"),
                                    indicator: "red",
                                    message: res.message ? res.message.message : __("Unable to introspect actions.")
                                });
                            }
                        }
                    });
                }
            },
            {
                fieldtype: "Section Break",
                label: __("Discovered Action Candidates")
            },
            {
                fieldname: "candidates_html",
                fieldtype: "HTML"
            }
        ],
        primary_action_label: __("Import Selected Actions"),
        primary_action: function() {
            const selectedActions = [];
            const $wrapper = d.fields_dict.candidates_html.$wrapper;
            $wrapper.find("input.chk-select-candidate:checked").each(function() {
                const idx = parseInt($(this).data("index"), 10);
                if (discoveredCandidates[idx]) {
                    selectedActions.push(discoveredCandidates[idx]);
                }
            });

            if (selectedActions.length === 0) {
                frappe.msgprint(__("Please select at least one discovered action to import."));
                return;
            }

            frappe.call({
                method: "universal_chatbot.api.v1.wizard.import_discovered_actions",
                args: {
                    integration_name: integrationName,
                    actions: JSON.stringify(selectedActions)
                },
                freeze: true,
                freeze_message: __("Importing actions..."),
                callback: function(res) {
                    if (res.message && res.message.status === "success") {
                        d.hide();
                        frappe.show_alert({ message: res.message.message, indicator: "green" });
                        renderIntegrationManagement(frm);
                    }
                }
            });
        }
    });

    function renderCandidatesTable(candidates) {
        const $wrapper = d.fields_dict.candidates_html.$wrapper;
        if (!candidates || candidates.length === 0) {
            $wrapper.html(`
                <div style="padding:16px; text-align:center; color:#94a3b8; font-size:12px; background:#f8fafc; border:1px dashed #cbd5e1; border-radius:6px;">
                    ${__("No actions discovered. Check the identifier or ensure credentials have read access.")}
                </div>
            `);
            return;
        }

        let rowsHtml = candidates.map(function(c, idx) {
            const methodColor = c.method === 'GET' ? 'badge-success' : (c.method === 'POST' ? 'badge-primary' : (c.method === 'DELETE' ? 'badge-danger' : 'badge-warning'));
            const reqList = (c.input_schema && c.input_schema.required) ? c.input_schema.required : [];
            const propList = (c.input_schema && c.input_schema.properties) ? Object.keys(c.input_schema.properties) : [];
            const outKeys = c.output_mapping ? Object.keys(c.output_mapping) : [];

            return `
                <tr style="border-bottom:1px solid #f1f5f9;">
                    <td style="vertical-align:middle; text-align:center; width:30px;">
                        <input type="checkbox" class="chk-select-candidate" data-index="${idx}" checked style="cursor:pointer;" />
                    </td>
                    <td style="vertical-align:middle;">
                        <span class="badge ${methodColor}" style="font-size:9px; font-family:monospace;">${escapeHtml(c.method)}</span>
                    </td>
                    <td style="vertical-align:middle;">
                        <strong style="font-size:12px; font-family:monospace; color:#1e293b;">⚡ ${escapeHtml(c.action_name)}</strong>
                        <div style="font-size:11px; color:#64748b; font-family:monospace; margin-top:2px;">
                            ${escapeHtml(c.operation)}
                        </div>
                        ${c.description ? `<div style="font-size:10px; color:#475569; margin-top:2px;">${escapeHtml(c.description)}</div>` : ''}
                    </td>
                    <td style="vertical-align:middle; font-size:11px; color:#475569;">
                        <div>
                            <span class="text-muted"><i class="fa fa-arrow-right"></i> Params:</span> 
                            ${propList.length > 0 ? propList.map(p => `<code>${escapeHtml(p)}${reqList.includes(p) ? '*' : ''}</code>`).join(', ') : '<span class="text-muted">None</span>'}
                        </div>
                        <div style="margin-top:2px;">
                            <span class="text-muted"><i class="fa fa-arrow-left"></i> Returns:</span> 
                            ${outKeys.length > 0 ? outKeys.slice(0, 4).map(o => `<code style="color:#15803d;">${escapeHtml(o)}</code>`).join(', ') + (outKeys.length > 4 ? ` <span class="badge badge-light">+${outKeys.length - 4}</span>` : '') : '<span class="text-muted">None</span>'}
                        </div>
                    </td>
                </tr>
            `;
        }).join("");

        const html = `
            <div style="margin-top:4px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; font-size:12px;">
                    <span style="color:#1e293b; font-weight:600;">
                        ${__("Found {0} action candidate(s)", [candidates.length])}
                    </span>
                    <button type="button" class="btn btn-default btn-xs btn-toggle-all-candidates" style="font-size:10px;">
                        ${__("Toggle All")}
                    </button>
                </div>
                <div class="table-responsive" style="max-height: 280px; overflow-y: auto; border: 1px solid #e2e8f0; border-radius: 4px;">
                    <table class="table table-sm table-hover" style="margin-bottom:0; font-size:11px;">
                        <thead style="background:#f8fafc; color:#475569; position:sticky; top:0; z-index:1;">
                            <tr>
                                <th style="width:30px; text-align:center;"></th>
                                <th style="width:65px;">${__("Method")}</th>
                                <th>${__("Action & Endpoint")}</th>
                                <th style="width:160px;">${__("Schema Details")}</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${rowsHtml}
                        </tbody>
                    </table>
                </div>
            </div>
        `;

        $wrapper.html(html);

        $wrapper.find(".btn-toggle-all-candidates").off("click").on("click", function() {
            const $chks = $wrapper.find("input.chk-select-candidate");
            const allChecked = $chks.filter(":checked").length === $chks.length;
            $chks.prop("checked", !allChecked);
        });
    }

    d.show();
}
