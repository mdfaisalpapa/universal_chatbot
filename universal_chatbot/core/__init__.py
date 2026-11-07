"""Core domain module for Universal Chatbot.

Strict Architectural Rule:
Modules within `core/`, `flow/`, `channels/`, and `connectors/` must NEVER
import `frappe`. Persistence and Frappe-specific interactions are handled
strictly via adapters.
"""
