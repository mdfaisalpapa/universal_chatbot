"""End-to-End Demonstration: Universal Chatbot connected to kvc3.local

Simulates:
1. User opening website chat widget.
2. Bot greeting user and prompting for flat number.
3. User responding with flat number "TB2-203".
4. Chatbot calling external ERPNext (kvc3.local) via Frappe REST Connector using encrypted credentials.
5. Bot formatting response with template interpolation and returning outstanding dues.
"""

import frappe
from universal_chatbot.api.v1.chat import init_chat, send_message


def run_demonstration():
    frappe.init("chatbot.local")
    frappe.connect()

    print("======================================================================")
    print(" UNIVERSAL CHATBOT -> KVC3.LOCAL END-TO-END DEMO")
    print("======================================================================")

    # 1. Ensure Bot Channel
    channel_name = "Website Channel"
    if not frappe.db.exists("Bot Channel", channel_name):
        channel = frappe.get_doc({
            "doctype": "Bot Channel",
            "channel_name": channel_name,
            "channel_type": "Web Widget",
            "is_enabled": 1,
        }).insert(ignore_permissions=True)
    else:
        channel = frappe.get_doc("Bot Channel", channel_name)

    # 2. Ensure Bot Deployment
    deployment_key = "kvc3_web_live_demo_key"
    existing_dep = frappe.db.get_value("Bot Deployment", {"deployment_key": deployment_key}, "name")
    if existing_dep:
        dep = frappe.get_doc("Bot Deployment", existing_dep)
        dep.status = "Active"
        dep.allowed_domains = "*"
        dep.chatbot = "kvc3_bot"
        dep.save(ignore_permissions=True)
    else:
        dep = frappe.get_doc({
            "doctype": "Bot Deployment",
            "deployment_name": "KVC3 Portal Assistant",
            "chatbot": "kvc3_bot",
            "channel": channel.name,
            "deployment_key": deployment_key,
            "status": "Active",
            "allowed_domains": "*",
        }).insert(ignore_permissions=True)

    frappe.db.commit()
    print(f"[*] Provisioned Deployment: {dep.name} (Key: {deployment_key})")

    external_user_id = "resident_tb2_203"

    # Step 1: User initiates conversation
    print("\n[Step 1] User opens widget and starts chat: 'How much maintenance is outstanding for my flat?'")
    print("         Simulating Web Channel Adapter request...")

    init_resp = init_chat(
        deployment_key=deployment_key,
        external_user_id=external_user_id,
    )
    conversation_id = init_resp["conversation_id"]
    print(f"         Session created: {conversation_id}")
    print(f"         Session status:  {init_resp.get('session_status')}")

    print("\n--- Outbound Bot Messages ---")
    for m in init_resp.get("messages", []):
        print(f"  [BOT] {m.get('text')}")

    # Step 2: User answers with flat number
    test_flat = "TB2-203"
    print(f"\n[Step 2] User inputs flat number: '{test_flat}'")
    print("         Sending normalized message via WebChannelAdapter...")

    msg_resp = send_message(
        deployment_key=deployment_key,
        external_user_id=external_user_id,
        conversation_id=conversation_id,
        message=test_flat,
    )
    print(f"         Session status: {msg_resp.get('session_status')}")

    print("\n--- Outbound Bot Messages ---")
    outbound_texts = []
    for m in msg_resp.get("messages", []):
        text = m.get("text", "")
        print(f"  [BOT] {text}")
        outbound_texts.append(text)

    # Verification
    print("\n======================================================================")
    print(" VERIFICATION & RESULTS (Owner Occupied Flat: TB2-203)")
    print("======================================================================")

    matched_header = any("the details for flat TB2-203:" in t for t in outbound_texts)
    matched_owner = any("👤 Owner: PRAVEEN KUMAR" in t for t in outbound_texts)
    matched_details = any("🏢 Details: B2 Block, 2 BHK, 1133 sqft" in t for t in outbound_texts)
    matched_tenant = any("👥 Tenant: None (Owner Occupied)" in t for t in outbound_texts)
    matched_amount = any("💰 Outstanding Dues: ₹ 2,940.00" in t for t in outbound_texts)

    print(f"[*] Response contains flat header: {matched_header}")
    print(f"[*] Response contains owner details: {matched_owner}")
    print(f"[*] Response contains flat details: {matched_details}")
    print(f"[*] Response contains tenant details: {matched_tenant}")
    print(f"[*] Response contains dues amount: {matched_amount}")

    # Verify Action Execution Log in DB
    action_log = frappe.get_all(
        "Action Execution",
        filters={"conversation": conversation_id},
        fields=["name", "action", "status", "execution_time", "input_payload", "output_payload"],
    )
    print(f"[*] Action Execution log created: {len(action_log) > 0}")
    if action_log:
        print(f"    - ID: {action_log[0]['name']}")
        print(f"    - Status: {action_log[0]['status']}")
        print(f"    - Duration: {action_log[0]['execution_time']}s")
        print(f"    - Input: {action_log[0]['input_payload']}")
        print(f"    - Output: {action_log[0]['output_payload'][:120]}...")

    assert (
        matched_header and matched_owner and matched_details and matched_tenant and matched_amount and action_log
    ), "TB2-203 verification failed"

    # Step 3: Test flat with active tenant (TA1-203)
    print("\n======================================================================")
    print(" [Step 3] Testing Flat with Active Tenant: TA1-203")
    print("======================================================================")
    user_tenant = "resident_ta1_203"
    init_resp_t = init_chat(
        deployment_key=deployment_key,
        external_user_id=user_tenant,
    )
    conv_t = init_resp_t["conversation_id"]
    msg_resp_t = send_message(
        deployment_key=deployment_key,
        external_user_id=user_tenant,
        conversation_id=conv_t,
        message="TA1-203",
    )
    outbound_t = [m.get("text", "") for m in msg_resp_t.get("messages", [])]
    for text in outbound_t:
        print(f"  [BOT] {text}")

    matched_t_header = any("the details for flat TA1-203:" in t for t in outbound_t)
    matched_t_owner = any("👤 Owner: B BALAJI" in t for t in outbound_t)
    matched_t_details = any("🏢 Details: A1 Block, 1 BHK, 579 sqft" in t for t in outbound_t)
    matched_t_tenant = any("👥 Tenant: Mr. Devilal Reddy (Active)" in t for t in outbound_t)
    matched_t_amount = any("💰 Outstanding Dues: ₹ 1,555.00" in t for t in outbound_t)

    print(f"[*] Response contains flat header: {matched_t_header}")
    print(f"[*] Response contains owner details: {matched_t_owner}")
    print(f"[*] Response contains flat details: {matched_t_details}")
    print(f"[*] Response contains tenant details: {matched_t_tenant}")
    print(f"[*] Response contains dues amount: {matched_t_amount}")

    assert (
        matched_t_header and matched_t_owner and matched_t_details and matched_t_tenant and matched_t_amount
    ), "TA1-203 verification failed"

    print("\n[SUCCESS] Both Owner-Occupied and Tenant-Occupied scenarios passed completely!")
    print("          All expanded fields (Owner, Details, Tenant, Dues) retrieved and formatted properly.")


if __name__ == "__main__":
    run_demonstration()
