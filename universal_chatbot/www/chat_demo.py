import frappe


def get_context(context):
    context.no_cache = 1
    deployment_key = frappe.form_dict.get("deployment_key")
    if not deployment_key:
        deployment = frappe.db.get_value("Bot Deployment", {"status": "Active"}, ["name", "deployment_key"], as_dict=True)
        if deployment:
            deployment_key = deployment.deployment_key

    context.deployment_key = deployment_key or "demo_key"
