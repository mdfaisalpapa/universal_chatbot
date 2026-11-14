UNIVERSAL CHATBOT
Project Blueprint and Technical Architecture
Version 1.0Target framework: Frappe v16Deployment model: Hybrid — self-hosted and centrally hostedInitial integration model: API-first
Document purpose
This document consolidates the agreed vision, architecture, functional scope, data model, security principles, deployment strategy and implementation roadmap for Universal Chatbot. It is intended to serve as the baseline specification for implementation.
1. Project Vision
Universal Chatbot will be a configurable, reusable chatbot platform capable of operating across multiple communication channels and connecting to different business applications and databases. A chatbot configured once should be deployable across multiple channels, with channel-specific presentation handled by adapters.
1.1 Design objectives
Platform-independent chatbot engine.
Channel-independent conversation logic.
Reusable integrations with external applications.
Visual conversation-flow designer.
Optional AI capabilities.
Secure access to external business data.
Self-hosted and centrally hosted deployment.
Multi-tenant architecture for hosted deployments.
Extensible architecture for future channels and connectors.
Configuration portability between installations.
2. Architectural Principles
Separate the engine from Frappe
Frappe provides administration, configuration, persistence and management interfaces. Conversation and flow execution logic remain independent of Frappe.
Separate channels from conversation logic
Channel adapters normalize incoming messages and translate standard responses back into channel-specific payloads.
API-first integrations
External applications are accessed through controlled APIs initially; direct database access is not required.
AI is optional
Rule-based conversations must work without an AI provider. AI is an additional capability, not a mandatory dependency.
Security by design
Only predefined, validated and permission-controlled actions may execute. AI must not execute arbitrary Python, SQL or application code.
Modular monolith initially
Start with clearly separated modules in one application. Split services only when operational scale justifies it.
3. High-Level Architecture
The system consists of four principal layers:
Layer
Responsibilities / Components
Communication channels
Website widget, WhatsApp, Telegram, mobile applications and external API clients.
Channel Gateway
Receives messages, identifies bot and deployment, validates requests and normalizes channel payloads.
Conversation Engine
Conversation and session management, flow execution, intent resolution, AI orchestration, action execution, permission validation and response dispatch.
Connector Framework
Frappe/ERPNext REST connector, generic REST connector and future database or custom connectors.
External systems
ERPNext, CRM, educational management systems, apartment management systems and other business applications.
The Frappe administration application provides the management interface for bots, channels, flows, integrations, AI settings, conversations and analytics.
3.1 Message lifecycle
A channel adapter receives a user message.
The Channel Gateway validates the request and converts it to the common protocol.
The Conversation Engine identifies the bot, contact, conversation and active flow.
The Flow Engine executes nodes and invokes permitted actions when required.
The Connector Framework communicates with the external business system.
The engine returns a standard response; the channel adapter formats and sends it.
4. Core Application Components
4.1 Core Conversation Engine
Receives normalized messages; identifies bots and conversations; maintains session state; executes flows; invokes configured actions; generates responses; and returns results to channel adapters. It must not depend directly on Frappe DocTypes or channel-specific libraries.
4.2 Channel Adapter Framework
Each channel has a separate adapter implementing common operations such as receive_message(), send_message(), validate_webhook(), normalize_message() and format_response(). Initial channel: website. WhatsApp and Telegram follow in Phase 2.
4.3 Connector Framework
Connectors expose a common interface for testing connections, listing available actions, validating parameters and executing permitted operations.
4.4 AI Orchestrator
A provider-independent layer for intent classification, natural-language response generation, entity extraction, knowledge retrieval and AI-assisted configuration. AI may select only from configured and authorised actions.
Illustrative connector interface:
class BaseConnector:    def test_connection(self):        raise NotImplementedError    def get_available_actions(self):        raise NotImplementedError    def validate_parameters(self, action, parameters):        raise NotImplementedError    def execute(self, action, parameters, context):        raise NotImplementedError
5. Bot Configuration and Deployment Model
A bot is independent of the channel on which it operates. One bot may be deployed on a website, WhatsApp, Telegram and a mobile application while sharing conversation flows and business integrations.
Entity / DocType
Purpose and principal fields
Chatbot
Logical chatbot: Bot Name, Bot Code, Description, Status, Default Language, Welcome Message, Default Flow and Fallback Message.
Bot Deployment
Deployment instance: Bot, Deployment Name, Deployment Type, Site or Domain, Environment and Status.
Bot Channel
Channel association: Bot, Deployment, Channel Type, Provider, Account Reference and Status.
Bot Settings
Operational settings: AI Enabled, Flow Mode, Session Timeout, Fallback Message, Language and Human Handover settings.
Bot Version
Published configuration snapshot: Bot, Version, Configuration Snapshot, Published By, Published On and Status.
Published configuration must be versioned so that changes do not unexpectedly alter conversations already running against an earlier published version.
6. Conversation Management
DocType
Purpose / fields
Chat Contact
Represents a person or external contact; Display Name and Contact Status.
Channel Identity
Maps an external identity to a contact; Contact, Channel, External User ID and Verification Status.
Chat Conversation
Bot, Deployment, Contact, Channel, Status, Started At and Last Activity.
Chat Message
Conversation, Direction, Message Type, Content, External Message ID, Status and Timestamp.
Conversation State
Conversation, Current Node, Variables, Context and Active Flow Version.
Conversation Event
Records conversation start, flow start, node execution, action execution, handover, closure and errors.
Identity linking across channels must be explicit and verified. Contacts must not be merged merely because their names or phone numbers appear similar. Conversation history must follow configurable retention policies.
7. Visual Flow Builder
The visual flow builder allows administrators to configure conversations without writing code. A flow is represented as connected nodes with defined transitions.
Initial node
Purpose
Start
Starts the conversation.
Send Message
Sends text or another supported message.
Ask Question
Requests information from the user.
Multiple Choice
Displays predefined choices.
Condition
Evaluates a condition and branches.
Set Variable
Creates or updates a variable.
Call Action
Executes a configured integration action.
AI Response
Generates an AI-assisted response.
End
Ends the conversation.
Later node types may include human handover, delay, loops, subflows, file/media handling and approval workflows.
Flow DocType
Principal fields
Chatbot Flow
Bot, Flow Name, Version, Status and Description.
Flow Node
Flow, Node ID, Node Type and Configuration.
Flow Transition
Source Node, Target Node and Condition.
Flow Variable
Flow, Variable Name, Data Type and Default Value.
Flow Execution
Conversation, Flow, Current Node, Status and Execution Context.
7.1 Flow execution
Receive a message and identify the active conversation.
Load the current flow state and published flow version.
Execute the current node and evaluate its transition.
Continue through eligible nodes and prepare the response.
Persist the updated conversation state.
Pause safely when waiting for user input and resume on the next message.
Published flows must be validated before activation and stored in a structured, versioned format.
8. Common Message Protocol
All channels communicate with the engine through a common message protocol. Channel-specific payload structures remain inside their respective adapters.
8.1 Incoming message example
{  "tenant_id": "customer_001",  "bot_id": "dreambig_assistant",  "deployment_id": "website_prod",  "channel": "web",  "external_user_id": "visitor_123",  "conversation_id": "conv_00001",  "message": {    "message_id": "msg_001",    "type": "text",    "text": "What courses are available?"  },  "metadata": {    "language": "en",    "timezone": "Asia/Kolkata"  }}
8.2 Outgoing response example
{  "conversation_id": "conv_00001",  "response": {    "type": "text",    "text": "We offer the following courses..."  },  "actions": [],  "session_status": "active"}
The initial implementation supports text. The protocol should accommodate images, documents, audio, video, buttons, lists, location, interactive forms and voice messages.
9. Integration and Action Framework
DocType
Purpose / fields
Chatbot Integration
Integration Name, Integration Type, Base URL and Status.
Integration Credential
Integration, Authentication Type and encrypted credentials.
Integration Action
Action Name, Integration, Operation, Input Schema, Output Mapping, Permission Requirement and Confirmation Required.
Action Execution
Action, Conversation, Input, Output, Status and Execution Time.
Integration Environment
Integration, Environment and Endpoint.
9.1 Example configured action
{  "action_name": "get_maintenance_dues",  "connector": "kvc3_erpnext",  "operation": "get_maintenance_dues",  "method": "POST",  "parameters": {    "flat_number": {      "type": "string",      "required": true    }  },  "authentication": "verified_resident",  "permission": "view_own_maintenance",  "confirmation_required": false}
9.2 Integration security
Encrypt credentials and never expose API tokens to browser clients.
Execute only configured actions and validate parameters against schemas.
Validate external API responses before using them.
Require authorisation for sensitive actions and explicit confirmation for financial or irreversible actions.
Log action executions and errors without unnecessarily recording sensitive information.
9.3 Future direct database integration
Direct SQL connectors for MySQL and PostgreSQL are deferred to a later phase. They should use read-only credentials by default, allowlisted tables or views, parameterised queries, restricted permissions, timeouts, result limits and audit logging. Unrestricted AI-generated SQL must never be executed. Controlled application APIs remain preferred for write operations.
10. AI Architecture
AI DocType
Purpose / fields
AI Provider
Provider, Endpoint, Model and Status.
AI Configuration
Provider, Model, Temperature, System Instructions and Token Limits.
Knowledge Source
Source Type, Location and Status.
Knowledge Document
Source, File and Processing Status.
AI Prompt Template
Prompt Name, Template and Version.
AI Usage Log
Provider, Model, Tokens, Cost and Timestamp.
Planned capabilities include intent classification, parameter extraction, contextual responses, knowledge-base search, summarisation and AI-assisted flow configuration.
AI must not bypass flow permissions or application access controls. For example, a resident requesting maintenance dues must be verified and authorised before the external ERPNext action runs.
11. Security and Access Control
Potential security and operations components include Bot Access Policy, Bot User Mapping, Human Handover, Webhook Endpoint, Webhook Event, API Client and Bot Analytics. Some may initially be child tables or settings.
11.1 Security requirements
Authenticate incoming webhooks and validate provider signatures where supported.
Use secure API authentication and encrypted integration credentials.
Apply role-based access control and server-side tenant isolation.
Validate all external inputs and apply rate limits.
Prevent replay attacks where applicable.
Audit sensitive operations and avoid exposing confidential information in logs.
Define data-retention and deletion policies.
11.2 Multi-tenant security
For central hosting, every tenant-owned record must be associated with a tenant. Isolation must cover bots, conversations, contacts, messages, integrations, credentials, knowledge sources and analytics. Enforcement must occur on the server, not merely through interface filtering.
12. Proposed Application Structure
Universal Chatbot will be an independent Frappe application named universal_chatbot. It must not be embedded within society_erp, dreambig_egs or another business-specific application.
universal_chatbot/├── pyproject.toml├── universal_chatbot/│   ├── core/│   │   ├── engine.py│   │   ├── dispatcher.py│   │   ├── session_manager.py│   │   ├── conversation.py│   │   ├── message.py│   │   ├── state_manager.py│   │   └── event_bus.py│   ├── flow/│   │   ├── parser.py│   │   ├── validator.py│   │   ├── executor.py│   │   ├── transitions.py│   │   └── nodes/│   ├── channels/│   │   ├── base.py│   │   ├── registry.py│   │   ├── web/│   │   ├── whatsapp/│   │   └── telegram/│   ├── connectors/│   │   ├── base.py│   │   ├── registry.py│   │   ├── frappe/│   │   └── rest/│   ├── ai/│   │   ├── orchestrator.py│   │   ├── providers/│   │   ├── prompts.py│   │   └── knowledge/│   ├── actions/│   │   ├── registry.py│   │   ├── executor.py│   │   └── permissions.py│   ├── api/│   ├── doctype/│   ├── public/│   │   ├── js/│   │   ├── css/│   │   └── widget/│   ├── templates/│   ├── hooks.py│   └── install.py└── tests/
This is the target structure. Directories for future channels and AI providers will be populated in later phases. The core, flow, channels and connectors modules must not import Frappe directly; Frappe-specific persistence and administration should be implemented through adapters.
13. Hybrid Deployment Architecture
13.1 Self-hosted deployment
Customer installs the application on their own Frappe site.
Customer controls the application and database.
Conversations and configuration remain within the customer's environment.
The application connects to messaging providers and external systems.
13.2 Central hosted deployment
Central administration and runtime serving multiple tenants.
Tenant-specific bots, configurations, credentials and integrations.
Tenant-specific usage limits, quotas and billing.
Explicit isolation of conversations, knowledge and analytics.
The central platform must enforce tenant isolation even where multiple tenants share one Frappe site.
13.3 Future private-network connector agent
A future agent may run inside a customer's network and establish an outbound authenticated connection to the central chatbot service. This avoids requiring public exposure of private ERPNext instances. It is not part of Phase 1.
14. Phase 1 — Initial Implementation
14.1 Objective
Deliver a working configurable chatbot on a website that conducts rule-based conversations and retrieves information from a separate ERPNext installation through REST APIs.
14.2 Included scope
Independent Frappe application and initial DocTypes.
Bot configuration and conversation management.
Common message protocol and basic conversation engine.
Rule-based flow engine and basic visual flow designer.
Embeddable website chat widget.
Frappe REST and generic REST connectors.
Basic authentication, security and configuration versioning/export.
14.3 Excluded from Phase 1
WhatsApp and Telegram integrations.
Production multi-tenant central hosting.
Advanced AI and knowledge-base capabilities.
Direct SQL database connectors.
Private-network connector agent.
Full human operator dashboard and advanced analytics/billing.
The architecture must allow these capabilities to be added without redesigning the core engine.
15. Phase 1 Development Milestones
Version
Milestone
Deliverable
v0.1
Application foundation
Installable Frappe app and initial DocTypes.
v0.2
Conversation engine
Common message protocol and persistent conversations.
v0.3
Flow engine
Rule-based execution and conditional branches.
v0.4
Website widget
Embeddable chatbot interface.
v0.5
ERPNext connector
Secure external API integration.
v0.6
Visual flow designer
Graphical flow creation and editing.
v0.7
Security and testing
Tested Phase 1 release.
Milestone 1 — Application foundation
Create an independent Git repository and Frappe application.
Establish the module structure and initial DocTypes.
Configure roles, permissions and automated tests.
Milestone 2 — Conversation engine
Implement common message classes, conversation/session management and persistence.
Implement conversation state management and incoming-message APIs.
Milestone 3 — Flow engine
Implement parser, node registry, node execution and transitions.
Implement conditions, variables and flow validation.
Milestone 4 — Website widget
Develop a standalone JavaScript widget and embed script.
Connect to chatbot APIs and preserve conversation identity across refreshes.
Support basic text interaction.
Milestone 5 — External ERPNext connector
Configure external ERPNext connections and API authentication.
Define available actions, validate inputs and execute actions securely.
Handle errors and timeouts.
Milestone 6 — Visual flow designer
Develop graphical flow editing, node connections and property configuration.
Validate flow structure and publish flow versions.
Milestone 7 — Security and testing
Test authentication, permissions, conversation isolation and external API security.
Test multiple bots, flow versioning, installation and upgrades.
Document deployment and configuration.
16. Development and Testing Environment
Site
Purpose
chatbot.local
Hosts Universal Chatbot.
customer.local
Simulates a separate customer ERPNext system.
demo.local
Optional independent website hosting the widget.
16.1 Demonstration scenario
A visitor asks: "How much maintenance is outstanding for my flat?"
The chatbot asks for the flat number and required verification information.
The resident is verified through the external ERPNext system.
The chatbot calls the configured maintenance-dues action.
The external system returns permitted information.
The chatbot displays the outstanding amount and saves the conversation history.
Use sample or test data during development.
17. Phase 1 Acceptance Criteria
Installs on a clean Frappe v16 site.
Supports multiple independent bots and flows.
Deploys a bot to a website.
Persists conversations across browser refreshes.
Executes conditional branches correctly.
Embeds on a non-Frappe website.
Connects to a separate ERPNext installation.
Never exposes external API credentials to the browser.
Controls integration actions through permissions.
Isolates conversations and bot configurations appropriately.
Supports versioning and export of flow configurations.
Preserves existing configurations during application upgrades.
18. Future Development Roadmap
Phase
Scope
Phase 2 — Omnichannel and AI
WhatsApp, Telegram, mobile API, AI provider framework, intent recognition, AI responses, knowledge base, human handover and operator dashboard.
Phase 3 — Advanced integrations
MySQL/PostgreSQL connectors, custom connector SDK, private-network connector agent, advanced workflow nodes, approvals and event-triggered conversations.
Phase 4 — Hosted platform
Central multi-tenant administration, tenant provisioning, subscriptions, usage management, billing, quotas, monitoring and enterprise deployment options.
19. Key Technical Decisions
Area
Agreed baseline
Framework
Frappe v16
Application
Independent universal_chatbot app
Architecture
Modular monolith
Core engine
Platform-independent Python
Deployment
Hybrid
Initial integration
API-first
Flow configuration
Visual builder; AI-assisted configuration later
Initial channel
Website
Initial connectors
Frappe REST and Generic REST
AI
Optional; Phase 2
WhatsApp / Telegram
Phase 2
Direct SQL
Phase 3
Central multi-tenancy
Future hosted-platform phase
Configuration portability
Versioned and exportable
20. Implementation Strategy and Guiding Principles
Do not introduce business-specific logic into the universal chatbot core.
Do not make the core engine dependent on Frappe.
Do not mix channel-specific payloads with the common message protocol.
Do not introduce microservices prematurely.
Do not implement direct database access before the API connector framework is stable.
Do not make AI a mandatory dependency.
Do not allow AI to bypass configured permissions and actions.
Do not expose integration credentials to browser clients.
Keep the application independently installable and upgradeable.
Maintain automated tests for the core engine and flow execution.
Preserve compatibility with both self-hosted and centrally hosted deployment.
Protect configuration and conversation data during application upgrades.
Immediate Next Step
Begin Milestone 1 by verifying the existing Frappe v16 development bench, creating the independent universal_chatbot application and Git repository, establishing the initial application structure, defining and creating the first DocTypes, installing the application on chatbot.local, and verifying installation before proceeding to the conversation engine.
— End of Project Blueprint —
PHASE 2, 3 AND 4
Detailed Functional Blueprint, Technical Design and Delivery Roadmap
Universal Chatbot | Extension to Project Blueprint Version 1.0
Target: Frappe v16 • Hybrid deployment • API-first integration • Modular monolith
Document control and interpretation
This is a continuation and expansion of the Phase 1 baseline. The original Phase 1 content is retained above. This addendum defines the intended scope, architecture extensions, DocTypes, workflows, security controls, milestones, dependencies and acceptance criteria for Phases 2–4. It is a product and engineering blueprint, not a commitment to a fixed calendar or a substitute for detailed sprint-level design.
The platform remains an independent Frappe application named universal_chatbot. Phase 2–4 features must extend the common message protocol, channel adapter contract, connector contract and published configuration model. Business-specific logic must remain in customer applications or connector implementations.
1. Overall roadmap and phase boundaries
Phase
Primary outcome
Major capabilities
Exit condition
Phase 1 (baseline)
Working website chatbot foundation
Core engine, rule-based flows, website widget, REST connectors, visual flow builder, basic security
A customer can install the app, publish a website bot and securely call an external ERPNext API.
Phase 2
Production omnichannel + practical AI
WhatsApp, Telegram, public/mobile API, AI providers, intent/entity extraction, knowledge base, human handover and operator console
One bot works consistently across multiple channels with controlled AI, searchable knowledge and human escalation.
Phase 3
Enterprise integration and workflow automation
SQL read connectors, connector SDK, private-network agent, advanced nodes, approvals, event-triggered outbound conversations
The platform can safely orchestrate complex business processes and connect to private/on-premise systems.
Phase 4
Commercial hosted SaaS platform
Tenant provisioning/isolation, plans, subscriptions, quotas, usage metering, billing, platform operations and enterprise deployment options
A centrally hosted service can onboard, isolate, meter, support and bill multiple customer organisations.
2. Cross-phase architectural rules
Keep the conversation engine and flow runtime framework-independent. Frappe remains the administration, persistence and management layer.
Use a modular monolith through Phase 3. Extract a worker, gateway or connector service only when measured throughput, isolation or deployment requirements justify it.
All channel adapters translate provider payloads into the common protocol. No channel-specific field or SDK object should leak into flow definitions.
All integrations execute through registered connectors and allowlisted actions. AI may recommend an action but cannot invent or execute one.
Published bot versions are immutable snapshots. Draft edits do not mutate live conversations; deployments can pin a version or move through a controlled release.
Use asynchronous jobs for slow provider calls, media processing, AI inference, outbound campaigns, webhook retries and event delivery.
Every tenant-scoped operation must enforce tenant identity server-side. UI filters are not a security boundary.
Prefer idempotent processing, bounded retries, dead-letter handling and correlation IDs for all inbound/outbound events.
PHASE 2 — Omnichannel and AI capabilities
3. Phase 2 objectives and scope
Phase 2 turns the Phase 1 website chatbot into a practical multi-channel assistant. It adds messaging channels and AI capabilities while preserving deterministic flows and permission-controlled actions. The aim is not to make every conversation AI-driven; administrators must be able to choose rule-based, AI-assisted or hybrid behaviour per bot, flow or node.
Add WhatsApp Business Platform and Telegram as production channel adapters, subject to provider account approval and policy compliance.
Provide a stable public API for mobile applications and other first-party clients; a native mobile application itself is not included.
Introduce provider-neutral AI orchestration with at least one configurable provider implementation and a provider abstraction for additional providers.
Add intent classification, entity extraction, controlled AI responses, knowledge retrieval and AI-assisted flow authoring.
Provide human handover, agent assignment, operator inbox, internal notes, canned replies and conversation closure.
Add channel-aware message templates, delivery status, media metadata, retry handling, opt-in/opt-out and analytics.
4. Phase 2 channel architecture
Each channel adapter implements a common interface and owns provider-specific authentication, webhook verification, payload parsing, rate limits, message formatting and delivery receipts. The gateway resolves the Bot Deployment and tenant before dispatching a normalized message to the engine.
Channel
Inbound mechanism
Outbound mechanism
Phase 2 requirements
WhatsApp
Meta webhook callback
WhatsApp Cloud API
Webhook signature/token verification, phone-number/business-account mapping, approved templates for business-initiated messages, 24-hour customer-service window handling, media, delivery/read/failure statuses, opt-in and opt-out.
Telegram
Bot webhook (polling only for local development if needed)
Telegram Bot API
Webhook secret token, bot token encryption, chat/user identity mapping, text, buttons, callback queries, media references, rate-limit handling.
Mobile / public API
Authenticated HTTPS API
Synchronous response or WebSocket/SSE/polling contract
API client credentials, scoped tokens, conversation resume, push-event hook, pagination and versioned API.
Website (enhancement)
Existing widget gateway
Existing widget transport
Typing/agent status, attachments, reconnect, accessibility, consent and channel continuity where identity is verified.
4.1 WhatsApp message lifecycle
Meta sends an HTTPS webhook event to the registered endpoint.
Adapter verifies the webhook challenge or request signature/token as applicable and stores the raw event reference with minimal sensitive data.
Gateway deduplicates by provider event/message ID and resolves the channel account, deployment, bot and tenant.
Adapter normalizes text, media, interactive replies, contacts and timestamps into the common message protocol.
Conversation engine resumes or creates the conversation and applies contact identity and consent rules.
Flow/AI processing produces a channel-neutral response. The WhatsApp adapter checks message-window and template constraints before sending.
Outbound message ID and delivery status are recorded; provider callbacks update message status asynchronously.
4.2 Delivery reliability
Persist inbound events before acknowledging webhooks where practical; process through a queue.
Use unique provider event IDs and idempotency keys to prevent duplicate conversations and duplicate business actions.
Retry transient failures with exponential backoff and jitter; do not retry permanent policy or validation failures indefinitely.
Provide a dead-letter queue and administrative replay tool with permission checks.
Track accepted, queued, sent, delivered, read, failed and expired states separately.
5. Phase 2 AI architecture
Add an AI Orchestrator between the Conversation Engine and model providers. It is a policy-enforcing broker, not an unrestricted agent. Provider adapters normalize model requests, responses, token usage, errors and supported capabilities.
AI capability
Behaviour and control
Intent classification
Map user utterance to configured intents; return confidence and candidate intent. Low confidence routes to clarification or fallback.
Entity extraction
Extract typed fields (flat number, invoice number, course, date, etc.) against a declared schema. Validate and confirm critical values.
AI response
Generate natural-language responses using approved system instructions, conversation context and permitted retrieved content.
Knowledge retrieval (RAG)
Retrieve relevant chunks from approved knowledge sources, apply tenant/bot filters and provide grounded answers with source references where configured.
AI flow assistance
Suggest flow nodes, transitions, prompts and test cases in draft mode. Human administrator reviews and publishes.
Tool/action selection
AI may select only from the actions exposed to the current bot and user context. Server-side permission checks and parameter validation are mandatory before execution.
5.1 AI execution policy
AI is optional and can be disabled globally, per tenant, bot, deployment, flow or node.
Never execute model-generated Python, JavaScript, shell commands or arbitrary SQL.
Never let model output set tenant ID, verified identity, roles, permissions or credential values. These are trusted server-side context only.
Require explicit confirmation for payments, financial commitments, account changes, destructive operations and other irreversible actions.
Use structured output schemas for intent, entities and tool selection; reject malformed or out-of-policy output.
Apply per-provider timeout, token limit, concurrency limit, retry policy, spend limit and fallback behaviour.
Treat retrieved documents and user messages as untrusted input; defend against prompt injection and data exfiltration.
6. Knowledge base and retrieval
Knowledge Base supports tenant- and bot-scoped information that the chatbot may use to answer questions. Phase 2 should start with uploaded documents and curated URLs or text sources. More complex enterprise repositories can be added later.
Component / DocType
Key fields / responsibility
Knowledge Source
Tenant, Bot, Source Type (upload/URL/text/API), Source Name, location, refresh schedule, status, access scope, last indexed time.
Knowledge Document
Source, original file/reference, title, MIME type, checksum, language, processing status, error, version.
Knowledge Chunk
Document, chunk index, text, token estimate, metadata, embedding reference, access labels.
Knowledge Index Job
Source/document, job type, status, attempts, started/completed timestamps, error summary.
Retrieval Policy
Bot, allowed sources, minimum relevance, maximum chunks, citation mode, fallback behaviour, retention rules.
Ingestion pipeline: validate file/type/size → extract text → normalize → split into chunks → generate embeddings → store index → publish index version.
Maintain source checksums and re-index only changed content. Support disable, delete and reprocess operations.
Enforce tenant, bot and document-level access filters before retrieval, not after the model receives content.
Return source metadata to the response renderer where citations or “source” links are enabled.
Define retention and deletion propagation for original files, extracted text, chunks and embeddings.
7. Human handover and operator console
Human handover pauses automated execution at a defined point and transfers the conversation to a queue or assigned agent. The conversation remains associated with its channel and can resume automation when the agent closes or returns it.
DocType
Purpose / principal fields
Handover Queue
Tenant, queue name, skills/tags, business hours, assignment strategy, overflow behaviour.
Agent Profile
User, availability, skills, max concurrent conversations, channel permissions.
Conversation Assignment
Conversation, queue, assigned agent, assigned by, assigned at, accepted at, closed at.
Handover Event
Conversation, reason, source node, status, actor, timestamps, resolution code.
Internal Note
Conversation, author, note, visibility, timestamp; never sent to customer.
Canned Response
Tenant, team, shortcut, content, channel compatibility, language.
Operator inbox filters: unassigned, mine, waiting, escalated, overdue and closed.
Agent actions: accept, assign, transfer, reply, add internal note, attach supported media, resolve and resume bot.
Show contact verification level and allowed customer context; do not expose unrestricted ERP records.
Define business hours, SLA timers, queue capacity, reassignment on agent absence and escalation rules.
Maintain a complete audit trail of assignment and operator actions.

