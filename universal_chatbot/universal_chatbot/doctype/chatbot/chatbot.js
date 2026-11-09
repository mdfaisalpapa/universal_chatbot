frappe.ui.form.on("Chatbot", {
    refresh: function(frm) {
        if (!frm.is_new()) {
            // ✏️ Single, unambiguous primary action on top toolbar (no redundant buttons)
            frm.add_custom_button(__("✏️ Edit Bot & Channels"), function() {
                openBotEditor(frm);
            }).addClass("btn-primary");

            // Central Management Hub: Render both Flow & Channel dashboards inline
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
                        <button type="button" class="btn btn-primary btn-xs btn-create-flow-modal">
                            <i class="fa fa-plus"></i> ${__("+ Create New Flow")}
                        </button>
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
