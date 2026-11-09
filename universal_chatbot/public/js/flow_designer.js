/**
 * Universal Chatbot - Visual Flow Designer
 * Graphical canvas and node editor for building conversation flows.
 */

window.UniversalChatbot = window.UniversalChatbot || {};

(function() {
    "use strict";

    const NODE_TYPES = [
        { type: "start", label: "Start", desc: "Conversation entry point", icon: "▶" },
        { type: "send_message", label: "Send Message", desc: "Display bot text", icon: "💬" },
        { type: "ask_question", label: "Ask Question", desc: "Prompt user for text", icon: "❓" },
        { type: "multiple_choice", label: "Multiple Choice", desc: "Options / buttons", icon: "🔘" },
        { type: "condition", label: "Condition", desc: "Branching logic", icon: "🔀" },
        { type: "set_variable", label: "Set Variable", desc: "Store state variable", icon: "📝" },
        { type: "call_action", label: "Call Action", desc: "External REST action", icon: "⚡" },
        { type: "end", label: "End", desc: "Terminate conversation", icon: "⏹" }
    ];

    function normalizeType(ntype) {
        if (!ntype) return "";
        return ntype.toLowerCase().replace(/[\s-]+/g, "_");
    }

    class FlowDesigner {
        constructor(container, flowName, options = {}) {
            this.container = $(container);
            this.flowName = flowName;
            this.options = options;

            this.nodes = [];
            this.transitions = [];
            this.variables = [];
            this.selectedNode = null;
            this.connectingFrom = null;

            this.nodeCounter = 1;
            this.activePropertiesTab = "form";
            this.initLayout();
            this.bindEvents();
            this.loadFlow();
        }

        initLayout() {
            this.container.html(`
                <div class="flow-designer-wrapper">
                    <!-- Top Toolbar -->
                    <div class="flow-designer-toolbar">
                        <div class="flow-toolbar-left">
                            <span class="flow-toolbar-title" id="flow-title">${this.flowName}</span>
                            <span class="flow-toolbar-badge" id="flow-status-badge">Draft</span>
                        </div>
                        <div class="flow-toolbar-right">
                            <button class="btn btn-default btn-xs" id="btn-quick-wizard" title="Quick Create / Re-scaffold Bot">
                                <i class="fa fa-magic"></i> ✨ Quick Create Bot
                            </button>
                            <button class="btn btn-default btn-xs" id="btn-validate">
                                <i class="fa fa-check"></i> Validate
                            </button>
                            <button class="btn btn-primary btn-sm btn-save-flow-toolbar" id="btn-save" style="font-weight: 600; padding: 4px 14px;">
                                <i class="fa fa-save"></i> Save Flow
                            </button>
                            <button class="btn btn-success btn-xs" id="btn-publish">
                                <i class="fa fa-rocket"></i> Publish
                            </button>
                        </div>
                    </div>

                    <!-- Main Workspace -->
                    <div class="flow-designer-workspace">
                        <!-- Node Palette -->
                        <div class="flow-palette">
                            <div class="flow-palette-header">Node Palette</div>
                            <div class="flow-palette-items">
                                ${NODE_TYPES.map(n => `
                                    <div class="flow-palette-item" data-type="${n.type}" draggable="true">
                                        <div class="flow-node-icon ${n.type}">${n.icon}</div>
                                        <div class="flow-palette-text">
                                            <span class="flow-palette-title">${n.label}</span>
                                            <span class="flow-palette-desc">${n.desc}</span>
                                        </div>
                                    </div>
                                `).join("")}
                            </div>
                        </div>

                        <!-- Canvas -->
                        <div class="flow-canvas-container" id="flow-canvas-container">
                            <div class="flow-canvas" id="flow-canvas">
                                <svg class="flow-connections-svg" id="connections-svg">
                                    <defs>
                                        <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                                            <path d="M 0 1 L 10 5 L 0 9 z" fill="#94a3b8" />
                                        </marker>
                                        <marker id="arrow-selected" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                                            <path d="M 0 1 L 10 5 L 0 9 z" fill="#3b82f6" />
                                        </marker>
                                    </defs>
                                    <g id="connections-group"></g>
                                    <path id="temp-line" d="" fill="none" stroke="#3b82f6" stroke-dasharray="4" stroke-width="2" style="display:none;" />
                                </svg>
                                <div id="nodes-container"></div>
                            </div>
                        </div>

                        <!-- Properties Panel / Sidebar -->
                        <div class="flow-properties-panel property-panel" id="flow-properties-panel" data-element="property-panel" style="display:none;">
                            <div class="flow-properties-header">
                                <div style="display:flex; align-items:center; gap:8px;">
                                    <span class="flow-prop-header-title" style="font-weight:600; font-size:14px; color:#1e293b;">Node Properties</span>
                                    <span class="flow-selected-badge" style="display:none;"></span>
                                </div>
                                <div style="display:flex; align-items:center; gap:6px;">
                                    <button type="button" class="btn-dock-toggle" title="Toggle Dock Side (Left / Right)" style="background:#f1f5f9; border:1px solid #cbd5e1; border-radius:4px; padding:2px 8px; font-size:11px; font-weight:600; color:#475569; cursor:pointer;">
                                        <i class="fa fa-columns"></i> Dock Left
                                    </button>
                                    <button type="button" class="btn-close-properties" title="Close Panel" style="background:none; border:none; font-size:20px; color:#64748b; cursor:pointer; line-height:1; padding:0 4px;">&times;</button>
                                </div>
                            </div>
                            <div class="flow-properties-body" id="flow-properties-content">
                                <div class="flow-properties-empty">
                                    <div style="font-size:24px;margin-bottom:8px;">🖱️</div>
                                    Select a node on the canvas to configure properties.
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `);

            this.$canvas = this.container.find("#flow-canvas");
            this.$canvasContainer = this.container.find("#flow-canvas-container");
            this.$nodesContainer = this.container.find("#nodes-container");
            this.$connectionsGroup = this.container.find("#connections-group");
            this.$tempLine = this.container.find("#temp-line");
            this.$propertiesPanel = this.container.find(".flow-properties-panel, #flow-properties-panel, #property-panel");
            this.$propertiesContent = this.container.find("#flow-properties-content, .flow-properties-body");
            this.$propertiesHeader = this.container.find(".flow-properties-header");
        }

        bindEvents() {
            const me = this;

            // Palette item click / drag
            this.container.on("click", ".flow-palette-item", function() {
                const nodeType = $(this).data("type");
                me.createNode(nodeType, 200 + Math.random() * 80, 150 + Math.random() * 80);
            });

            // Canvas dragover & drop
            this.$canvasContainer.on("dragover", function(e) {
                e.preventDefault();
            });

            this.$canvasContainer.on("drop", function(e) {
                e.preventDefault();
                const nodeType = e.originalEvent.dataTransfer.getData("text/plain");
                if (!nodeType) return;
                const rect = me.$canvas[0].getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                me.createNode(nodeType, Math.max(20, x), Math.max(20, y));
            });

            this.container.on("dragstart", ".flow-palette-item", function(e) {
                e.originalEvent.dataTransfer.setData("text/plain", $(this).data("type"));
            });

            // Canvas click deselect
            this.$canvas.on("click", function(e) {
                if ($(e.target).closest(".flow-canvas-node, .flow-node, .node, .flow-port, .flow-properties-panel, #flow-properties-panel, #property-panel").length === 0) {
                    me.selectNode(null);
                }
            });

            // Node click / drag logic
            let draggingNode = null;
            let dragOffset = { x: 0, y: 0 };

            // Universal selection delegation on container matching all node selectors (.flow-canvas-node, .flow-node, .node)
            this.container.on("mousedown", ".flow-canvas-node, .flow-node, .node", function(e) {
                if ($(e.target).is(".flow-port") || $(e.target).is(".flow-node-delete-btn")) return;
                const $nodeEl = $(this).closest(".flow-canvas-node, .flow-node, .node");
                const nid = $nodeEl.data("id") || $nodeEl.attr("data-id") || ($nodeEl.attr("id") ? $nodeEl.attr("id").replace(/^node-/, "") : null);
                if (nid) {
                    me.selectNode(nid);
                }

                draggingNode = $nodeEl;
                const pos = draggingNode.position();
                dragOffset = {
                    x: e.pageX - pos.left,
                    y: e.pageY - pos.top
                };
                e.stopPropagation();
            });

            // Explicit click on canvas node opens property inspector
            this.container.on("click", ".flow-canvas-node, .flow-node, .node", function(e) {
                if ($(e.target).is(".flow-port") || $(e.target).is(".flow-node-delete-btn")) return;
                const $nodeEl = $(this).closest(".flow-canvas-node, .flow-node, .node");
                const nid = $nodeEl.data("id") || $nodeEl.attr("data-id") || ($nodeEl.attr("id") ? $nodeEl.attr("id").replace(/^node-/, "") : null);
                if (nid) {
                    me.selectNode(nid);
                }
                e.stopPropagation();
            });

            // Prevent clicks inside properties panel from closing it
            this.container.on("click mousedown", ".flow-properties-panel, #flow-properties-panel, #property-panel", function(e) {
                e.stopPropagation();
            });

            // Toggle dock left / right button
            this.container.on("click", ".btn-dock-toggle", function(e) {
                e.preventDefault();
                e.stopPropagation();
                const $panel = me.$propertiesPanel;
                const isLeft = $panel.hasClass("dock-left");
                if (isLeft) {
                    $panel.removeClass("dock-left");
                    $(this).html('<i class="fa fa-columns"></i> Dock Left');
                } else {
                    $panel.addClass("dock-left");
                    $(this).html('<i class="fa fa-columns"></i> Dock Right');
                }
            });

            // Close properties panel button
            this.container.on("click", ".btn-close-properties", function(e) {
                e.preventDefault();
                e.stopPropagation();
                me.selectNode(null);
            });

            // Node delete button
            this.$nodesContainer.on("click", ".flow-node-delete-btn", function(e) {
                e.stopPropagation();
                const nid = $(this).closest(".flow-canvas-node").data("id");
                me.deleteNode(nid);
            });

            // Connection creation (drag from output port)
            this.$nodesContainer.on("mousedown", ".flow-port.port-out", function(e) {
                e.stopPropagation();
                const nid = $(this).closest(".flow-canvas-node").data("id");
                me.connectingFrom = nid;
                me.$tempLine.show();
                me.updateTempLine(e.pageX, e.pageY);
            });

            // Complete connection on input port
            this.$nodesContainer.on("mouseup", ".flow-port.port-in", function(e) {
                e.stopPropagation();
                if (me.connectingFrom) {
                    const targetNid = $(this).closest(".flow-canvas-node").data("id");
                    if (me.connectingFrom !== targetNid) {
                        me.createTransition(me.connectingFrom, targetNid);
                    }
                    me.connectingFrom = null;
                    me.$tempLine.hide();
                }
            });

            $(document).on("mousemove.flow_designer", function(e) {
                if (draggingNode) {
                    const newX = Math.max(0, e.pageX - dragOffset.x);
                    const newY = Math.max(0, e.pageY - dragOffset.y);
                    draggingNode.css({ left: newX + "px", top: newY + "px" });
                    const nid = draggingNode.data("id");
                    const nodeObj = me.nodes.find(n => n.node_id === nid);
                    if (nodeObj) {
                        nodeObj.x = newX;
                        nodeObj.y = newY;
                    }
                    me.renderTransitions();
                } else if (me.connectingFrom) {
                    me.updateTempLine(e.pageX, e.pageY);
                }
            });

            $(document).on("mouseup.flow_designer", function() {
                draggingNode = null;
                if (me.connectingFrom) {
                    me.connectingFrom = null;
                    me.$tempLine.hide();
                }
            });

            // Click transition to delete
            this.$connectionsGroup.on("click", ".flow-connection-path", function() {
                const src = $(this).data("src");
                const tgt = $(this).data("tgt");
                frappe.confirm(`Delete connection from ${src} to ${tgt}?`, () => {
                    me.transitions = me.transitions.filter(t => !(t.source_node === src && t.target_node === tgt));
                    me.renderTransitions();
                });
            });

            // Toolbar buttons
            this.container.find("#btn-quick-wizard").on("click", () => {
                if (window.UniversalChatbot && window.UniversalChatbot.open_bot_wizard) {
                    window.UniversalChatbot.open_bot_wizard((res) => {
                        if (res && res.flow_name) {
                            me.loadFlow(res.flow_name);
                        }
                    });
                }
            });
            this.container.find("#btn-validate").on("click", () => me.validateFlowUI());
            this.container.find("#btn-save").on("click", () => me.saveFlow());
            this.container.find("#btn-publish").on("click", () => me.publishFlow());

            // Global Delegated Handlers for Properties Panel (bound once to prevent duplicate executions)
            // Variable chips insertion click handler
            this.container.on("click", ".btn-insert-var-chip", function(e) {
                e.preventDefault();
                e.stopPropagation();
                const varName = $(this).data("var");
                const targetSel = $(this).data("target");
                const $target = me.$propertiesContent.find(targetSel);
                if ($target.length) {
                    me.insertVariableAtCursor($target, varName);
                }
            });

            // Tab switching
            this.container.on("click", ".flow-prop-tab", function(e) {
                e.preventDefault();
                e.stopPropagation();
                const tab = $(this).data("tab");
                me.activePropertiesTab = tab;
                me.$propertiesContent.find(".flow-prop-tab").removeClass("active");
                $(this).addClass("active");
                me.$propertiesContent.find(".flow-tab-content").hide();
                me.$propertiesContent.find(`.flow-tab-${tab}`).show();
            });

            // Format JSON button
            this.container.on("click", "#btn-format-json", function(e) {
                e.preventDefault();
                e.stopPropagation();
                const $jsonEditor = me.$propertiesContent.find("#prop-node-config-json");
                const $jsonStatus = me.$propertiesContent.find("#prop-json-status");
                try {
                    const parsed = JSON.parse($jsonEditor.val());
                    $jsonEditor.val(JSON.stringify(parsed, null, 2));
                    $jsonStatus.text("Valid JSON").removeClass("invalid").addClass("valid");
                    $jsonEditor.removeClass("is-invalid");
                } catch (err) {
                    frappe.msgprint({
                        title: __("Invalid JSON"),
                        indicator: "red",
                        message: __("Cannot format invalid JSON: {0}", [err.message])
                    });
                }
            });

            // Node ID change listener
            this.container.on("change blur", "#prop-node-id", function() {
                if (!me.selectedNode) return;
                const node = me.nodes.find(n => n.node_id === me.selectedNode);
                if (!node) return;

                const newId = $(this).val().trim();
                if (!newId || newId === node.node_id) {
                    $(this).val(node.node_id);
                    return;
                }
                if (me.nodes.some(n => n.node_id === newId)) {
                    frappe.msgprint({
                        title: __("Validation Error"),
                        indicator: "red",
                        message: __("A node with ID '{0}' already exists.", [newId])
                    });
                    $(this).val(node.node_id);
                    return;
                }
                const oldId = node.node_id;
                node.node_id = newId;

                // Update transitions referencing this node
                me.transitions.forEach(t => {
                    if (t.source_node === oldId) t.source_node = newId;
                    if (t.target_node === oldId) t.target_node = newId;
                });

                // Update canvas DOM element
                const $nodeEl = me.$nodesContainer.find(`[data-id="${oldId}"]`);
                $nodeEl.attr("data-id", newId);
                $nodeEl.find(".flow-node-id").text(newId);

                me.selectedNode = newId;
                me.renderTransitions();
                frappe.show_alert({ message: __("Renamed node to '{0}'", [newId]), indicator: "blue" }, 3);
            });

            // JSON Editor real-time synchronization
            this.container.on("input change", "#prop-node-config-json", function() {
                if (!me.selectedNode) return;
                const node = me.nodes.find(n => n.node_id === me.selectedNode);
                if (!node) return;

                const $jsonStatus = me.$propertiesContent.find("#prop-json-status");
                const rawVal = $(this).val().trim();
                try {
                    const parsed = rawVal ? JSON.parse(rawVal) : {};
                    if (typeof parsed !== "object" || Array.isArray(parsed)) {
                        throw new Error("Configuration must be a JSON object {...}");
                    }
                    $jsonStatus.text("Valid JSON").removeClass("invalid").addClass("valid");
                    $(this).removeClass("is-invalid");

                    // Preserve UI coordinates
                    const uiX = node.configuration ? node.configuration.ui_x : undefined;
                    const uiY = node.configuration ? node.configuration.ui_y : undefined;
                    node.configuration = parsed;
                    if (uiX !== undefined) node.configuration.ui_x = uiX;
                    if (uiY !== undefined) node.configuration.ui_y = uiY;

                    // Update snippet preview on canvas
                    const snippet = me.getNodeSnippet(node);
                    me.$nodesContainer.find(`[data-id="${node.node_id}"] .flow-node-snippet`).text(snippet);

                    // Sync quick fields from newly pasted / typed JSON
                    me.updateQuickFieldsFromConfig(node);
                } catch (err) {
                    $jsonStatus.text("Invalid JSON").removeClass("valid").addClass("invalid").attr("title", err.message);
                    $(this).addClass("is-invalid");
                }
            });

            // Call Action: Add Parameter Button
            this.container.on("click", ".btn-add-param", function(e) {
                e.preventDefault();
                e.stopPropagation();
                if (!me.selectedNode) return;
                const node = me.nodes.find(n => n.node_id === me.selectedNode);
                if (!node) return;
                const upstreamVars = me.getUpstreamVariables(node.node_id);
                me.$propertiesContent.find(".params-empty-note").remove();
                const $row = $(me.renderParamRow("", "", upstreamVars, node.node_id));
                me.$propertiesContent.find("#flow-params-container").append($row);
                $row.find(".param-key").focus();
                me.syncCallActionFromUI(node);
            });

            // Call Action: Add Output Mapping Button
            this.container.on("click", ".btn-add-output", function(e) {
                e.preventDefault();
                e.stopPropagation();
                if (!me.selectedNode) return;
                const node = me.nodes.find(n => n.node_id === me.selectedNode);
                if (!node) return;
                me.$propertiesContent.find(".outputs-empty-note").remove();
                const $row = $(me.renderOutputRow("", ""));
                me.$propertiesContent.find("#flow-outputs-container").append($row);
                $row.find(".output-path").focus();
                me.syncCallActionFromUI(node);
            });

            // Call Action: Remove Row Event
            this.container.on("click", ".btn-remove-row", function(e) {
                e.preventDefault();
                e.stopPropagation();
                if (!me.selectedNode) return;
                const node = me.nodes.find(n => n.node_id === me.selectedNode);
                if (!node) return;
                const $container = $(this).closest("#flow-params-container, #flow-outputs-container");
                $(this).closest(".flow-mapping-row").remove();
                if ($container.attr("id") === "flow-params-container" && $container.children(".param-row").length === 0) {
                    $container.html('<div class="flow-mapping-empty-note params-empty-note">No parameters configured. Click "+ Add Parameter" above.</div>');
                } else if ($container.attr("id") === "flow-outputs-container" && $container.children(".output-row").length === 0) {
                    $container.html('<div class="flow-mapping-empty-note outputs-empty-note">No output mappings configured. Click "+ Add Output" above.</div>');
                }
                me.syncCallActionFromUI(node);
            });

            // Call Action: Parameter quick variable dropdown select
            this.container.on("change", ".param-quick-select", function(e) {
                e.stopPropagation();
                const sel = $(this).val();
                if (sel) {
                    $(this).siblings(".param-val").val(sel).trigger("input");
                    $(this).val("");
                }
            });

            // Call Action: Fetch Output Schema Button (Test & Extract API Variables)
            this.container.on("click", ".btn-fetch-schema", function(e) {
                e.preventDefault();
                e.stopPropagation();
                if (!me.selectedNode) return;
                const node = me.nodes.find(n => n.node_id === me.selectedNode);
                if (node) {
                    me.fetchOutputSchema(node);
                }
            });

            // Call Action: Input change events
            this.container.on("input change", "#prop-action-name, .param-key, .param-val, .output-path, .output-var", function(e) {
                if (!me.selectedNode) return;
                const node = me.nodes.find(n => n.node_id === me.selectedNode);
                if (node && normalizeType(node.node_type) === "call_action") {
                    me.syncCallActionFromUI(node);
                }
            });

            // Simple prop-field change listener
            this.container.on("input change", ".prop-field", function(e) {
                if (!me.selectedNode) return;
                const node = me.nodes.find(n => n.node_id === me.selectedNode);
                if (node && normalizeType(node.node_type) !== "call_action") {
                    me.syncSimpleFieldsFromUI(node);
                }
            });
        }

        updateTempLine(pageX, pageY) {
            if (!this.connectingFrom) return;
            const srcNode = this.nodes.find(n => n.node_id === this.connectingFrom);
            if (!srcNode) return;
            const srcEl = this.$nodesContainer.find(`[data-id="${srcNode.node_id}"]`);
            const rect = this.$canvas[0].getBoundingClientRect();
            const startX = srcNode.x + srcEl.outerWidth() / 2;
            const startY = srcNode.y + srcEl.outerHeight();
            const curX = pageX - rect.left + this.$canvasContainer.scrollLeft();
            const curY = pageY - rect.top + this.$canvasContainer.scrollTop();

            const d = `M ${startX} ${startY} C ${startX} ${startY + 40}, ${curX} ${curY - 40}, ${curX} ${curY}`;
            this.$tempLine.attr("d", d);
        }

        loadFlow() {
            const me = this;
            frappe.call({
                method: "universal_chatbot.api.v1.flow_designer.load_visual_flow",
                args: { flow_name: this.flowName },
                callback: function(r) {
                    if (r.message) {
                        const data = r.message;
                        me.nodes = (data.nodes || []).map(n => ({
                            ...n,
                            node_type: normalizeType(n.node_type)
                        }));
                        me.transitions = data.transitions || [];
                        me.variables = data.variables || [];
                        me.container.find("#flow-status-badge").text(data.status || "Draft");
                        if (data.status === "Published") {
                            me.container.find("#flow-status-badge").addClass("published");
                        }
                        me.renderAll();
                    }
                }
            });
        }

        createNode(nodeType, x = 100, y = 100) {
            let nid = `${nodeType}_${this.nodeCounter++}`;
            while (this.nodes.some(n => n.node_id === nid)) {
                nid = `${nodeType}_${this.nodeCounter++}`;
            }

            const defConfig = this.getDefaultConfigForType(nodeType);
            const node = {
                node_id: nid,
                node_type: nodeType,
                configuration: defConfig,
                x: x,
                y: y
            };

            this.nodes.push(node);
            this.renderNode(node);
            this.selectNode(nid);
        }

        getDefaultConfigForType(type) {
            switch (type) {
                case "start":
                    return { description: "Conversation start" };
                case "send_message":
                    return { message: "Hello! How can I assist you today?" };
                case "ask_question":
                    return { prompt: "Please enter your response:", save_to_variable: "user_input" };
                case "multiple_choice":
                    return { prompt: "Please choose an option:", save_to_variable: "user_choice", options: ["Option 1", "Option 2"] };
                case "condition":
                    return { variable: "user_choice", operator: "==", value: "Option 1" };
                case "set_variable":
                    return { variable: "status", value: "active" };
                case "call_action":
                    return { action_name: "", parameters: {}, output_variable: "action_result" };
                case "end":
                    return { message: "Thank you for chatting with us. Goodbye!" };
                default:
                    return {};
            }
        }

        deleteNode(nodeId) {
            this.nodes = this.nodes.filter(n => n.node_id !== nodeId);
            this.transitions = this.transitions.filter(t => t.source_node !== nodeId && t.target_node !== nodeId);
            this.$nodesContainer.find(`[data-id="${nodeId}"]`).remove();
            if (this.selectedNode === nodeId) {
                this.selectNode(null);
            }
            this.renderTransitions();
        }

        createTransition(src, tgt) {
            if (src === tgt) return;
            const exists = this.transitions.some(t => t.source_node === src && t.target_node === tgt);
            if (exists) return;
            this.transitions.push({
                source_node: src,
                target_node: tgt,
                condition: ""
            });
            this.renderTransitions();
        }

        renderAll() {
            this.$nodesContainer.empty();
            this.nodes.forEach(n => this.renderNode(n));
            this.renderTransitions();
        }

        renderNode(node) {
            const normType = normalizeType(node.node_type);
            const meta = NODE_TYPES.find(t => t.type === normType) || { label: node.node_type || "Node", icon: "•" };
            const snippet = this.getNodeSnippet(node);
            const esc = (s) => (s === null || s === undefined) ? "" : ((window.frappe && frappe.utils && frappe.utils.escape_html) ? frappe.utils.escape_html(String(s)) : String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;"));

            const html = `
                <div class="flow-canvas-node flow-node node" id="node-${node.node_id}" data-id="${node.node_id}" data-node-id="${node.node_id}" style="left:${node.x}px; top:${node.y}px;">
                    ${normType !== "start" ? '<div class="flow-port port-in"></div>' : ""}
                    <div class="flow-node-header">
                        <div class="flow-node-header-title">
                            <span class="flow-node-icon ${normType}" style="width:20px;height:20px;font-size:10px;">${meta.icon}</span>
                            <span>${meta.label}</span>
                        </div>
                        <button class="flow-node-delete-btn" title="Delete node">&times;</button>
                    </div>
                    <div class="flow-node-body">
                        <div class="flow-node-id">${node.node_id}</div>
                        <div class="flow-node-snippet">${esc(snippet)}</div>
                    </div>
                    ${normType !== "end" ? '<div class="flow-port port-out"></div>' : ""}
                </div>
            `;
            this.$nodesContainer.append(html);
        }

        getNodeSnippet(node) {
            const c = node.configuration || {};
            if (c.message) return c.message;
            if (c.text) return c.text;
            if (c.prompt) return c.prompt;
            if (c.question) return c.question;
            if (c.variable) return `${c.variable} ${c.operator || "=="} ${c.value || ""}`;
            if (c.action_name) {
                const pKeys = c.parameters ? Object.keys(c.parameters) : [];
                return pKeys.length > 0 ? `${c.action_name}(${pKeys.join(", ")})` : `Action: ${c.action_name}`;
            }
            return "";
        }

        renderTransitions() {
            const me = this;
            let svgHtml = "";
            this.transitions.forEach(t => {
                const srcNode = me.nodes.find(n => n.node_id === t.source_node);
                const tgtNode = me.nodes.find(n => n.node_id === t.target_node);
                if (!srcNode || !tgtNode) return;

                const srcEl = me.$nodesContainer.find(`[data-id="${t.source_node}"]`);
                const tgtEl = me.$nodesContainer.find(`[data-id="${t.target_node}"]`);
                if (!srcEl.length || !tgtEl.length) return;

                const startX = srcNode.x + srcEl.outerWidth() / 2;
                const startY = srcNode.y + srcEl.outerHeight();
                const endX = tgtNode.x + tgtEl.outerWidth() / 2;
                const endY = tgtNode.y;

                const dy = Math.max(30, Math.abs(endY - startY) / 2);
                const path = `M ${startX} ${startY} C ${startX} ${startY + dy}, ${endX} ${endY - dy}, ${endX} ${endY}`;
                svgHtml += `<path class="flow-connection-path" data-src="${t.source_node}" data-tgt="${t.target_node}" d="${path}" marker-end="url(#arrow)" />`;
            });
            this.$connectionsGroup.html(svgHtml);
        }

        selectNode(nodeId) {
            this.selectedNode = nodeId;
            this.$nodesContainer.find(".flow-canvas-node, .flow-node, .node").removeClass("selected active");

            if (!nodeId) {
                if (this.$propertiesPanel) {
                    this.$propertiesPanel.removeClass("open active visible").css("display", "none").hide();
                }
                const $badge = this.container.find(".flow-selected-badge");
                if ($badge.length) $badge.hide();
                if (this.$propertiesContent) {
                    this.$propertiesContent.html('<div class="flow-properties-empty"><div style="font-size:24px;margin-bottom:8px;">🖱️</div>Select a node on the canvas to configure properties.</div>');
                }
                return;
            }

            const node = this.nodes.find(n => n.node_id === nodeId);
            if (!node) {
                if (this.$propertiesPanel) {
                    this.$propertiesPanel.removeClass("open active visible").css("display", "none").hide();
                }
                return;
            }

            // Highlight node with active & selected classes
            const $nodeEl = this.$nodesContainer.find(`[data-id="${nodeId}"], #node-${nodeId}`);
            $nodeEl.addClass("selected active");

            // Slide open & display properties sidebar panel
            if (this.$propertiesPanel) {
                this.$propertiesPanel.addClass("open active visible").css("display", "flex").show();
            }

            this.renderProperties(node);
        }

        escapeHtml(s) {
            if (s === null || s === undefined) return "";
            if (window.frappe && frappe.utils && frappe.utils.escape_html) {
                return frappe.utils.escape_html(String(s));
            }
            return String(s)
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }

        getUpstreamVariables(nodeId) {
            if (!nodeId) return [];

            const visited = new Set();
            const upstreamNodeIds = new Set();

            // Recursive DFS working backwards along incoming transitions
            const dfsUpstream = (currId) => {
                const incoming = this.transitions.filter(t => t.target_node === currId);
                for (const t of incoming) {
                    const srcId = t.source_node;
                    if (!visited.has(srcId)) {
                        visited.add(srcId);
                        upstreamNodeIds.add(srcId);
                        dfsUpstream(srcId);
                    }
                }
            };

            dfsUpstream(nodeId);

            const collectedVars = [];

            // Only collect save_to_variable, variable, or output_mapping keys from preceding nodes
            for (const n of this.nodes) {
                if (upstreamNodeIds.has(n.node_id)) {
                    const c = n.configuration || {};
                    const normType = normalizeType(n.node_type);

                    // 1. Ask Question & Multiple Choice: save_to_variable
                    if (normType === "ask_question" || normType === "multiple_choice") {
                        if (c.save_to_variable && typeof c.save_to_variable === "string") {
                            const v = c.save_to_variable.trim();
                            if (v && !collectedVars.includes(v)) {
                                collectedVars.push(v);
                            }
                        }
                    }
                    // 2. Set Variable: variable
                    else if (normType === "set_variable") {
                        if (c.variable && typeof c.variable === "string") {
                            const v = c.variable.trim();
                            if (v && !collectedVars.includes(v)) {
                                collectedVars.push(v);
                            }
                        }
                    }
                    // 3. Call Action: output_mapping keys
                    else if (normType === "call_action") {
                        if (c.output_mapping && typeof c.output_mapping === "object" && !Array.isArray(c.output_mapping)) {
                            for (const [k, v] of Object.entries(c.output_mapping)) {
                                if (k && typeof k === "string" && /^[a-zA-Z_][a-zA-Z0-9_]*$/.test(k)) {
                                    const vName = k.trim();
                                    if (!collectedVars.includes(vName)) {
                                        collectedVars.push(vName);
                                    }
                                }
                                if (typeof v === "string" && /^[a-zA-Z_][a-zA-Z0-9_]*$/.test(v) && !v.includes(".")) {
                                    const vName = v.trim();
                                    if (!collectedVars.includes(vName)) {
                                        collectedVars.push(vName);
                                    }
                                }
                            }
                        }
                        if (c.output_variable && typeof c.output_variable === "string") {
                            const v = c.output_variable.trim();
                            if (!collectedVars.includes(v)) collectedVars.push(v);
                        }
                        if (c.save_result_to_variable && typeof c.save_result_to_variable === "string") {
                            const v = c.save_result_to_variable.trim();
                            if (!collectedVars.includes(v)) collectedVars.push(v);
                        }
                    }
                }
            }

            return collectedVars;
        }

        extractVariablesFromNode(node) {
            const vars = [];
            if (!node || !node.configuration) return vars;
            const c = node.configuration;
            const normType = normalizeType(node.node_type);

            if (normType === "ask_question" || normType === "multiple_choice") {
                if (c.save_to_variable && typeof c.save_to_variable === "string") {
                    vars.push(c.save_to_variable.trim());
                }
            } else if (normType === "set_variable") {
                if (c.variable && typeof c.variable === "string") {
                    vars.push(c.variable.trim());
                }
            } else if (normType === "call_action") {
                if (c.output_mapping && typeof c.output_mapping === "object" && !Array.isArray(c.output_mapping)) {
                    for (const [k, v] of Object.entries(c.output_mapping)) {
                        if (/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(k)) {
                            vars.push(k.trim());
                        }
                        if (typeof v === "string" && /^[a-zA-Z_][a-zA-Z0-9_]*$/.test(v) && !v.includes(".")) {
                            vars.push(v.trim());
                        }
                    }
                }
                if (c.output_variable && typeof c.output_variable === "string") {
                    vars.push(c.output_variable.trim());
                }
                if (c.save_result_to_variable && typeof c.save_result_to_variable === "string") {
                    vars.push(c.save_result_to_variable.trim());
                }
                if (c.result_variable && typeof c.result_variable === "string") {
                    vars.push(c.result_variable.trim());
                }
            }
            return vars;
        }

        renderParamRow(key = "", val = "", upstreamVars = [], nodeId = "") {
            const esc = this.escapeHtml.bind(this);
            const datalistId = `var-list-param-${nodeId}`;
            return `
                <div class="flow-mapping-row param-row">
                    <input type="text" class="form-control param-key" placeholder="API Param (e.g. flat_number)" value="${esc(key)}" style="flex:1; font-size:12px; padding:5px 8px;" />
                    <span style="color:#94a3b8; font-size:12px; font-weight:bold;">&larr;</span>
                    <input type="text" class="form-control param-val" list="${datalistId}" placeholder="Value or {{var}}" value="${esc(val)}" style="flex:1; font-size:12px; padding:5px 8px;" />
                    ${upstreamVars.length > 0 ? `
                        <select class="param-quick-select" title="Insert variable" style="width: auto; max-width: 85px; font-size: 11px; padding: 4px 6px; border: 1px solid #cbd5e1; border-radius: 4px; background: #ffffff; color: #3b82f6; font-weight: 600; cursor: pointer;">
                            <option value="">+ Var</option>
                            ${upstreamVars.map(v => `<option value="{{${esc(v)}}}">{{${esc(v)}}}</option>`).join("")}
                        </select>
                    ` : ''}
                    <button type="button" class="btn-remove-row" title="Remove parameter">
                        <i class="fa fa-times"></i>
                    </button>
                </div>
            `;
        }

        renderOutputRow(targetVar = "", path = "") {
            const esc = this.escapeHtml.bind(this);
            return `
                <div class="flow-mapping-row output-row">
                    <input type="text" class="form-control output-path" placeholder="API Response Key (e.g. data.amount)" value="${esc(path)}" style="flex:1.2; font-size:12px; padding:5px 8px;" />
                    <span style="color:#94a3b8; font-size:12px; font-weight:bold;">&rarr;</span>
                    <input type="text" class="form-control output-var" placeholder="Flow Var (e.g. dues)" value="${esc(targetVar)}" style="flex:1; font-size:12px; padding:5px 8px;" />
                    <button type="button" class="btn-remove-row" title="Remove output mapping">
                        <i class="fa fa-times"></i>
                    </button>
                </div>
            `;
        }

        renderProperties(node) {
            const me = this;
            const normType = normalizeType(node.node_type);
            const meta = NODE_TYPES.find(t => t.type === normType) || { label: node.node_type || "Node", icon: "•" };
            const c = node.configuration || {};
            const esc = this.escapeHtml.bind(this);

            const upstreamVars = this.getUpstreamVariables(node.node_id);

            // Clone configuration without internal ui coordinates for the JSON editor
            const cleanConfig = Object.assign({}, c);
            delete cleanConfig.ui_x;
            delete cleanConfig.ui_y;

            // Update header badge with node label
            const $badge = this.container.find(".flow-selected-badge");
            if ($badge.length) {
                $badge.text(meta.label).show();
            }

            // Datalist for variable autocompletion
            const datalistId = `var-list-param-${node.node_id}`;
            const datalistHtml = `
                <datalist id="${datalistId}">
                    ${upstreamVars.map(v => `<option value="{{${esc(v)}}}">${esc(v)}</option>`).join("")}
                </datalist>
            `;

            // Helper to render variable chips
            const renderChips = (targetSelector, title = "Available Variables (click to insert)") => `
                <div class="flow-form-group" style="margin-top: 8px;">
                    <label style="font-size:11px; font-weight:600; color:#475569; display:flex; align-items:center; gap:4px;">
                        <i class="fa fa-tags" style="color:#6366f1;"></i> ${title}
                    </label>
                    <div class="flow-var-chips-container" style="margin-top:4px;">
                        ${upstreamVars.length > 0 ? upstreamVars.map(v => `
                            <button type="button" class="btn-insert-var-chip" data-var="${esc(v)}" data-target="${targetSelector}" title="Insert {{${esc(v)}}}">
                                <span class="chip-brackets">{{</span>${esc(v)}<span class="chip-brackets">}}</span>
                            </button>
                        `).join("") : `
                            <div class="flow-mapping-empty-note">No upstream variables detected. Connect an Ask Question or Call Action node upstream.</div>
                        `}
                    </div>
                </div>
            `;

            // Generate type-specific quick helper fields
            let customFields = "";

            if (normType === "send_message" || normType === "end") {
                customFields = `
                    <div class="flow-form-group">
                        <label>Message Content</label>
                        <textarea class="prop-field form-control" id="prop-message-text" data-key="message" rows="4" placeholder="Enter message text...">${esc(c.message || c.text || "")}</textarea>
                        <div class="flow-form-help">Supports {{variable_name}} template syntax.</div>
                    </div>
                    ${renderChips("#prop-message-text")}
                `;
            } else if (normType === "ask_question") {
                customFields = `
                    <div class="flow-form-group">
                        <label>Prompt Text</label>
                        <textarea class="prop-field form-control" id="prop-question-prompt" data-key="prompt" rows="3" placeholder="e.g. Please enter your flat number:">${esc(c.prompt || c.question || "")}</textarea>
                        <div class="flow-form-help">The question prompt displayed to the user.</div>
                    </div>
                    ${renderChips("#prop-question-prompt", "Insert Variable into Prompt")}
                    <div class="flow-form-group" style="margin-top: 12px;">
                        <label>Save to Variable</label>
                        <input type="text" class="prop-field form-control" id="prop-save-variable" data-key="save_to_variable" value="${esc(c.save_to_variable || "")}" placeholder="e.g. user_flat" />
                        <div class="flow-form-help">Variable name to store the user's response for downstream nodes.</div>
                    </div>
                `;
            } else if (normType === "call_action") {
                customFields = `
                    <div class="flow-call-action-builder">
                        <div class="flow-form-group">
                            <label>Integration Action Name</label>
                            <input type="text" class="form-control" id="prop-action-name" value="${esc(c.action_name || "")}" placeholder="e.g. get_maintenance_dues" />
                            <div class="flow-form-help">Unique action identifier configured in Integration Action.</div>
                        </div>

                        <!-- Parameters (Inputs) Section -->
                        <div class="flow-form-group" style="margin-top: 14px;">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 6px;">
                                <label style="font-weight:600; font-size:12px; margin:0;">
                                    <i class="fa fa-sign-in" style="color:#3b82f6;"></i> Input Parameters
                                </label>
                                <button type="button" class="btn btn-default btn-xs btn-add-param" style="font-size:11px; padding:2px 7px;">
                                    <i class="fa fa-plus"></i> Add Parameter
                                </button>
                            </div>
                            <div class="flow-form-help" style="margin-bottom:6px;">Map API parameter keys to flow variables or static values.</div>
                            <div class="flow-params-list" id="flow-params-container"></div>
                        </div>

                        <!-- Output Mapping Section -->
                        <div class="flow-form-group" style="margin-top: 14px;">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 6px;">
                                <label style="font-weight:600; font-size:12px; margin:0;">
                                    <i class="fa fa-sign-out" style="color:#10b981;"></i> Output Mapping
                                </label>
                                <div style="display:flex; gap:6px;">
                                    <button type="button" class="btn btn-default btn-xs btn-fetch-schema" style="font-size:11px; padding:2px 7px; color:#2563eb; font-weight:600;" title="Test API and extract response fields">
                                        <i class="fa fa-bolt"></i> Fetch Output Schema
                                    </button>
                                    <button type="button" class="btn btn-default btn-xs btn-add-output" style="font-size:11px; padding:2px 7px;">
                                        <i class="fa fa-plus"></i> Add Output
                                    </button>
                                </div>
                            </div>
                            <div class="flow-form-help" style="margin-bottom:6px;">Map API response fields into flow variables.</div>
                            <div class="flow-outputs-list" id="flow-outputs-container"></div>
                        </div>
                    </div>
                `;
            } else if (normType === "multiple_choice") {
                const optStr = Array.isArray(c.options) ? c.options.map(o => typeof o === "object" ? (o.label || o.value) : o).join(", ") : (c.options || "");
                customFields = `
                    <div class="flow-form-group">
                        <label>Prompt Text</label>
                        <textarea class="prop-field form-control" id="prop-mc-prompt" data-key="prompt" rows="2">${esc(c.prompt || c.question || "")}</textarea>
                    </div>
                    ${renderChips("#prop-mc-prompt")}
                    <div class="flow-form-group" style="margin-top: 10px;">
                        <label>Options (comma separated)</label>
                        <input type="text" class="prop-field form-control" data-key="options_str" value="${esc(optStr)}" placeholder="Option 1, Option 2" />
                    </div>
                    <div class="flow-form-group" style="margin-top: 10px;">
                        <label>Save to Variable</label>
                        <input type="text" class="prop-field form-control" data-key="save_to_variable" value="${esc(c.save_to_variable || "")}" placeholder="e.g. user_choice" />
                    </div>
                `;
            } else if (normType === "condition") {
                customFields = `
                    <div class="flow-form-group">
                        <label>Variable to Check</label>
                        <input type="text" class="prop-field form-control" data-key="variable" list="${datalistId}" value="${esc(c.variable || "")}" placeholder="e.g. flat_number" />
                    </div>
                    <div class="flow-form-group" style="margin-top: 10px;">
                        <label>Operator</label>
                        <select class="prop-field form-control" data-key="operator">
                            <option value="==" ${c.operator === "==" ? "selected" : ""}>Equals (==)</option>
                            <option value="!=" ${c.operator === "!=" ? "selected" : ""}>Not Equals (!=)</option>
                            <option value=">" ${c.operator === ">" ? "selected" : ""}>Greater Than (&gt;)</option>
                            <option value="<" ${c.operator === "<" ? "selected" : ""}>Less Than (&lt;)</option>
                            <option value="contains" ${c.operator === "contains" ? "selected" : ""}>Contains</option>
                        </select>
                    </div>
                    <div class="flow-form-group" style="margin-top: 10px;">
                        <label>Compare Value</label>
                        <input type="text" class="prop-field form-control" data-key="value" value="${esc(c.value !== undefined ? String(c.value) : "")}" placeholder="e.g. active" />
                    </div>
                `;
            } else if (normType === "set_variable") {
                customFields = `
                    <div class="flow-form-group">
                        <label>Variable Name</label>
                        <input type="text" class="prop-field form-control" data-key="variable" list="${datalistId}" value="${esc(c.variable || "")}" placeholder="e.g. resident_type" />
                    </div>
                    <div class="flow-form-group" style="margin-top: 10px;">
                        <label>Value</label>
                        <input type="text" class="prop-field form-control" id="prop-set-value" data-key="value" value="${esc(c.value !== undefined ? String(c.value) : "")}" placeholder="e.g. Owner" />
                    </div>
                    ${renderChips("#prop-set-value")}
                `;
            }

            const activeTab = this.activePropertiesTab || "form";

            const html = `
                ${datalistHtml}
                <div class="flow-properties-section">
                    <div class="flow-form-group">
                        <label>Node ID</label>
                        <input type="text" id="prop-node-id" class="form-control" value="${esc(node.node_id)}" placeholder="Unique Node ID" />
                        <div class="flow-form-help">Unique string identifier for this node.</div>
                    </div>
                    <div class="flow-form-group" style="margin-top: 10px;">
                        <label>Node Type</label>
                        <input type="text" class="form-control" value="${meta.icon} ${meta.label} (${node.node_type})" disabled style="background:#f1f5f9; cursor:not-allowed;" />
                    </div>
                </div>

                <div class="flow-prop-tabs" style="margin-top: 14px;">
                    ${customFields ? `<div class="flow-prop-tab ${activeTab === 'form' ? 'active' : ''}" data-tab="form">Quick Form</div>` : ''}
                    <div class="flow-prop-tab ${activeTab === 'json' || !customFields ? 'active' : ''}" data-tab="json">Configuration (JSON)</div>
                </div>

                ${customFields ? `
                    <div class="flow-tab-content flow-tab-form" style="${activeTab === 'form' ? 'display:block;' : 'display:none;'}">
                        ${customFields}
                    </div>
                ` : ''}

                <div class="flow-tab-content flow-tab-json" style="${activeTab === 'json' || !customFields ? 'display:block;' : 'display:none;'}">
                    <div class="flow-form-group">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                            <label style="margin:0; font-size:12px; font-weight:600;">Configuration (JSON)</label>
                            <div style="display:flex; gap:6px; align-items:center;">
                                <span id="prop-json-status" class="flow-json-badge valid">Valid JSON</span>
                                <button type="button" class="btn btn-default btn-xs" id="btn-format-json" title="Format / Beautify JSON" style="padding:1px 6px; font-size:11px;">
                                    <i class="fa fa-magic"></i> Format
                                </button>
                            </div>
                        </div>
                        <textarea id="prop-node-config-json" class="prop-json-editor" rows="12" spellcheck="false">${esc(JSON.stringify(cleanConfig, null, 2))}</textarea>
                        <div class="flow-form-help" style="margin-top:4px;">
                            Edit the raw JSON blob governing prompts, parameters, mappings, or variables.
                        </div>
                    </div>
                </div>
            `;

            this.$propertiesContent.html(html);

            if (normType === "call_action") {
                this.updateCallActionFormFromConfig(node, upstreamVars);
            }
        }

        fetchOutputSchema(node) {
            const me = this;
            const actionName = this.$propertiesContent.find("#prop-action-name").val().trim() || (node.configuration && node.configuration.action_name);
            if (!actionName) {
                frappe.msgprint({
                    title: __("Action Name Required"),
                    indicator: "orange",
                    message: __("Please enter an Integration Action Name (e.g. 'get_maintenance_dues') before testing output schema.")
                });
                return;
            }

            // Gather any current parameter keys
            const currentParams = {};
            this.$propertiesContent.find("#flow-params-container .param-row").each(function() {
                const k = $(this).find(".param-key").val().trim();
                const v = $(this).find(".param-val").val().trim();
                if (k) currentParams[k] = v;
            });

            const paramKeys = Object.keys(currentParams);
            let promptFields = [];

            if (paramKeys.length > 0) {
                promptFields = paramKeys.map(k => ({
                    fieldname: k,
                    fieldtype: "Data",
                    label: __(k),
                    reqd: 0,
                    default: (currentParams[k] || "").replace(/[{}]/g, "").trim()
                }));
            } else {
                promptFields = [
                    {
                        fieldname: "sample_param_name",
                        fieldtype: "Data",
                        label: __("Sample Parameter Key (optional)"),
                        default: "flat_number"
                    },
                    {
                        fieldname: "sample_param_val",
                        fieldtype: "Data",
                        label: __("Sample Parameter Value"),
                        default: "TB2-203"
                    }
                ];
            }

            frappe.prompt(
                promptFields,
                function(values) {
                    let samplePayload = {};
                    if (paramKeys.length > 0) {
                        samplePayload = values;
                    } else if (values.sample_param_name && values.sample_param_val) {
                        samplePayload[values.sample_param_name.trim()] = values.sample_param_val.trim();
                    }

                    frappe.call({
                        method: "universal_chatbot.api.v1.flow_designer.test_integration_action",
                        args: {
                            action_name: actionName,
                            sample_parameters: JSON.stringify(samplePayload)
                        },
                        freeze: true,
                        freeze_message: __("Executing Action and Inferring Schema..."),
                        callback: function(r) {
                            if (r.message && r.message.status === "success") {
                                const result = r.message.result;
                                const extracted = me.extractPathsFromApiResponse(result);

                                if (extracted.length === 0) {
                                    frappe.msgprint({
                                        title: __("No Output Fields Found"),
                                        indicator: "orange",
                                        message: __("The action executed successfully but returned no key-value fields to extract.")
                                    });
                                    return;
                                }

                                if (!node.configuration) node.configuration = {};
                                if (!node.configuration.output_mapping || typeof node.configuration.output_mapping !== "object") {
                                    node.configuration.output_mapping = {};
                                }

                                let addedCount = 0;
                                extracted.forEach(item => {
                                    const existingPaths = Object.values(node.configuration.output_mapping);
                                    if (!node.configuration.output_mapping[item.targetVar] && !existingPaths.includes(item.path)) {
                                        node.configuration.output_mapping[item.targetVar] = item.path;
                                        addedCount++;
                                    }
                                });

                                // Re-render the output mapping section and sync with JSON editor
                                me.updateCallActionFormFromConfig(node);
                                me.syncConfigToJSONEditor(node);

                                frappe.show_alert({
                                    message: __("Successfully extracted {0} output schema field(s)!", [addedCount || extracted.length]),
                                    indicator: "green"
                                }, 5);
                            } else {
                                frappe.msgprint({
                                    title: __("API Test Failed"),
                                    indicator: "red",
                                    message: __(r.message ? r.message.message : "Could not execute action with sample parameters.")
                                });
                            }
                        }
                    });
                },
                __("Test Integration Action: {0}", [actionName]),
                __("Execute & Extract")
            );
        }

        extractPathsFromApiResponse(result) {
            const list = [];
            if (!result || typeof result !== "object") return list;

            const traverse = (obj, prefix = "", depth = 0) => {
                if (depth > 4 || !obj || typeof obj !== "object") return;
                for (const [k, v] of Object.entries(obj)) {
                    if (k === "_action_output_mapping" || k === "status_code") continue;
                    const fullPath = prefix ? `${prefix}.${k}` : k;
                    if (v && typeof v === "object" && !Array.isArray(v)) {
                        traverse(v, fullPath, depth + 1);
                    } else if (Array.isArray(v)) {
                        if (v.length > 0 && typeof v[0] === "object") {
                            traverse(v[0], `${fullPath}.0`, depth + 1);
                        } else {
                            list.push({ path: fullPath, targetVar: k });
                        }
                    } else {
                        list.push({ path: fullPath, targetVar: k });
                    }
                }
            };

            if (result.data && typeof result.data === "object") {
                traverse(result.data, "data", 1);
            } else if (result.unpacked && typeof result.unpacked === "object") {
                traverse(result.unpacked, "unpacked", 1);
            } else {
                traverse(result, "", 0);
            }

            return list;
        }

        insertVariableAtCursor($el, varName) {
            if (!$el || !$el.length) return;
            const token = `{{${varName}}}`;
            const dom = $el[0];
            const start = dom.selectionStart !== undefined ? dom.selectionStart : dom.value.length;
            const end = dom.selectionEnd !== undefined ? dom.selectionEnd : dom.value.length;
            const text = dom.value;
            dom.value = text.substring(0, start) + token + text.substring(end);
            dom.selectionStart = dom.selectionEnd = start + token.length;
            dom.focus();
            $el.trigger("input");
        }

        syncCallActionFromUI(node) {
            const actionName = this.$propertiesContent.find("#prop-action-name").val().trim();
            const parameters = {};
            this.$propertiesContent.find("#flow-params-container .param-row").each(function() {
                const k = $(this).find(".param-key").val().trim();
                const v = $(this).find(".param-val").val().trim();
                if (k) {
                    parameters[k] = v;
                }
            });

            const outputMapping = {};
            this.$propertiesContent.find("#flow-outputs-container .output-row").each(function() {
                const path = $(this).find(".output-path").val().trim();
                const vname = $(this).find(".output-var").val().trim();
                if (vname && path) {
                    outputMapping[vname] = path;
                } else if (vname) {
                    outputMapping[vname] = vname;
                } else if (path) {
                    outputMapping[path] = path;
                }
            });

            node.configuration.action_name = actionName;
            node.configuration.parameters = parameters;
            node.configuration.output_mapping = outputMapping;

            this.syncConfigToJSONEditor(node);
        }

        syncSimpleFieldsFromUI(node) {
            this.$propertiesContent.find(".prop-field").each(function() {
                const key = $(this).data("key");
                let val = $(this).val();
                if (!key) return;

                if (key === "options_str") {
                    node.configuration.options = val.split(",").map(s => s.trim()).filter(Boolean);
                } else if (key === "prompt") {
                    node.configuration.prompt = val;
                    node.configuration.question = val;
                } else if (key === "message") {
                    node.configuration.message = val;
                    node.configuration.text = val;
                } else {
                    node.configuration[key] = val;
                }
            });

            this.syncConfigToJSONEditor(node);
        }

        syncConfigToJSONEditor(node) {
            const currentClean = { ...node.configuration };
            delete currentClean.ui_x;
            delete currentClean.ui_y;

            const $jsonEditor = this.$propertiesContent.find("#prop-node-config-json");
            const $jsonStatus = this.$propertiesContent.find("#prop-json-status");
            $jsonEditor.val(JSON.stringify(currentClean, null, 2));
            $jsonStatus.text("Valid JSON").removeClass("invalid").addClass("valid");
            $jsonEditor.removeClass("is-invalid");

            const snippet = this.getNodeSnippet(node);
            this.$nodesContainer.find(`[data-id="${node.node_id}"] .flow-node-snippet`).text(snippet);
        }

        updateCallActionFormFromConfig(node, upstreamVars) {
            const c = node.configuration || {};
            const vars = upstreamVars || this.getUpstreamVariables(node.node_id);
            this.$propertiesContent.find("#prop-action-name").val(c.action_name || "");

            // Rebuild parameters
            const $paramsContainer = this.$propertiesContent.find("#flow-params-container");
            $paramsContainer.empty();
            const params = c.parameters || {};
            const paramEntries = Object.entries(params);
            if (paramEntries.length > 0) {
                paramEntries.forEach(([k, v]) => {
                    const valStr = typeof v === "object" ? JSON.stringify(v) : String(v);
                    $paramsContainer.append(this.renderParamRow(k, valStr, vars, node.node_id));
                });
            } else {
                $paramsContainer.html('<div class="flow-mapping-empty-note params-empty-note">No parameters configured. Click "+ Add Parameter" above.</div>');
            }

            // Rebuild output mapping
            const $outputsContainer = this.$propertiesContent.find("#flow-outputs-container");
            $outputsContainer.empty();
            const outputs = c.output_mapping || {};
            const outputEntries = Object.entries(outputs);
            if (outputEntries.length > 0) {
                outputEntries.forEach(([k, v]) => {
                    let targetVar = k;
                    let path = typeof v === "string" ? v : JSON.stringify(v);
                    if (k.includes(".") && typeof v === "string" && !v.includes(".")) {
                        path = k;
                        targetVar = v;
                    }
                    $outputsContainer.append(this.renderOutputRow(targetVar, path));
                });
            } else {
                $outputsContainer.html('<div class="flow-mapping-empty-note outputs-empty-note">No output mappings configured. Click "+ Add Output" above.</div>');
            }
        }

        updateQuickFieldsFromConfig(node) {
            const c = node.configuration || {};
            const normType = normalizeType(node.node_type);

            if (normType === "call_action") {
                this.updateCallActionFormFromConfig(node);
                return;
            }

            if (normType === "ask_question") {
                const promptVal = c.prompt !== undefined ? c.prompt : (c.question || "");
                this.$propertiesContent.find("#prop-question-prompt").val(promptVal);
                this.$propertiesContent.find("#prop-save-variable").val(c.save_to_variable || "");
                return;
            }

            if (normType === "send_message" || normType === "end") {
                const msgVal = c.message !== undefined ? c.message : (c.text || "");
                this.$propertiesContent.find("#prop-message-text").val(msgVal);
                return;
            }

            this.$propertiesContent.find(".prop-field").each(function() {
                const key = $(this).data("key");
                if (key === "options_str") {
                    const optStr = Array.isArray(c.options) ? c.options.map(o => typeof o === "object" ? (o.label || o.value) : o).join(", ") : (c.options || "");
                    $(this).val(optStr);
                } else if (key && c[key] !== undefined) {
                    $(this).val(c[key]);
                }
            });
        }

        syncActiveNodeProperties() {
            if (!this.selectedNode) return true;
            const node = this.nodes.find(n => n.node_id === this.selectedNode);
            if (!node) return true;

            const normType = normalizeType(node.node_type);
            if (normType === "call_action") {
                this.syncCallActionFromUI(node);
            } else {
                this.syncSimpleFieldsFromUI(node);
            }

            const $idInput = this.$propertiesContent.find("#prop-node-id");
            if ($idInput.length) {
                const newId = $idInput.val().trim();
                if (newId && newId !== node.node_id && !this.nodes.some(n => n.node_id === newId)) {
                    const oldId = node.node_id;
                    node.node_id = newId;
                    this.transitions.forEach(t => {
                        if (t.source_node === oldId) t.source_node = newId;
                        if (t.target_node === oldId) t.target_node = newId;
                    });
                    this.selectedNode = newId;
                }
            }

            const $jsonEditor = this.$propertiesContent.find("#prop-node-config-json");
            if ($jsonEditor.length) {
                const rawVal = $jsonEditor.val().trim();
                try {
                    const parsed = rawVal ? JSON.parse(rawVal) : {};
                    if (typeof parsed !== "object" || Array.isArray(parsed)) {
                        throw new Error("Configuration must be a JSON object {...}");
                    }
                    const uiX = node.configuration ? node.configuration.ui_x : undefined;
                    const uiY = node.configuration ? node.configuration.ui_y : undefined;
                    node.configuration = parsed;
                    if (uiX !== undefined) node.configuration.ui_x = uiX;
                    if (uiY !== undefined) node.configuration.ui_y = uiY;
                } catch (e) {
                    frappe.msgprint({
                        title: __("Invalid JSON Configuration"),
                        indicator: "red",
                        message: __("Node '{0}' has invalid JSON configuration: {1}", [node.node_id, e.message])
                    });
                    return false;
                }
            }

            return true;
        }

        serialize() {
            this.syncActiveNodeProperties();
            return {
                flow_name: this.flowName,
                nodes: this.nodes.map(n => ({
                    node_id: n.node_id,
                    node_type: n.node_type,
                    configuration: n.configuration || {},
                    x: Math.round(n.x),
                    y: Math.round(n.y)
                })),
                transitions: this.transitions.map(t => ({
                    source_node: t.source_node,
                    target_node: t.target_node,
                    condition: t.condition || ""
                })),
                variables: this.variables || []
            };
        }

        validateFlowUI(showSuccessToast = true) {
            const payload = this.serialize();
            const startNodes = payload.nodes.filter(n => normalizeType(n.node_type) === "start");
            if (startNodes.length === 0) {
                frappe.msgprint({
                    title: __("Validation Error"),
                    indicator: "red",
                    message: __("The flow must have at least one Start node.")
                });
                return false;
            }
            if (startNodes.length > 1) {
                frappe.msgprint({
                    title: __("Validation Error"),
                    indicator: "red",
                    message: __("The flow cannot have more than one Start node.")
                });
                return false;
            }

            const nodeIds = new Set();
            for (const n of payload.nodes) {
                const nid = (n.node_id || "").trim();
                if (!nid) {
                    frappe.msgprint({
                        title: __("Validation Error"),
                        indicator: "red",
                        message: __("All flow nodes must have a non-empty Node ID.")
                    });
                    return false;
                }
                if (nodeIds.has(nid)) {
                    frappe.msgprint({
                        title: __("Validation Error"),
                        indicator: "red",
                        message: __("Duplicate Node ID '{0}' found.", [nid])
                    });
                    return false;
                }
                nodeIds.add(nid);
            }

            if (showSuccessToast) {
                frappe.show_alert({ message: __("Flow structure is valid!"), indicator: "green" });
            }
            return true;
        }

        saveFlow(callback) {
            const me = this;
            if (!this.syncActiveNodeProperties()) return;
            if (!this.validateFlowUI(false)) return;

            const payload = this.serialize();
            frappe.call({
                method: "universal_chatbot.api.v1.flow_designer.save_visual_flow",
                args: {
                    flow_name: this.flowName,
                    flow_data: JSON.stringify(payload)
                },
                freeze: true,
                freeze_message: __("Saving Flow..."),
                callback: function(r) {
                    if (r.message && r.message.status === "success") {
                        frappe.show_alert({
                            message: __("Flow '{0}' saved successfully! ({1} nodes, {2} transitions)", [
                                me.flowName,
                                r.message.nodes_count || me.nodes.length,
                                r.message.transitions_count || me.transitions.length
                            ]),
                            indicator: "green"
                        }, 5);

                        // Reload parent form in Desk if open to prevent state divergence
                        if (window.cur_frm && window.cur_frm.doc && window.cur_frm.doc.name === me.flowName) {
                            window.cur_frm.reload_doc();
                        }

                        if (typeof callback === "function") {
                            callback(r.message);
                        }
                    } else {
                        frappe.msgprint({
                            title: __("Save Failed"),
                            indicator: "red",
                            message: __("Could not save flow: {0}", [r.message ? r.message.error || JSON.stringify(r.message) : "Unknown error"])
                        });
                    }
                },
                error: function(err) {
                    frappe.msgprint({
                        title: __("Error Saving Flow"),
                        indicator: "red",
                        message: err.message || __("An error occurred while saving the flow.")
                    });
                }
            });
        }

        publishFlow() {
            const me = this;
            if (!this.validateFlowUI(false)) return;

            frappe.prompt([
                {
                    fieldname: "changelog",
                    fieldtype: "Small Text",
                    label: __("Version Changelog"),
                    default: "Published from Visual Flow Designer"
                }
            ], function(values) {
                frappe.call({
                    method: "universal_chatbot.api.v1.flow_designer.publish_flow",
                    args: {
                        flow_name: me.flowName,
                        changelog: values.changelog
                    },
                    freeze: true,
                    freeze_message: __("Publishing Flow..."),
                    callback: function(r) {
                        if (r.message && r.message.status === "success") {
                            frappe.msgprint({
                                title: __("Flow Published"),
                                indicator: "green",
                                message: __("Published version {0} successfully.", [r.message.version_number])
                            });
                            me.container.find("#flow-status-badge").text("Published").addClass("published");
                        }
                    }
                });
            }, __("Publish New Version"), __("Publish"));
        }
    }

    UniversalChatbot.FlowDesigner = FlowDesigner;

    UniversalChatbot.open_flow_designer = function(flowName, frm) {
        let designerInstance = null;

        const dialog = new frappe.ui.Dialog({
            title: `Visual Flow Designer: ${flowName}`,
            size: "extra-large",
            fields: [
                {
                    fieldtype: "HTML",
                    fieldname: "designer_container"
                }
            ],
            primary_action_label: __("Save Flow"),
            primary_action: function() {
                if (designerInstance) {
                    designerInstance.saveFlow();
                }
            },
            secondary_action_label: __("Close"),
            secondary_action: function() {
                dialog.hide();
            }
        });

        dialog.$wrapper.addClass("flow-designer-modal");

        // Add prominent Save button in modal header
        const $headerSaveBtn = $(`
            <button type="button" class="btn btn-primary btn-sm btn-save-flow-header" style="margin-right: 12px; font-weight: 600;">
                <i class="fa fa-save" style="margin-right: 4px;"></i> ${__("Save Flow")}
            </button>
        `);
        $headerSaveBtn.on("click", function(e) {
            e.preventDefault();
            if (designerInstance) {
                designerInstance.saveFlow();
            }
        });

        // Insert into modal header
        const $actions = dialog.$wrapper.find(".modal-header .modal-actions");
        if ($actions.length) {
            $actions.prepend($headerSaveBtn);
        } else {
            dialog.$wrapper.find(".modal-header").append($headerSaveBtn);
        }

        dialog.show();

        // Style primary action in footer
        const $primaryBtn = dialog.get_primary_btn();
        if ($primaryBtn && $primaryBtn.length) {
            $primaryBtn.addClass("btn-save-flow-footer").html(`<i class="fa fa-save" style="margin-right: 5px;"></i> ${__("Save Flow")}`);
        }

        const $wrapper = dialog.get_field("designer_container").$wrapper;
        $wrapper.css({ width: "100%", height: "100%", display: "flex", flex: "1", "min-width": "0", "max-width": "100%", overflow: "hidden" });
        designerInstance = new FlowDesigner($wrapper, flowName, { dialog: dialog, frm: frm });
        dialog.flowDesignerInstance = designerInstance;
    };

})();