---

## 7.1 Glific-Parity Capabilities: Broadcast Campaigns, Form Collection & Funnel Analytics

To provide comprehensive feature parity with modern two-way communication platforms like Glific while maintaining enterprise ERP governance, Phase 2 incorporates three specialized operational engines:

### A. Targeted Broadcast & Outbound Campaign Manager
While Universal Chatbot explicitly avoids serving as an unsolicited bulk spam engine, transactional and community broadcasts are essential for enterprise operations (e.g., emergency water outages, AGM election notifications, invoice dues alerts).

* **DocType: `Chatbot Broadcast Campaign`**
  - **Fields**: `campaign_name`, `channel` (Telegram/WhatsApp), `template` (Meta-approved HSM or Telegram message template), `status` (Draft, Scheduled, In Progress, Completed, Failed), `scheduled_time`, `rate_limit_per_second`, `total_recipients`, `delivered_count`, `read_count`, `failed_count`.
  - **Audience Segmentation**: Directly queries Frappe DocTypes (e.g., `tabOwners` where dues > 0, `tabTenants` where agreement expires in 30 days) or accepts static recipient lists.
  - **Guardrails**: Strictly honors `Channel Consent` opt-ins/opt-outs, WhatsApp 24-hour service conversation windows, and automated queuing via background Redis workers (`frappe.enqueue`) to prevent telecom rate-limit bans.

