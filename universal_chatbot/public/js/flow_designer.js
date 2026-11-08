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
                            <button class="btn btn-default btn-xs" id="btn-validate">
                                <i class="fa fa-check"></i> Validate
                            </button>
                            <button class="btn btn-primary btn-xs" id="btn-save">
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

                        <!-- Properties Panel -->
                        <div class="flow-properties-panel" id="flow-properties-panel">
                            <div class="flow-properties-header">
                                <span>Node Properties</span>
                            </div>
                            <div class="flow-properties-body" id="flow-properties-content">
                                <div class="flow-properties-empty">Select a node on the canvas to configure properties.</div>
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
            this.$propertiesContent = this.container.find("#flow-properties-content");
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
                if ($(e.target).closest(".flow-canvas-node").length === 0 && !$(e.target).is(".flow-port")) {
                    me.selectNode(null);
                }
            });

            // Node click / drag logic
            let draggingNode = null;
            let dragOffset = { x: 0, y: 0 };

            this.$nodesContainer.on("mousedown", ".flow-canvas-node", function(e) {
                if ($(e.target).is(".flow-port") || $(e.target).is(".flow-node-delete-btn")) return;
                const nid = $(this).data("id");
                me.selectNode(nid);

                draggingNode = $(this);
                const pos = draggingNode.position();
                dragOffset = {
                    x: e.pageX - pos.left,
                    y: e.pageY - pos.top
                };
                e.stopPropagation();
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
            this.container.find("#btn-validate").on("click", () => me.validateFlowUI());
            this.container.find("#btn-save").on("click", () => me.saveFlow());
            this.container.find("#btn-publish").on("click", () => me.publishFlow());
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
                        me.nodes = data.nodes || [];
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
            const meta = NODE_TYPES.find(t => t.type === node.node_type) || { label: node.node_type, icon: "•" };
            const snippet = this.getNodeSnippet(node);

            const html = `
                <div class="flow-canvas-node" data-id="${node.node_id}" style="left:${node.x}px; top:${node.y}px;">
                    ${node.node_type !== "start" ? '<div class="flow-port port-in"></div>' : ""}
                    <div class="flow-node-header">
                        <div class="flow-node-header-title">
                            <span class="flow-node-icon ${node.node_type}" style="width:20px;height:20px;font-size:10px;">${meta.icon}</span>
                            <span>${meta.label}</span>
                        </div>
                        <button class="flow-node-delete-btn" title="Delete node">&times;</button>
                    </div>
                    <div class="flow-node-body">
                        <div class="flow-node-id">${node.node_id}</div>
                        <div class="flow-node-snippet">${frappe.utils.escape_html(snippet)}</div>
                    </div>
                    ${node.node_type !== "end" ? '<div class="flow-port port-out"></div>' : ""}
                </div>
            `;
            this.$nodesContainer.append(html);
        }

        getNodeSnippet(node) {
            const c = node.configuration || {};
            if (c.message) return c.message;
            if (c.prompt) return c.prompt;
            if (c.variable) return `${c.variable} ${c.operator || "=="} ${c.value || ""}`;
            if (c.action_name) return `Action: ${c.action_name}`;
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
            this.$nodesContainer.find(".flow-canvas-node").removeClass("selected");
            if (!nodeId) {
                this.$propertiesContent.html('<div class="flow-properties-empty">Select a node on the canvas to configure properties.</div>');
                return;
            }

            const node = this.nodes.find(n => n.node_id === nodeId);
            if (!node) return;
            this.$nodesContainer.find(`[data-id="${nodeId}"]`).addClass("selected");
            this.renderProperties(node);
        }

        renderProperties(node) {
            const me = this;
            const c = node.configuration || {};
            let customFields = "";

            if (node.node_type === "send_message" || node.node_type === "end") {
                customFields = `
                    <div class="flow-form-group">
                        <label>Message Content</label>
                        <textarea class="prop-field" data-key="message" rows="4">${c.message || ""}</textarea>
                        <div class="flow-form-help">Supports {{variable_name}} template syntax.</div>
                    </div>
                `;
            } else if (node.node_type === "ask_question") {
                customFields = `
                    <div class="flow-form-group">
                        <label>Question Prompt</label>
                        <textarea class="prop-field" data-key="prompt" rows="3">${c.prompt || ""}</textarea>
                    </div>
                    <div class="flow-form-group">
                        <label>Save Answer To Variable</label>
                        <input type="text" class="prop-field" data-key="save_to_variable" value="${c.save_to_variable || ""}" />
                    </div>
                `;
            } else if (node.node_type === "multiple_choice") {
                const optStr = Array.isArray(c.options) ? c.options.map(o => typeof o === "object" ? (o.label || o.value) : o).join(", ") : (c.options || "");
                customFields = `
                    <div class="flow-form-group">
                        <label>Prompt</label>
                        <textarea class="prop-field" data-key="prompt" rows="2">${c.prompt || ""}</textarea>
                    </div>
                    <div class="flow-form-group">
                        <label>Options (comma separated)</label>
                        <input type="text" class="prop-field" data-key="options_str" value="${optStr}" />
                    </div>
                    <div class="flow-form-group">
                        <label>Save Answer To Variable</label>
                        <input type="text" class="prop-field" data-key="save_to_variable" value="${c.save_to_variable || ""}" />
                    </div>
                `;
            } else if (node.node_type === "condition") {
                customFields = `
                    <div class="flow-form-group">
                        <label>Variable</label>
                        <input type="text" class="prop-field" data-key="variable" value="${c.variable || ""}" />
                    </div>
                    <div class="flow-form-group">
                        <label>Operator</label>
                        <select class="prop-field" data-key="operator">
                            <option value="==" ${c.operator === "==" ? "selected" : ""}>Equals (==)</option>
                            <option value="!=" ${c.operator === "!=" ? "selected" : ""}>Not Equals (!=)</option>
                            <option value=">" ${c.operator === ">" ? "selected" : ""}>Greater Than (&gt;)</option>
                            <option value="<" ${c.operator === "<" ? "selected" : ""}>Less Than (&lt;)</option>
                            <option value="contains" ${c.operator === "contains" ? "selected" : ""}>Contains</option>
                        </select>
                    </div>
                    <div class="flow-form-group">
                        <label>Compare Value</label>
                        <input type="text" class="prop-field" data-key="value" value="${c.value || ""}" />
                    </div>
                `;
            } else if (node.node_type === "set_variable") {
                customFields = `
                    <div class="flow-form-group">
                        <label>Variable Name</label>
                        <input type="text" class="prop-field" data-key="variable" value="${c.variable || ""}" />
                    </div>
                    <div class="flow-form-group">
                        <label>Value</label>
                        <input type="text" class="prop-field" data-key="value" value="${c.value || ""}" />
                    </div>
                `;
            } else if (node.node_type === "call_action") {
                customFields = `
                    <div class="flow-form-group">
                        <label>Integration Action</label>
                        <input type="text" class="prop-field" data-key="action_name" value="${c.action_name || ""}" placeholder="e.g. get_order_status" />
                    </div>
                    <div class="flow-form-group">
                        <label>Save Result To Variable</label>
                        <input type="text" class="prop-field" data-key="output_variable" value="${c.output_variable || "action_result"}" />
                    </div>
                `;
            }

            const html = `
                <div class="flow-form-group">
                    <label>Node ID</label>
                    <input type="text" id="prop-node-id" value="${node.node_id}" />
                </div>
                <div class="flow-form-group">
                    <label>Node Type</label>
                    <input type="text" value="${node.node_type}" disabled />
                </div>
                <hr style="margin: 8px 0; border-top: 1px solid #f1f5f9;" />
                ${customFields}
            `;

            this.$propertiesContent.html(html);

            // Change listeners
            this.$propertiesContent.find("#prop-node-id").on("change", function() {
                const newId = $(this).val().trim();
                if (!newId || newId === node.node_id) return;
                if (me.nodes.some(n => n.node_id === newId)) {
                    frappe.msgprint(__("A node with this ID already exists."));
                    $(this).val(node.node_id);
                    return;
                }
                const oldId = node.node_id;
                node.node_id = newId;
                me.transitions.forEach(t => {
                    if (t.source_node === oldId) t.source_node = newId;
                    if (t.target_node === oldId) t.target_node = newId;
                });
                me.renderAll();
                me.selectNode(newId);
            });

            this.$propertiesContent.find(".prop-field").on("input change", function() {
                const key = $(this).data("key");
                let val = $(this).val();

                if (key === "options_str") {
                    node.configuration.options = val.split(",").map(s => s.trim()).filter(Boolean);
                } else {
                    node.configuration[key] = val;
                }
                const snippet = me.getNodeSnippet(node);
                me.$nodesContainer.find(`[data-id="${node.node_id}"] .flow-node-snippet`).text(snippet);
            });
        }

        serialize() {
            return {
                flow_name: this.flowName,
                nodes: this.nodes.map(n => ({
                    node_id: n.node_id,
                    node_type: n.node_type,
                    configuration: n.configuration,
                    x: Math.round(n.x),
                    y: Math.round(n.y)
                })),
                transitions: this.transitions.map(t => ({
                    source_node: t.source_node,
                    target_node: t.target_node,
                    condition: t.condition || ""
                })),
                variables: this.variables
            };
        }

        validateFlowUI() {
            const payload = this.serialize();
            const startNodes = payload.nodes.filter(n => n.node_type === "start");
            if (startNodes.length === 0) {
                frappe.msgprint({ title: __("Validation Error"), indicator: "red", message: __("The flow must have at least one Start node.") });
                return false;
            }
            if (startNodes.length > 1) {
                frappe.msgprint({ title: __("Validation Error"), indicator: "red", message: __("The flow cannot have more than one Start node.") });
                return false;
            }
            frappe.show_alert({ message: __("Flow structure is valid!"), indicator: "green" });
            return true;
        }

        saveFlow() {
            const me = this;
            if (!this.validateFlowUI()) return;

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
                        frappe.show_alert({ message: __("Flow saved successfully!"), indicator: "green" });
                    }
                }
            });
        }

        publishFlow() {
            const me = this;
            if (!this.validateFlowUI()) return;

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

    UniversalChatbot.open_flow_designer = function(flowName) {
        const dialog = new frappe.ui.Dialog({
            title: `Visual Flow Designer: ${flowName}`,
            size: "extra-large",
            fields: [
                {
                    fieldtype: "HTML",
                    fieldname: "designer_container"
                }
            ]
        });

        dialog.$wrapper.addClass("flow-designer-modal");
        dialog.show();

        const $wrapper = dialog.get_field("designer_container").$wrapper;
        $wrapper.css({ width: "100%", height: "100%", display: "flex", flex: "1" });
        new FlowDesigner($wrapper, flowName, { dialog: dialog });
    };

})();
