/**
 * Universal Chatbot - Guided Bot Creation & Management Wizard
 * Unified, interactive interface for creating, viewing, and editing chatbots,
 * starter templates, and omnichannel configurations (Web, WhatsApp, Telegram).
 */

window.UniversalChatbot = window.UniversalChatbot || {};

(function() {
    "use strict";

    /**
     * Unified dialog supporting both 'create' and 'edit' modes.
     * In edit mode, accepts opts.doc (frm.doc) or opts.bot_slug.
     */
    UniversalChatbot.open_bot_dialog = function(opts) {
        opts = opts || {};
        const isEdit = opts.mode === "edit";

        // Resolve doc and slug robustly
        let doc = opts.doc || null;
        let botSlug = (opts.bot_slug || "").trim();

        if (doc && typeof doc === "object") {
            if (doc.doc) doc = doc.doc; // frm wrapper
            if (!botSlug) {
                botSlug = (doc.bot_name || doc.name || doc.docname || "").trim();
            }
        }

        if (!botSlug && window.cur_frm && window.cur_frm.doc) {
            if (!doc) doc = window.cur_frm.doc;
            botSlug = (doc.bot_name || doc.name || "").trim();
        }

        const onSuccess = opts.onSuccess;
        const initialData = opts.initialData || {};

        const startStep = opts.startStep || 1;
        let currentStep = startStep;
        let loadedConfig = null;

        const step1_fields = [
            "step_1_section",
            "bot_title",
            "bot_slug",
            "starter_template",
            "template_preview_html"
        ];

        const step2_fields = [
            "step_2_section",
            "enable_web",
            "web_domains",
            "wa_section",
            "enable_whatsapp",
            "wa_phone_number_id",
            "wa_verify_token",
            "wa_access_token",
            "tg_section",
            "enable_telegram",
            "tg_bot_token"
        ];

        // Resolve fallback values for step 1
        const initialTitle = (doc && (doc.title || doc.bot_name)) || initialData.bot_title || botSlug || "";
        const initialSlug = (doc && (doc.bot_name || doc.name)) || initialData.bot_slug || botSlug || "";

        let initialTemplate = "ERP & API Lookup";
        if (doc && doc.primary_flow) {
            const pf = (doc.primary_flow || "").toLowerCase();
            if (pf.includes("faq")) initialTemplate = "FAQ & Support";
            else if (pf.includes("blank")) initialTemplate = "Blank Canvas";
            else initialTemplate = "ERP & API Lookup";
        } else if (initialData.starter_template) {
            initialTemplate = initialData.starter_template;
        }

        function handleSecondaryAction() {
            if (currentStep === 2 && startStep === 1) {
                goToStep(1);
            } else {
                dialog.hide();
            }
        }

        const dialog = new frappe.ui.Dialog({
            title: isEdit
                ? (initialTitle ? __("✏️ Edit Chatbot: {0}", [initialTitle]) : __("✏️ Edit Chatbot & Channels"))
                : __("✨ Quick Create Chatbot (Guided Setup)"),
            size: "large",
            fields: [
                // ==========================================
                // STEP 1: IDENTITY & STARTER TEMPLATE
                // ==========================================
                {
                    fieldtype: "Section Break",
                    fieldname: "step_1_section",
                    label: isEdit ? __("1. Bot Identity & Flow") : __("1. Identity & Starter Template")
                },
                {
                    fieldtype: "Data",
                    fieldname: "bot_title",
                    label: __("Bot Title"),
                    reqd: 1,
                    default: initialTitle,
                    placeholder: __("e.g. Apartment Maintenance Assistant")
                },
                {
                    fieldtype: "Data",
                    fieldname: "bot_slug",
                    label: __("Bot Slug / ID"),
                    default: initialSlug,
                    description: isEdit
                        ? __("System identifier for this chatbot (read-only in edit mode).")
                        : __("Unique system ID (auto-generated from title if left blank)."),
                    placeholder: __("e.g. apartment_maintenance_bot"),
                    read_only: isEdit ? 1 : 0
                },
                {
                    fieldtype: "Select",
                    fieldname: "starter_template",
                    label: isEdit ? __("Starter Flow Template / Architecture") : __("Starter Template"),
                    options: [
                        "ERP & API Lookup",
                        "FAQ & Support",
                        "Blank Canvas"
                    ],
                    default: initialTemplate,
                    reqd: 1
                },
                {
                    fieldtype: "HTML",
                    fieldname: "template_preview_html"
                },

                // ==========================================
                // STEP 2: OMNICHANNEL CONFIGURATION
                // ==========================================
                {
                    fieldtype: "Section Break",
                    fieldname: "step_2_section",
                    label: __("2. Omnichannel Configuration & Deployments")
                },
                {
                    fieldtype: "Check",
                    fieldname: "enable_web",
                    label: __("🌐 Web Chat Widget (Embed on Website / Portal)"),
                    default: 1
                },
                {
                    fieldtype: "Data",
                    fieldname: "web_domains",
                    label: __("Allowed Domains"),
                    default: "*",
                    placeholder: __("e.g. * or https://mysite.com")
                },
                {
                    fieldtype: "Section Break",
                    fieldname: "wa_section",
                    label: __("WhatsApp Channel")
                },
                {
                    fieldtype: "Check",
                    fieldname: "enable_whatsapp",
                    label: __("📱 WhatsApp (Meta Cloud API)"),
                    default: 0
                },
                {
                    fieldtype: "Data",
                    fieldname: "wa_phone_number_id",
                    label: __("Phone Number ID"),
                    placeholder: "e.g. 1495456033646066"
                },
                {
                    fieldtype: "Data",
                    fieldname: "wa_verify_token",
                    label: __("Verify Token"),
                    placeholder: "e.g. my_verify_token_123"
                },
                {
                    fieldtype: "Small Text",
                    fieldname: "wa_access_token",
                    label: __("Permanent System User Access Token"),
                    placeholder: "EAAP..."
                },
                {
                    fieldtype: "Section Break",
                    fieldname: "tg_section",
                    label: __("Telegram Channel")
                },
                {
                    fieldtype: "Check",
                    fieldname: "enable_telegram",
                    label: __("✈️ Telegram Bot"),
                    default: 0
                },
                {
                    fieldtype: "Small Text",
                    fieldname: "tg_bot_token",
                    label: __("Telegram Bot Token (from @BotFather)"),
                    placeholder: "123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ"
                }
            ],
            primary_action_label: startStep === 2 ? (isEdit ? __("💾 Save & Connect Channels") : __("🚀 Save Channels")) : __("Next: Configure Channels →"),
            primary_action: function() {
                if (currentStep === 1) {
                    const title = (dialog.get_value("bot_title") || "").trim();
                    if (!title) {
                        frappe.msgprint({
                            title: __("Validation Required"),
                            indicator: "orange",
                            message: __("Please enter a <strong>Bot Title</strong> before proceeding.")
                        });
                        if (dialog.fields_dict.bot_title && dialog.fields_dict.bot_title.$input) {
                            dialog.fields_dict.bot_title.$input.focus();
                        }
                        return;
                    }

                    if (!isEdit) {
                        let slug = (dialog.get_value("bot_slug") || "").trim();
                        if (!slug) {
                            slug = title.toLowerCase().replace(/[^a-z0-9_]+/g, "_").replace(/^_+|_+$/g, "");
                            setFieldValue("bot_slug", slug);
                        }
                        goToStep(2);
                    } else {
                        const activeSlug = (dialog.get_value("bot_slug") || botSlug || "").trim();
                        if (loadedConfig) {
                            goToStep(2);
                        } else {
                            frappe.call({
                                method: "universal_chatbot.api.v1.wizard.get_bot_config",
                                args: { bot_slug: activeSlug },
                                freeze: true,
                                freeze_message: __("Loading channel configurations..."),
                                callback: function(r) {
                                    if (r.message) {
                                        loadedConfig = r.message;
                                    }
                                    goToStep(2);
                                }
                            });
                        }
                    }
                } else if (currentStep === 2) {
                    submitBotData();
                }
            },
            secondary_action_label: __("Cancel"),
            secondary_action: handleSecondaryAction
        });

        // Helper to robustly set control value, input DOM element, and disp_area
        function setFieldValue(fieldname, value) {
            if (value === undefined || value === null) value = "";
            try {
                dialog.set_value(fieldname, value);
            } catch(e) {}

            const f = dialog.fields_dict[fieldname];
            if (f) {
                if (f.$input) {
                    if (f.df && f.df.fieldtype === "Check") {
                        f.$input.prop("checked", !!value);
                    } else {
                        f.$input.val(value);
                    }
                }
                if (f.disp_area) {
                    $(f.disp_area).text(value).removeClass("hide");
                }
                if (typeof f.set_input === "function") {
                    try { f.set_input(value); } catch(e) {}
                }
            }
        }

        function updateChannelFieldVisibility() {
            const waEnabled = !!dialog.get_value("enable_whatsapp");
            const tgEnabled = !!dialog.get_value("enable_telegram");
            const webEnabled = !!dialog.get_value("enable_web");

            dialog.set_df_property("web_domains", "hidden", webEnabled ? 0 : 1);

            dialog.set_df_property("wa_phone_number_id", "hidden", waEnabled ? 0 : 1);
            dialog.set_df_property("wa_verify_token", "hidden", waEnabled ? 0 : 1);
            dialog.set_df_property("wa_access_token", "hidden", waEnabled ? 0 : 1);

            dialog.set_df_property("tg_bot_token", "hidden", tgEnabled ? 0 : 1);
        }

        function goToStep(step) {
            currentStep = step;
            renderStepView();

            if (currentStep === 2) {
                if (isEdit && loadedConfig) {
                    populateStep2FromConfig(loadedConfig);
                } else {
                    updateChannelFieldVisibility();
                }
            }
        }

        function renderStepView() {
            if (currentStep === 1) {
                step1_fields.forEach(fn => dialog.set_df_property(fn, "hidden", 0));
                step2_fields.forEach(fn => dialog.set_df_property(fn, "hidden", 1));

                dialog.set_primary_action(__("Next: Configure Channels →"));
                dialog.set_secondary_action_label(__("Cancel"));
                dialog.set_secondary_action(function() {
                    dialog.hide();
                });

                updateTemplatePreview(dialog.get_value("starter_template") || initialTemplate);
            } else if (currentStep === 2) {
                step1_fields.forEach(fn => dialog.set_df_property(fn, "hidden", 1));
                step2_fields.forEach(fn => dialog.set_df_property(fn, "hidden", 0));

                if (startStep === 2) {
                    dialog.set_primary_action(isEdit ? __("💾 Save & Connect Channels") : __("🚀 Save Channels"));
                    dialog.set_secondary_action_label(__("Cancel"));
                    dialog.set_secondary_action(function() {
                        dialog.hide();
                    });
                } else {
                    dialog.set_primary_action(isEdit ? __("💾 Save & Update Channels") : __("🚀 Create Bot & Launch Designer"));
                    dialog.set_secondary_action_label(__("← Back"));
                    dialog.set_secondary_action(function() {
                        goToStep(1);
                    });
                }

                updateChannelFieldVisibility();
            }

            // Ensure an explicit Cancel button is available in footer next to secondary action if on step 2 with back
            if (currentStep === 2 && startStep === 1) {
                if (dialog.footer && !dialog.footer.find(".btn-custom-cancel").length) {
                    const $cancelBtn = $(`<button type="button" class="btn btn-default btn-modal-close btn-custom-cancel" style="margin-right:auto;">${__("Cancel")}</button>`);
                    $cancelBtn.on("click", function() {
                        dialog.hide();
                    });
                    dialog.footer.prepend($cancelBtn);
                }
            }

            // Header close button always hides
            dialog.get_close_btn().off("click").on("click", function(e) {
                e.preventDefault();
                dialog.hide();
            });
        }

        function updateTemplatePreview(templateName) {
            const previewMap = {
                "ERP & API Lookup": `
                    <div style="background: #f0f7ff; border: 1px solid #bfdbfe; border-radius: 6px; padding: 12px; margin-top: 8px;">
                        <div style="font-weight: 600; font-size: 13px; color: #1e40af; display: flex; align-items: center; gap: 6px;">
                            <span>⚡ ERP & API Lookup Assistant</span>
                            <span class="badge badge-primary" style="font-size: 10px;">Recommended</span>
                        </div>
                        <div style="font-size: 12px; color: #3b82f6; margin-top: 4px; line-height: 1.4;">
                            Prompts user for an ID (e.g. flat number or order ID), invokes REST API connector (<code>get_maintenance_dues</code>), and prints formatted output.
                        </div>
                    </div>
                `,
                "FAQ & Support": `
                    <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; padding: 12px; margin-top: 8px;">
                        <div style="font-weight: 600; font-size: 13px; color: #15803d; display: flex; align-items: center; gap: 6px;">
                            <span>💬 FAQ & Support Assistant</span>
                            <span class="badge badge-success" style="font-size: 10px;">Interactive</span>
                        </div>
                        <div style="font-size: 12px; color: #16a34a; margin-top: 4px; line-height: 1.4;">
                            Displays an interactive multi-choice menu branching to business hours, contact numbers, and community policies.
                        </div>
                    </div>
                `,
                "Blank Canvas": `
                    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px; margin-top: 8px;">
                        <div style="font-weight: 600; font-size: 13px; color: #475569; display: flex; align-items: center; gap: 6px;">
                            <span>🎨 Blank Canvas</span>
                            <span class="badge badge-secondary" style="font-size: 10px;">Custom</span>
                        </div>
                        <div style="font-size: 12px; color: #64748b; margin-top: 4px; line-height: 1.4;">
                            Minimal starting flow with Start and End nodes. Ideal for crafting completely custom logic in the Visual Flow Designer.
                        </div>
                    </div>
                `
            };

            const html = previewMap[templateName] || previewMap["ERP & API Lookup"];
            const field = dialog.get_field("template_preview_html");
            if (field && field.$wrapper) {
                field.$wrapper.html(html);
            }
        }

        function populateStep2FromConfig(cfg) {
            if (!cfg) return;
            const ch = cfg.channels || {};
            const wa = ch.whatsapp || {};
            const tg = ch.telegram || {};
            const web = ch.web_widget || ch.web || {};
            const webDep = (cfg.deployments || []).find(d => d.channel_type === "Web Widget");

            const hasWa = !!(wa.name || wa.whatsapp_phone_number_id || wa.whatsapp_access_token || wa.is_enabled);
            const hasTg = !!(tg.name || tg.telegram_bot_token || tg.is_enabled);
            const hasWeb = !!(web.name || web.is_enabled !== undefined ? (web.is_enabled ? 1 : 0) : 1);

            const vals = {
                enable_web: hasWeb ? 1 : 0,
                web_domains: (webDep && webDep.allowed_domains) || "*",
                enable_whatsapp: hasWa ? 1 : 0,
                wa_phone_number_id: wa.whatsapp_phone_number_id || "",
                wa_verify_token: wa.whatsapp_verify_token || "",
                wa_access_token: wa.whatsapp_access_token || "",
                enable_telegram: hasTg ? 1 : 0,
                tg_bot_token: tg.telegram_bot_token || ""
            };

            dialog.set_values(vals).then(function() {
                updateChannelFieldVisibility();
            });

            // Also directly update input DOM elements immediately
            setFieldValue("enable_web", hasWeb ? 1 : 0);
            setFieldValue("web_domains", vals.web_domains);
            setFieldValue("enable_whatsapp", hasWa ? 1 : 0);
            setFieldValue("wa_phone_number_id", vals.wa_phone_number_id);
            setFieldValue("wa_verify_token", vals.wa_verify_token);
            setFieldValue("wa_access_token", vals.wa_access_token);
            setFieldValue("enable_telegram", hasTg ? 1 : 0);
            setFieldValue("tg_bot_token", vals.tg_bot_token);

            updateChannelFieldVisibility();
        }

        function applyLoadedConfig(cfg) {
            if (!cfg) return;
            loadedConfig = cfg;

            const title = cfg.title || cfg.bot_slug || initialTitle;
            const slug = cfg.bot_slug || initialSlug;

            dialog.set_title(__("✏️ Edit Chatbot: {0}", [title]));

            setFieldValue("bot_title", title);
            setFieldValue("bot_slug", slug);

            let template = "ERP & API Lookup";
            if (cfg.primary_flow) {
                const pf = (cfg.primary_flow || "").toLowerCase();
                if (pf.includes("faq")) template = "FAQ & Support";
                else if (pf.includes("blank")) template = "Blank Canvas";
                else template = "ERP & API Lookup";
            }
            setFieldValue("starter_template", template);
            updateTemplatePreview(template);

            if (currentStep === 2) {
                populateStep2FromConfig(cfg);
            }
        }

        function submitBotData() {
            const title = (dialog.get_value("bot_title") || "").trim();
            const slug = (dialog.get_value("bot_slug") || botSlug || "").trim();
            const starterTemplate = dialog.get_value("starter_template") || "ERP & API Lookup";

            const templateKeyMap = {
                "ERP & API Lookup": "api_lookup",
                "FAQ & Support": "simple_faq",
                "Blank Canvas": "blank",
                "api_lookup": "api_lookup",
                "simple_faq": "simple_faq",
                "blank": "blank"
            };

            const templateId = templateKeyMap[starterTemplate] || "api_lookup";
            const channels = [];

            channels.push({
                type: "web",
                is_enabled: !!dialog.get_value("enable_web"),
                allowed_domains: dialog.get_value("web_domains") || "*"
            });

            channels.push({
                type: "whatsapp",
                is_enabled: !!dialog.get_value("enable_whatsapp"),
                phone_number_id: (dialog.get_value("wa_phone_number_id") || "").trim(),
                access_token: (dialog.get_value("wa_access_token") || "").trim(),
                verify_token: (dialog.get_value("wa_verify_token") || "").trim()
            });

            channels.push({
                type: "telegram",
                is_enabled: !!dialog.get_value("enable_telegram"),
                bot_token: (dialog.get_value("tg_bot_token") || "").trim()
            });

            frappe.ui.form.is_saving = true;

            frappe.call({
                method: "universal_chatbot.api.v1.wizard.quick_create_bot",
                args: {
                    title: title,
                    bot_slug: slug,
                    template_id: templateId,
                    channels: JSON.stringify(channels),
                    allow_existing: 1,
                    edit_mode: isEdit ? 1 : 0
                },
                freeze: true,
                freeze_message: isEdit
                    ? __("Updating bot and channel configurations...")
                    : __("Scaffolding bot, flow, and deployments..."),
                callback: function(r) {
                    frappe.ui.form.is_saving = false;
                    if (r.message) {
                        dialog.hide();
                        if (isEdit) {
                            frappe.show_alert({
                                message: __("✓ Chatbot '{0}' and channels updated successfully!", [title]),
                                indicator: "green"
                            });
                        } else {
                            showSuccessModal(r.message);
                        }
                        if (typeof onSuccess === "function") {
                            onSuccess(r.message);
                        }
                    }
                }
            });
        }

        function showSuccessModal(result) {
            let deploymentsHtml = "";
            (result.deployments || []).forEach(dep => {
                if (dep.channel_type === "WhatsApp") {
                    deploymentsHtml += `
                        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px; margin-bottom: 8px;">
                            <div style="font-weight: 600; font-size: 13px; color: #166534;">📱 WhatsApp Webhook URL:</div>
                            <div style="display: flex; gap: 8px; margin-top: 4px;">
                                <input type="text" class="form-control input-sm" readonly value="${dep.webhook_url}" style="font-family: monospace; font-size: 11px;" />
                                <button class="btn btn-default btn-xs btn-copy-url" data-url="${dep.webhook_url}">${__("Copy")}</button>
                            </div>
                        </div>
                    `;
                } else if (dep.channel_type === "Telegram") {
                    deploymentsHtml += `
                        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px; margin-bottom: 8px;">
                            <div style="font-weight: 600; font-size: 13px; color: #0369a1;">✈️ Telegram Webhook URL:</div>
                            <div style="display: flex; gap: 8px; margin-top: 4px;">
                                <input type="text" class="form-control input-sm" readonly value="${dep.webhook_url}" style="font-family: monospace; font-size: 11px;" />
                                <button class="btn btn-default btn-xs btn-copy-url" data-url="${dep.webhook_url}">${__("Copy")}</button>
                            </div>
                        </div>
                    `;
                } else if (dep.channel_type === "Web Widget") {
                    deploymentsHtml += `
                        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px; margin-bottom: 8px;">
                            <div style="font-weight: 600; font-size: 13px; color: #4338ca;">🌐 Web Widget Embed Script:</div>
                            <div style="display: flex; gap: 8px; margin-top: 4px;">
                                <input type="text" class="form-control input-sm" readonly value="${escapeHtml(dep.embed_script)}" style="font-family: monospace; font-size: 11px;" />
                                <button class="btn btn-default btn-xs btn-copy-url" data-url="${escapeHtml(dep.embed_script)}">${__("Copy")}</button>
                            </div>
                        </div>
                    `;
                }
            });

            const successDialog = new frappe.ui.Dialog({
                title: __("🎉 Bot Created & Published Successfully!"),
                size: "large",
                fields: [
                    {
                        fieldtype: "HTML",
                        fieldname: "success_html"
                    }
                ],
                primary_action_label: __("🎨 Open in Visual Flow Designer"),
                primary_action: function() {
                    successDialog.hide();
                    if (window.UniversalChatbot && window.UniversalChatbot.open_flow_designer) {
                        window.UniversalChatbot.open_flow_designer(result.flow_name);
                    } else {
                        frappe.set_route("Form", "Chatbot Flow", result.flow_name);
                    }
                },
                secondary_action_label: __("View Chatbot Record"),
                secondary_action: function() {
                    successDialog.hide();
                    frappe.set_route("Form", "Chatbot", result.bot_slug);
                }
            });

            const $sWrapper = successDialog.get_field("success_html").$wrapper;
            $sWrapper.html(`
                <div style="padding: 10px 5px;">
                    <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 14px; margin-bottom: 16px;">
                        <h4 style="margin: 0 0 6px 0; color: #15803d; font-size: 16px;">
                            ✓ <strong>${result.title}</strong> is ready and active!
                        </h4>
                        <div style="font-size: 13px; color: #166534;">
                            Bot Slug: <code>${result.bot_slug}</code> | Main Flow: <code>${result.flow_name}</code> | Version: <code>v${result.version_number}</code>
                        </div>
                    </div>

                    ${deploymentsHtml ? `<div style="margin-bottom: 16px;"><h5 style="margin-bottom: 8px;">Active Channel Endpoints:</h5>${deploymentsHtml}</div>` : ''}

                    <p style="font-size: 13px; color: #64748b; margin-top: 10px;">
                        ${__("Your starter conversation flow has been generated and published. Click the button below to edit nodes visually.")}
                    </p>
                </div>
            `);

            $sWrapper.find(".btn-copy-url").on("click", function() {
                const text = $(this).attr("data-url") || $(this).data("url");
                if (text) {
                    if (frappe.utils && frappe.utils.copy_to_clipboard) {
                        frappe.utils.copy_to_clipboard(text);
                        frappe.show_alert({ message: __("Copied to clipboard!"), indicator: "green" });
                    } else if (navigator.clipboard && navigator.clipboard.writeText) {
                        navigator.clipboard.writeText(text);
                        frappe.show_alert({ message: __("Copied to clipboard!"), indicator: "green" });
                    }
                }
            });

            successDialog.show();
        }

        function escapeHtml(text) {
            return (text || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
        }

        dialog.show();
        renderStepView();

        // Step 1: Pre-fill immediately
        if (isEdit) {
            dialog.set_df_property("bot_slug", "read_only", 1);
            if (dialog.fields_dict.bot_slug && dialog.fields_dict.bot_slug.$input) {
                dialog.fields_dict.bot_slug.$input.prop("readonly", true);
            }

            setFieldValue("bot_title", initialTitle);
            setFieldValue("bot_slug", initialSlug);
            setFieldValue("starter_template", initialTemplate);
            updateTemplatePreview(initialTemplate);

            // Fetch full bot config from DB immediately
            if (botSlug) {
                frappe.call({
                    method: "universal_chatbot.api.v1.wizard.get_bot_config",
                    args: { bot_slug: botSlug },
                    callback: function(r) {
                        if (r.message) {
                            applyLoadedConfig(r.message);
                        }
                    }
                });
            }
        } else {
            if (initialData.bot_title) setFieldValue("bot_title", initialData.bot_title);
            if (initialData.bot_slug) setFieldValue("bot_slug", initialData.bot_slug);
            if (initialData.starter_template) setFieldValue("starter_template", initialData.starter_template);
        }

        // Reinforce on modal shown event
        dialog.$wrapper.on("shown.bs.modal", function() {
            if (isEdit) {
                const curTitle = dialog.get_value("bot_title") || initialTitle;
                const curSlug = dialog.get_value("bot_slug") || initialSlug;
                setFieldValue("bot_title", curTitle);
                setFieldValue("bot_slug", curSlug);
                if (dialog.fields_dict.bot_slug && dialog.fields_dict.bot_slug.$input) {
                    dialog.fields_dict.bot_slug.$input.prop("readonly", true);
                }
            }
            // Bind buttons
            dialog.get_secondary_btn().off("click").on("click", function(e) {
                e.preventDefault();
                handleSecondaryAction();
            });
            dialog.get_close_btn().off("click").on("click", function(e) {
                e.preventDefault();
                dialog.hide();
            });
        });

        // Live input listener for create mode
        if (!isEdit && dialog.fields_dict.bot_title && dialog.fields_dict.bot_title.$input) {
            dialog.fields_dict.bot_title.$input.on("input", function() {
                const raw = $(this).val() || "";
                const slug = raw.toLowerCase().replace(/[^a-z0-9_]+/g, "_").replace(/^_+|_+$/g, "");
                setFieldValue("bot_slug", slug);
            });
        }

        if (dialog.fields_dict.starter_template && dialog.fields_dict.starter_template.$input) {
            dialog.fields_dict.starter_template.$input.on("change", function() {
                updateTemplatePreview($(this).val());
            });
        }

        // Live change listener on channel toggles to show/hide fields smoothly
        if (dialog.fields_dict.enable_whatsapp && dialog.fields_dict.enable_whatsapp.$input) {
            dialog.fields_dict.enable_whatsapp.$input.on("change", function() {
                const checked = $(this).prop("checked");
                dialog.set_value("enable_whatsapp", checked ? 1 : 0).then(function() {
                    updateChannelFieldVisibility();
                });
            });
        }

        if (dialog.fields_dict.enable_telegram && dialog.fields_dict.enable_telegram.$input) {
            dialog.fields_dict.enable_telegram.$input.on("change", function() {
                const checked = $(this).prop("checked");
                dialog.set_value("enable_telegram", checked ? 1 : 0).then(function() {
                    updateChannelFieldVisibility();
                });
            });
        }

        if (dialog.fields_dict.enable_web && dialog.fields_dict.enable_web.$input) {
            dialog.fields_dict.enable_web.$input.on("change", function() {
                const checked = $(this).prop("checked");
                dialog.set_value("enable_web", checked ? 1 : 0).then(function() {
                    updateChannelFieldVisibility();
                });
            });
        }
    };

    /**
     * Public API: Launch Guided Bot Creation
     */
    UniversalChatbot.open_bot_wizard = function(onSuccess, initialData) {
        UniversalChatbot.open_bot_dialog({
            mode: "create",
            onSuccess: onSuccess,
            initialData: initialData
        });
    };

    /**
     * Public API: Launch Guided Bot Editor (Same interface for View and Edit)
     * Accepts either frm, frm.doc, or a bot_slug string.
     */
    UniversalChatbot.open_bot_editor = function(docOrSlug, onSuccess) {
        let doc = null;
        let botSlug = "";

        if (docOrSlug && typeof docOrSlug === "object") {
            if (docOrSlug.doc) {
                doc = docOrSlug.doc;
            } else {
                doc = docOrSlug;
            }
            botSlug = (doc.bot_name || doc.name || doc.docname || "").trim();
        } else if (typeof docOrSlug === "string") {
            botSlug = docOrSlug.trim();
        }

        if (!botSlug && window.cur_frm && window.cur_frm.doc) {
            doc = window.cur_frm.doc;
            botSlug = (doc.bot_name || doc.name || "").trim();
        }

        UniversalChatbot.open_bot_dialog({
            mode: "edit",
            bot_slug: botSlug,
            doc: doc,
            onSuccess: onSuccess
        });
    };

    /**
     * Public API: Launch Guided Channel Wizard directly on Step 2
     * Used by the "+ Add Connection" button on the Chatbot Central Hub.
     */
    UniversalChatbot.open_channel_wizard = function(docOrSlug, onSuccess) {
        let doc = null;
        let botSlug = "";

        if (docOrSlug && typeof docOrSlug === "object") {
            if (docOrSlug.doc) {
                doc = docOrSlug.doc;
            } else {
                doc = docOrSlug;
            }
            botSlug = (doc.bot_name || doc.name || doc.docname || "").trim();
        } else if (typeof docOrSlug === "string") {
            botSlug = docOrSlug.trim();
        }

        if (!botSlug && window.cur_frm && window.cur_frm.doc) {
            doc = window.cur_frm.doc;
            botSlug = (doc.bot_name || doc.name || "").trim();
        }

        UniversalChatbot.open_bot_dialog({
            mode: "edit",
            startStep: 2,
            bot_slug: botSlug,
            doc: doc,
            onSuccess: onSuccess
        });
    };

})();