### B. Multi-Field Structured Form Collection Engine
To eliminate the friction of chaining multiple sequential `Ask Question` nodes for complex registrations, Phase 2 introduces a dedicated form collection module:

* **Node Type: `Form Collection`**
  - **Fields**: Configures a JSON schema of multiple required fields (e.g., `first_name`, `flat_no`, `vehicle_reg`, `id_proof_file`).
  - **Capabilities**: Captures sequential inputs, validates regex/field types, supports photo/document file attachments, and on final step upserts directly into target ERP DocTypes (e.g., `Vehicle`, `Maintenance Ticket`, `Family Member`).
  - **In-Chat Interactive Forms**: For WhatsApp, leverages native WhatsApp Flow Forms; for Telegram, utilizes Telegram WebApps with pre-filled state.

### C. Drop-off & Conversational Funnel Analytics
Comprehensive visibility into user journeys, drop-offs, and service usage:

* **DocType: `Chatbot Analytics Snapshot`**
  - **Funnel Tracking**: Tracks node progression (`start_node` -> `main_menu_node` -> `service_card` -> completion) to pinpoint exact drop-off steps.
  - **Key Metrics**:
    - **Session Metrics**: Total conversations, active sessions, abandonment rate, resolution rate.
    - **Authentication Funnel**: New visitor conversion, 1-click Contact Sharing success rate vs unlinked abandonment.
    - **Feature Popularity**: Heatmap of most executed services (Dues, Gate Pass, Tickets, Financials).
    - **Operator Benchmarks**: Average response time, queue wait time, resolution time for Human Handover conversations.

