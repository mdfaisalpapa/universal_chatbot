"""Multiple Choice node implementation."""

from typing import Any, Dict, List
from universal_chatbot.flow.base import BaseFlowNode, NodeExecutionContext, NodeResult
from universal_chatbot.flow.evaluator import interpolate_template
from universal_chatbot.flow.registry import register_node


@register_node("Multiple Choice")
class MultipleChoiceNode(BaseFlowNode):
    """Presents user with multiple options and pauses flow until selection."""

    def execute(self, context: NodeExecutionContext) -> NodeResult:
        prompt_text = self.config.get("prompt") or self.config.get("text", "Please select an option:")
        rendered = interpolate_template(prompt_text, context.variables)

        # Support static options list or dynamic options variable (e.g. options_variable="menu_res.unpacked.data.options")
        raw_options = self.config.get("options", [])
        opt_var = self.config.get("options_variable")
        if opt_var:
            curr = context.variables
            for part in opt_var.split("."):
                if isinstance(curr, dict):
                    curr = curr.get(part)
                else:
                    curr = None
                    break
            if isinstance(curr, list):
                raw_options = curr

        rendered_options = []
        for opt in raw_options:
            label = interpolate_template(opt.get("label", ""), context.variables)
            val = opt.get("value") or opt.get("action") or label
            opt_dict = {"label": label, "value": val}
            if opt.get("url"):
                opt_dict["url"] = interpolate_template(opt["url"], context.variables)
            if opt.get("web_app_url"):
                opt_dict["web_app_url"] = interpolate_template(opt["web_app_url"], context.variables)
            if opt.get("request_contact"):
                opt_dict["request_contact"] = True
            rendered_options.append(opt_dict)

        msg = {
            "type": "options",
            "text": rendered,
            "options": rendered_options,
        }
        return NodeResult.pause_flow(outgoing_messages=[msg])

    def resume(self, context: NodeExecutionContext) -> NodeResult:
        save_var = self.config.get("save_to_variable") or self.config.get("variable_name", "user_choice")
        user_input = ""
        if context.incoming_message:
            msg_data = context.incoming_message.message or {}
            user_input = str(msg_data.get("text", "")).strip()

        # Support static or dynamic options
        raw_options = self.config.get("options", [])
        opt_var = self.config.get("options_variable")
        if opt_var:
            curr = context.variables
            for part in opt_var.split("."):
                if isinstance(curr, dict):
                    curr = curr.get(part)
                else:
                    curr = None
                    break
            if isinstance(curr, list):
                raw_options = curr

        matched_value = user_input
        matched_target_node = None

        # If user shared a contact or phone number, match any request_contact option
        has_shared_phone = bool(context.incoming_message and context.incoming_message.message.get("phone_number"))

        for opt in raw_options:
            if has_shared_phone and opt.get("request_contact"):
                matched_value = opt.get("action") or opt.get("value") or "share_contact"
                matched_target_node = opt.get("target_node")
                break
            val = str(opt.get("value") or opt.get("action") or "").strip()
            lbl = str(opt.get("label", "")).strip()
            if user_input.lower() in (val.lower(), lbl.lower()):
                matched_value = val
                matched_target_node = opt.get("target_node")
                break

        updates = {save_var: matched_value}
        return NodeResult.continue_flow(
            variable_updates=updates,
            next_node_override=matched_target_node,
        )