---

8. Phase 2 additional DocTypes
DocType
Key fields / purpose
Channel Account
Channel, provider, account/business ID, encrypted token reference, webhook configuration, status, verification state.
Channel Event
Provider event ID, channel account, received time, processing state, retry count, payload reference, error code.
Channel Message Template
Provider template ID, language, category, components, approval status, variable schema.
Channel Consent
Contact, channel identity, purpose, opt-in source/time, opt-out time, evidence and status.
AI Provider
Provider key, endpoint, supported capabilities, status, region, data-processing settings.
AI Model Configuration
Provider, model, limits, temperature, timeout, allowed bots/tenants, fallback model.
AI Policy
Allowed tasks, allowed actions, content restrictions, data handling, confidence thresholds.
AI Request Log
Tenant, bot, conversation, provider/model, task, tokens, latency, cost estimate, status; redact sensitive content.
Knowledge Source / Document / Chunk
As defined in the knowledge-base section.
Handover Queue / Agent Profile / Assignment
As defined in the operator-console section.
Chatbot Broadcast Campaign / Audience Segment
As defined in the broadcast campaign section.
Chatbot Analytics Snapshot
As defined in the analytics and funnel tracking section.
9. Phase 2 implementation milestones
Milestone
Deliverables
Exit test
2.1 Channel framework hardening
Adapter registry, webhook gateway, channel account management, event queue, idempotency
A test adapter can receive, normalize, dispatch and send without changing core engine code.
2.2 Telegram adapter
Webhook setup, identity mapping, text/buttons/media, delivery/error handling
End-to-end Telegram bot conversation with restart/resume and duplicate-event tests.
2.3 WhatsApp adapter
Meta Cloud API, webhook verification, templates, 24-hour window, media and status callbacks
Test number and approved production account can send/receive while respecting provider rules.
2.4 AI provider framework
Provider interface, settings, policies, logs, budget limits and fallback
Switch provider/model through configuration without changing flow code.
2.5 AI conversation features
Intent, entities, response generation, clarification and safe action selection
AI cannot call an unconfigured or unauthorised action; low-confidence path is deterministic.
2.6 Knowledge base
Upload/URL ingestion, chunking, indexing, retrieval, source display and deletion
Answers are grounded in the correct bot/tenant documents; cross-tenant retrieval tests pass.
2.7 Human handover
Queues, assignments, operator inbox, notes, canned replies and resume
Conversation can move bot → agent → bot with a complete audit trail.
2.8 Production readiness
Observability, load/security tests, retention, backup, deployment and runbooks
All Phase 2 acceptance criteria pass in staging.
10. Phase 2 acceptance criteria
A single published bot can be deployed on website, WhatsApp and Telegram without duplicating its conversation logic.
Webhook verification, idempotency, rate limiting, retries and delivery status work for each supported channel.
Conversation identity is channel-specific unless explicitly linked through a verified process.
AI can be switched off without breaking rule-based flows.
AI responses use configured policies and, where enabled, tenant-filtered knowledge retrieval.
AI cannot bypass user verification, connector permissions, action schemas or confirmation requirements.
Human agents can take over and return a conversation to automation without losing context.
Provider credentials are encrypted and never sent to browser clients or model prompts.
Usage, latency, error and cost metrics are visible to authorised administrators.
PHASE 3 — Advanced integrations and workflow automation
11. Phase 3 objectives and scope
Phase 3 expands Universal Chatbot from a conversational front end into a controlled workflow orchestration layer. It introduces carefully constrained database access, a developer connector SDK, a private-network connector agent, advanced flow nodes and event-triggered conversations. API integrations remain the preferred option, especially for write operations.
Read-only MySQL and PostgreSQL connectors with strict allowlists and query templates.
Custom connector SDK and connector certification/test harness.
Private-network agent for customers whose ERP/CRM systems are not internet-accessible.
Advanced flow constructs: subflows, loops, wait/delay, scheduled resume, parallel branches, approvals, file processing and reusable components.
Event-triggered outbound conversations from business events, schedules or approved webhooks.
Expanded governance, audit, workflow monitoring and operational recovery.
12. Database connector design
Database connectors are an exceptional integration path, not a replacement for application APIs. Initial release should be read-only. Write operations should continue through business application APIs or explicitly reviewed connector actions.
Control
Required design
Credentials
Dedicated least-privilege DB account; read-only by default; encrypted at rest; rotateable; never exposed to browser or AI.
Scope
Explicit allowlist of schemas, tables and preferably views. Deny system schemas and sensitive columns by default.
Query model
Named, administrator-authored query templates with parameter schemas. Parameterised execution only.
SQL safety
No model-generated free-form SQL execution. If AI-assisted query drafting is ever offered, it creates a draft requiring human review and compilation into an approved template.
Limits
Statement timeout, row limit, response-size cap, connection pool cap, concurrency limit and cancellation.
Network
TLS where supported, IP/network restrictions, private agent for private systems and outbound-only connection where possible.
Audit
Log actor, tenant, connector, approved query ID, parameters with sensitive values redacted, duration, rows returned and outcome.
Data governance
Column masking, retention, export restrictions and documented lawful purpose/consent as applicable.
13. Connector SDK and registry
The SDK provides a stable contract for first-party and third-party connectors. A connector package declares its version, capabilities, authentication requirements, actions, input/output schemas, permission model and health checks.
Base interfaces: Connector, ActionDefinition, CredentialProvider, ConnectorContext and ConnectorResult.
Lifecycle: discover → validate manifest → install/register → configure credentials → test connection → enable actions → monitor → upgrade/disable.
Manifest must declare supported platform/version, dependencies, permissions, network destinations, data categories and idempotency behaviour.
Provide developer CLI or bench commands to scaffold, validate, package and test connectors.
Run connector actions with bounded timeouts and isolated execution context; do not permit arbitrary package installation from the admin UI.
Maintain connector compatibility matrix and signed/versioned packages for centrally hosted deployments.
14. Private-network connector agent
The connector agent is a separately deployable lightweight service installed inside a customer-controlled network. It establishes an authenticated outbound connection to the hosted Universal Chatbot control plane and receives only authorised, signed jobs. It must not expose an inbound management port to the public internet.
Pairing: one-time enrollment token, tenant binding, agent identity and administrator approval.
Transport: outbound TLS connection with short-lived credentials, mutual authentication where feasible and periodic key rotation.
Job envelope: job ID, connector/action ID, schema version, expiry, nonce, tenant, correlation ID and signed authorization context.
Execution: local connector allowlist, parameter validation, destination allowlist, timeouts and bounded result payload.
Response: signed result, status, duration and sanitized error; sensitive payloads encrypted in transit.
Operations: heartbeat, version reporting, revocation, update policy, health status and audit trail.
Failure behaviour: reject expired/replayed jobs; queue safely during brief outages; do not replay non-idempotent operations without explicit safeguards.
15. Advanced flow engine
Node type
Purpose and safeguards
Subflow / reusable component
Invoke a published reusable flow with typed input/output variables and recursion/depth limit.
Loop / iterator
Iterate over a bounded list; maximum iterations and execution time; prevent unbounded loops.
Wait / delay
Pause until a duration or event; persist state and resume through scheduler/queue.
Parallel branch
Run independent branches with explicit join policy, timeout and partial-failure handling.
Approval request
Route an action to a named role/user/group; approve/reject/timeout/escalate with audit.
Human handover
Pause bot and route to queue/agent; resume or terminate on resolution.
File/media processing
Validate type/size, scan where available, extract metadata/text, store securely and apply retention.
Webhook / event wait
Wait for a signed event matching a correlation key and expiry window.
Schedule / reminder
Create a bounded scheduled message with consent, quiet hours and cancellation support.
Error handler / compensation
Catch defined failures, retry safe operations, route to manual resolution or execute configured compensation.
16. Approval workflow and event-triggered conversations
Approval nodes must identify the approver, decision deadline, allowed outcomes and any required second-person approval. Approval links must be authenticated and single-use; sensitive decisions should require login rather than possession of a link alone.
Approval records store request, requester, approver, decision, comments, timestamps, expiry and related action execution.
No action executes before required approval is recorded. Approval cannot override the underlying user/connector permission model.
Event triggers may originate from ERPNext webhooks, scheduled jobs, connector events or approved external webhooks.
Each trigger has a schema, authentication method, deduplication key, bot/tenant scope, eligibility rules, rate limit and message template/flow.
Outbound messages must respect channel consent, provider templates, quiet hours, frequency caps and opt-out state.
Support delayed follow-up, reminder cancellation and suppression when the underlying business condition has already changed.
17. Phase 3 additional DocTypes
DocType
Purpose / key fields
Database Connection
DB type, host reference, database/schema, encrypted credential reference, TLS, status, owner tenant.
Database Object Allowlist
Connection, schema, object, allowed columns, masking rules, access scope.
Database Query Template
Connection, query ID, SQL template, parameter schema, max rows, timeout, status, reviewer.
Connector Package
Name, publisher, version, manifest, signature, compatibility, approval status.
Connector Installation
Tenant/site, package/version, configuration, enabled actions, health.
Private Agent
Tenant, agent ID, version, public key/certificate ref, last heartbeat, status, revocation.
Workflow Approval
Conversation/flow execution, action, approver, decision, deadline, evidence and status.
Scheduled Conversation
Tenant, bot, flow/version, contact, channel, due time, timezone, consent snapshot, status.
Event Subscription
Source, event type, schema, secret reference, target bot/flow, filter, retry and status.
Workflow Job
Execution, node, queue, attempt, lock, status, timing, error and retry metadata.
18. Phase 3 implementation milestones
Milestone
Deliverables
Exit test
3.1 Connector SDK
Manifest, base interfaces, scaffold, test harness, registry and compatibility rules
A sample custom connector can be packaged, validated and installed without modifying core code.
3.2 SQL read connectors
MySQL/PostgreSQL connection, allowlists, query templates, masking and audit
Penetration tests confirm no arbitrary SQL, cross-tenant reads or unbounded result retrieval.
3.3 Private agent
Enrollment, outbound channel, job protocol, local execution and revocation
A hosted bot securely retrieves a permitted value from a system reachable only inside customer network.
3.4 Advanced flow nodes
Subflow, loop, wait, parallel, error handler and file handling
Flow validator prevents cycles/limits violations and runtime resumes correctly after restart.
3.5 Approval engine
Approval assignments, expiry, escalation and audit
Protected action remains blocked until valid approval; expired/replayed decisions fail.
3.6 Event automation
Webhook subscriptions, scheduled triggers, outbound messaging and suppression
Duplicate events do not create duplicate messages/actions; opt-out and quiet hours are respected.
3.7 Enterprise governance
Monitoring, replay, audit reports, admin controls and recovery runbooks
Operators can diagnose and safely recover failed workflow jobs.
19. Phase 3 acceptance criteria
SQL access is read-only by default, allowlisted, parameterised, bounded and audited.
No free-form AI-generated SQL or code is executed.
Custom connectors follow a versioned manifest and can be tested independently.
Private agent is outbound-only, tenant-bound, revocable and rejects replayed/expired jobs.
Advanced flow nodes enforce loop, depth, time and payload limits.
Approval and event workflows are durable across worker restarts and recover from transient failures.
Outbound automation honours consent, opt-out, channel rules, quiet hours and rate limits.
PHASE 4 — Centrally hosted multi-tenant platform
20. Phase 4 objectives and scope
Phase 4 productises Universal Chatbot as a centrally operated hosted platform while retaining the self-hosted installation path. It introduces tenant onboarding, hard isolation, subscription plans, metering, billing, quotas, support operations, platform monitoring and enterprise deployment options. The SaaS control plane must not become a trusted shortcut around the tenant’s own integration permissions.
Tenant signup, verification, provisioning, lifecycle management and tenant administrator onboarding.
Strong data and execution isolation across bots, contacts, conversations, knowledge, credentials, logs, jobs and analytics.
Subscription plans, trials, entitlements, quotas, usage metering, invoices and payment-provider integration.
Platform-level administration, observability, incident response, backups, restore and disaster recovery.
Regional/data residency options and dedicated deployment options for enterprise customers.
Self-hosted and hosted editions share compatible configuration exports and core runtime behaviour.
21. SaaS tenancy and isolation model
Start with a shared application deployment and tenant-scoped records only if the isolation model is proven through automated security tests. Offer dedicated site/database or dedicated worker pools for customers requiring stronger isolation, data residency or predictable resource allocation.
Domain
Isolation requirements
Identity and access
Tenant membership, tenant roles, SSO options, MFA support, invitation lifecycle and tenant-scoped API keys.
Data
Tenant ID on every tenant-owned record; server-side permission checks; tenant-aware unique constraints and query helpers.
Files and knowledge
Tenant-specific object-storage prefixes/buckets and encryption context; signed short-lived download URLs; tenant-filtered retrieval index.
Credentials
Per-tenant secret references, encryption key hierarchy and strict admin access; secrets never shared across tenant context.
Jobs and queues
Tenant attribution on every job; fair scheduling, concurrency quotas, noisy-neighbour controls and queue isolation tiers.
Cache and search
Tenant-prefixed cache keys and mandatory tenant filters in search/vector retrieval.
Logs and analytics
Tenant-scoped access, sensitive-data redaction, configurable retention and restricted platform support access.
Backups and deletion
Documented backup scope, restore testing, tenant export and verified deletion lifecycle including derived indexes.
22. Tenant lifecycle and provisioning
Prospective customer creates an account or receives an invitation.
Platform verifies email/domain and performs any required organisation/business verification.
Customer selects plan, region and deployment tier; trial or subscription state is created.
Provisioning creates tenant record, default roles, storage namespace, encryption context, quotas and initial admin.
Tenant admin configures bot, channels, connectors, AI provider and knowledge sources.
Platform health checks validate configuration without exposing secrets.
Tenant can upgrade, downgrade, suspend, export or close the account under defined policies.
23. Subscription, entitlement and billing model
Commercial object
Fields / behaviour
Plan
Plan code, name, billing interval, included quotas, features, channel availability, retention and support tier.
Subscription
Tenant, plan, status, trial dates, billing dates, renewal, cancellation, payment customer reference.
Entitlement
Feature code, limit, period, overage policy, effective date and override source.
Usage Meter
Metric, unit, aggregation window, tenant, source event and deduplication key.
Usage Summary
Tenant, period, metric totals, included amount, billable overage and reconciliation status.
Invoice
Provider reference, amount, currency, tax, status, due date, payment status and line items.
Payment Event
Provider event ID, subscription/invoice reference, signature validation, processing status.
Credit / Adjustment
Tenant, reason, amount/units, approver, expiry and audit history.
Potential metered dimensions include inbound/outbound messages, AI input/output tokens, knowledge storage, file storage, connector executions, private-agent jobs, active agents and retained conversation volume. Define the billable unit and deduplication rule for each metric before launch. Do not bill on raw webhook retries or duplicate provider events.
23.1 Quota enforcement
Use configurable soft warnings and hard limits. Provide grace periods or overage billing only where the plan explicitly permits it.
Enforce quotas at the server-side gateway/action/AI/job layer, not only in the UI.
Allow critical administrative access and data export during suspension; define exactly which runtime functions are paused.
Provide tenant-visible usage dashboards and projected usage where practical.
Meter usage asynchronously from immutable usage events and reconcile totals against provider records.
24. Platform operations and reliability
Platform control plane: tenant lifecycle, plan/entitlement management, deployment inventory, feature flags and support tools.
Observability: structured logs, metrics, traces, correlation IDs, queue depth, provider errors, webhook lag, AI latency/cost and tenant-level usage.
SLOs: define availability, message acceptance latency, webhook processing latency, recovery time and support response objectives before GA.
Incident management: alert routing, severity classification, status communication, runbooks, post-incident review and tenant impact reports.
Backup/restore: encrypted backups, point-in-time recovery where supported, regular restore drills and documented RPO/RTO by tier.
Release management: staged rollout, canary tenants, feature flags, migration validation, rollback plan and compatibility checks.
Abuse controls: signup throttling, spam detection, messaging velocity limits, account suspension and provider policy monitoring.
25. Enterprise deployment and data governance
Offer standard shared SaaS, dedicated tenant environment and self-hosted deployment tiers.
Define supported regions and document where application data, backups, AI requests and telemetry are processed.
Provide configurable retention, export, deletion and legal-hold policies appropriate to the service model.
Support SSO/SAML or OIDC, MFA policy, audit export, IP restrictions and enterprise key-management options as roadmap capabilities.
Provide data-processing terms, subprocessors list, security documentation, incident notification process and customer responsibility matrix.
Allow customer-managed AI provider credentials or approved regional AI endpoints where feasible.
26. Phase 4 additional DocTypes / platform entities
Entity / DocType
Purpose / key fields
Tenant
Tenant code, legal/display name, region, status, owner, plan, created/provisioned dates.
Tenant Membership
Tenant, user, role, invitation status, joined/disabled timestamps.
Tenant Provisioning Job
Tenant, deployment tier, resource allocation, status, attempts, logs and completion.
Plan / Plan Feature
Plan catalogue, feature flags, quota values, pricing and availability.
Subscription / Entitlement
Commercial relationship and effective feature/limit grants.
Usage Event / Usage Meter / Usage Summary
Immutable event ledger, aggregation rules and period summaries.
Invoice / Payment Event / Credit Adjustment
Billing, payment reconciliation and manual corrections.
Deployment Region
Region code, service endpoints, data-residency attributes and operational status.
Tenant Deployment
Shared/dedicated/self-hosted deployment mapping, version, health and capacity tier.
Platform Audit Event
Platform administrator actions, impersonation/support access, provisioning and billing changes.
Support Access Grant
Tenant-approved time-bound support access, reason, scope, approver and revocation.
27. Phase 4 implementation milestones
Milestone
Deliverables
Exit test
4.1 Tenancy foundation
Tenant identity, membership, tenant context middleware, data access layer and isolation tests
Automated adversarial tests prove no cross-tenant access through API, reports, search, files, jobs or cache.
4.2 Provisioning
Signup/invitation, tenant bootstrap, region/tier assignment and lifecycle controls
A new tenant can be provisioned and configured without manual database intervention.
4.3 Entitlements and metering
Plans, feature gates, immutable usage events, aggregation and quota enforcement
Usage reconciles with test provider events; duplicate events are not double-counted.
4.4 Billing integration
Payment provider adapter, invoices, webhooks, retries, dunning and credits
Successful, failed, refunded and duplicate payment events update subscription state correctly.
4.5 Platform operations
Monitoring, alerting, audit, support access, backup and restore runbooks
Operations team can detect, diagnose and recover from a simulated tenant-impacting incident.
4.6 Enterprise tier
Dedicated deployment option, SSO, audit export, regional controls and admin policies
Enterprise tenant meets documented isolation and governance requirements.
4.7 General availability
Security review, load test, legal/compliance readiness, documentation and support model
GA readiness review signed off; rollback and incident procedures tested.
28. Phase 4 acceptance criteria
A tenant can be created, provisioned, configured, suspended, exported and closed through controlled lifecycle workflows.
Tenant isolation covers database records, APIs, reports, files, search/vector indexes, caches, jobs, logs and analytics.
Plan entitlements and quotas are enforced server-side and visible to tenant administrators.
Usage metering is auditable, idempotent and reconcilable with provider-side events.
Billing webhooks are authenticated, deduplicated and recoverable.
Platform operators have least-privilege support access with approval, expiry and audit.
Backup restoration and tenant data export/deletion procedures are tested.
Self-hosted customers can continue operating without depending on SaaS control-plane availability.
29. Recommended release and versioning strategy
Release line
Scope
Compatibility rule
1.x
Phase 1 core and website channel
Stable common message protocol, flow schema v1 and connector contract v1.
2.x
Phase 2 channels and AI
Additive protocol capabilities; versioned channel payload mapping; AI provider abstraction; migration path for bot settings.
3.x
Phase 3 connectors and workflows
Versioned connector manifest and flow schema; safe migration of execution state; explicit deprecation windows.
4.x
Phase 4 SaaS platform
Tenant-aware APIs and platform control plane; maintain self-hosted installation and export compatibility.
Maintain separate versions for application package, public API, common message protocol, flow schema and connector manifest. Published bot snapshots must record the schema/runtime compatibility version. Use migration scripts and pre-upgrade backups; never silently rewrite active flow semantics.
30. Non-functional requirements and quality gates
Area
Minimum design requirement
Security
Threat model, secure secrets, least privilege, tenant isolation, webhook validation, rate limits, audit and dependency scanning.
Performance
Queue-based processing for slow work; bounded execution; load tests for concurrent sessions, webhook bursts and AI calls.
Availability
Graceful provider outage handling, retries, circuit breakers, health checks and documented recovery objectives.
Maintainability
Typed interfaces, modular packages, linting, unit/integration tests, API documentation and upgrade tests.
Observability
Structured logs, metrics, traces, correlation IDs and dashboards without unnecessary personal data.
Accessibility
Operator console and website widget usable by keyboard and assistive technology; accessible status and error messaging.
Portability
Export/import of bot configuration, flows, connector manifests and knowledge metadata with secrets excluded.
Privacy
Purpose limitation, minimisation, retention, deletion, consent and access/export workflows.
31. Testing strategy across phases
Unit tests: protocol parsing, state transitions, flow node behaviour, permission evaluation, schema validation and metering calculations.
Contract tests: every channel adapter, connector, AI provider and private agent must pass shared contract suites.
Integration tests: provider sandbox/test accounts, ERPNext test site, sample SQL databases and mock event sources.
Security tests: webhook forgery, replay, credential leakage, prompt injection, action escalation, SQL injection, SSRF, file upload abuse and cross-tenant access.
Reliability tests: duplicate events, out-of-order callbacks, worker restart, queue backlog, provider outage, timeout and retry exhaustion.
Performance tests: concurrent conversations, channel webhook bursts, large knowledge indexes, connector concurrency and operator inbox load.
Upgrade tests: install from clean site, upgrade from prior supported version, migrate active conversations and rollback/restore where possible.
Acceptance tests: scenario-based end-to-end tests owned jointly by product and engineering.
32. Key risks and mitigations
Risk
Mitigation
Provider policy changes or account restrictions
Keep channel adapters isolated; monitor policy changes; support provider sandbox; expose configuration validation and delivery diagnostics.
AI hallucination or unsafe action
Use AI for language and extraction, not authority; retrieval grounding, schemas, confirmation, permissions and deterministic fallbacks.
Cross-tenant data leakage
Tenant context enforced at data-access boundary; automated negative tests across every access path; security review before SaaS launch.
Unbounded workflow or queue execution
Node limits, execution budgets, concurrency caps, dead-letter queues and admin cancellation.
Private agent compromise
Outbound-only, least privilege, signed jobs, short-lived credentials, revocation and restricted destination allowlists.
Unexpected AI/provider costs
Budgets, per-tenant limits, model routing, caching where safe, usage alerts and fallback to rules.
SaaS noisy-neighbour effects
Fair scheduling, per-tenant quotas, queue isolation tiers and dedicated deployments for higher tiers.
Over-complexity too early
Preserve phase gates; do not build microservices, full billing or SQL write access before validated demand.
33. Recommended implementation order and dependencies
Complete and stabilise Phase 1 core contracts before adding production channels. Freeze the common message protocol and flow execution interfaces with versioning.
Build channel event reliability and Telegram first as a comparatively simple adapter; use it to validate adapter abstractions.
Implement WhatsApp next, including provider account setup, templates, consent and delivery status.
Add AI provider abstraction and policy enforcement before exposing AI nodes to end users.
Build knowledge ingestion/retrieval with tenant/bot scoping, then connect it to AI response generation.
Deliver handover and operator console after conversation identity, channel delivery and event state are reliable.
In Phase 3, deliver connector SDK before third-party connectors; implement SQL read-only controls before considering any write capability.
Build private agent only after connector action schemas and signing/authentication contracts are stable.
Add advanced workflow nodes incrementally with durable state and execution limits.
Before Phase 4 billing, complete tenant isolation and usage event ledger; billing must consume reconciled usage rather than instrumenting ad hoc counters.
Launch SaaS only after cross-tenant security testing, restore drills, incident runbooks and support processes are operational.
34. What is explicitly not included unless separately approved
A native iOS/Android end-user app; Phase 2 provides APIs and channel support for external apps.
Unrestricted autonomous AI agents, arbitrary code execution or unrestricted AI-generated SQL.
Direct database write access as a default integration method.
A general-purpose campaign marketing suite or bulk unsolicited messaging platform (Note: Targeted transactional broadcasts, consent-governed community announcements and billing alerts are explicitly supported via Chatbot Broadcast Campaign).
Guaranteed provider account approval, WhatsApp template approval, telecom delivery or third-party uptime.
A full ERP/CRM replacement; Universal Chatbot orchestrates conversations and approved actions in existing systems.
Automatic migration of customer data from arbitrary chatbot platforms without a separately scoped migration project.
35. Product decisions to confirm before each phase
Decision
Recommended default
WhatsApp integration
Meta WhatsApp Cloud API directly for initial release; consider BSP abstraction only if customer demand requires it.
AI provider
Provider-neutral interface; begin with one provider and keep tenant/customer key ownership configurable.
Knowledge vector store
Abstract the vector index behind an interface; choose the initial backend based on Frappe deployment constraints and operational simplicity.
Operator UI
Frappe Desk workspace for administration and agent console initially; separate frontend only if usability or scale requires it.
SQL connector
Read-only templates and allowlisted views only; API remains preferred.
Private agent topology
Outbound-only secure connection; avoid inbound port exposure and remote shell capability.
SaaS tenancy
Shared multi-tenant architecture only after formal isolation tests; dedicated site/database tier for stronger isolation.
Billing provider
Use an adapter; select provider after geography, currency, tax, recurring billing and settlement requirements are confirmed.
Hosting region
Decide from target customer geography, data residency and AI provider processing locations.
36. Definition of done for the overall product
A self-hosted customer can install, operate, upgrade and back up Universal Chatbot independently.
A centrally hosted customer can be provisioned and isolated without manual data-layer intervention.
A bot configuration can be exported from self-hosted and imported into hosted deployment, with secrets and environment-specific values handled separately.
Channels share common flows while retaining provider-specific policy and presentation handling.
AI is optional, governed, observable and never an authority for permissions.
Business data is accessed through explicit connectors/actions with auditable authorisation.
Long-running workflows, approvals, events and human handovers survive worker restarts.
Operators and tenant administrators can diagnose delivery, integration, AI and workflow failures.
Security, privacy, retention, export, deletion, backup and incident procedures are documented and tested.
Appendix A — Illustrative application module extensions
The following is a logical structure, not a requirement to create every folder immediately. Keep modules small and introduce them only when the corresponding phase begins.
universal_chatbot/  core/                 # framework-independent message and conversation engine  flow/                 # parser, validator, runtime, node registry  channels/             # web, whatsapp, telegram, public_api adapters  gateway/              # webhook/API ingress, auth, idempotency, routing  connectors/           # base contracts, frappe_rest, generic_rest, sql, sdk  agent/                # private-network agent protocol and job dispatch  ai/                   # provider adapters, policies, prompts, retrieval orchestration  knowledge/            # ingestion, extraction, chunking, indexing, retrieval  handover/             # queues, assignments, operator actions  workflows/            # approvals, schedules, event subscriptions, durable jobs  tenancy/              # tenant context, isolation and provisioning (Phase 4)  billing/              # plans, entitlements, usage ledger, invoices (Phase 4)  observability/        # metrics, traces, audit and health  api/                  # versioned public and internal endpoints  tests/                # unit, contract, integration, security and load tests
Appendix B — Example end-to-end scenarios
B1. WhatsApp resident enquiry with human escalation
Resident messages the association WhatsApp number.
Webhook adapter validates and deduplicates the message, then resolves the bot deployment.
Bot asks for flat number and performs the configured identity verification.
AI interprets the question but selects only the approved maintenance-dues action.
Connector calls the association ERPNext API using a server-held credential and resident-scoped permission.
Bot responds with the permitted balance and asks whether further help is required.
If resident disputes the amount, a handover node routes the conversation to the accounts queue.
Agent reviews the conversation, adds internal notes, replies and resolves it. The transcript and audit trail are retained according to policy.
B2. Private-network business lookup
A customer has an on-premise PostgreSQL database not exposed to the public internet.
Administrator installs and pairs the private connector agent with the customer tenant.
Administrator configures an allowlisted view and read-only query template.
A verified user asks for a permitted business status.
The bot invokes the approved action; hosted service sends a signed, expiring job over the agent’s outbound connection.
Agent validates tenant, action, schema and destination, executes the bounded query and returns a signed result.
Chatbot validates output and displays only fields allowed by the action policy.
B3. SaaS tenant onboarding and usage
An organisation signs up and selects a plan and region.
Provisioning creates tenant context, admin membership, storage namespace, quotas and default policies.
Tenant admin creates bots and configures its own channels, AI provider and connectors.
Immutable usage events are emitted for messages, AI tokens and connector calls.
Metering aggregates usage and enforces plan quotas; tenant admin sees usage dashboard and alerts.
Billing adapter creates the invoice and processes authenticated payment-provider events.
Appendix C — Phase gates
Gate
Must be true before proceeding
Phase 1 → Phase 2
Core protocol and flow schema stable; published versioning works; permissions and action execution tested; baseline observability present.
Phase 2 → Phase 3
Channel event handling reliable; AI policy controls proven; knowledge isolation and handover complete; usage/cost measurement available.
Phase 3 → Phase 4
Connector SDK and workflow runtime stable; private agent security reviewed; durable job recovery proven; tenant isolation design threat-modelled.
Phase 4 public launch
Tenant isolation penetration-tested; metering reconciled; billing recovery tested; backup/restore and incident drills complete; legal and support readiness approved.