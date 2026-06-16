# 🤖 Multi-Agent Retail Automation Engine with LangGraph & SQLite

An enterprise-grade, state-machine driven customer support network designed for premium retail infrastructure. Built entirely with **LangGraph**, **Ollama (Llama 3)**, and a relational **SQLite database**, this engine intelligently orchestrates intent routing, automated policy enforcement, secure live data fetching, and Human-In-The-Loop (HITL) compliance gates.

---

## 🏗️ Architecture Blueprint

The system coordinates operations across multiple dedicated node components inside a structured state graph graph pipeline:

*   **Intent Router Agent:** Employs a zero-temperature LLM parser to classify customer intents and extract contextual entities (e.g., Order IDs).
*   **Secure Data Fetcher:** Executes parameterized SQL injections-guarded queries across relational database tables (`orders` & `faq_store`).
*   **Compliance & Policy Validator:** Enforces static runtime business constraints (e.g., the 30-day return policy window).
*   **Human-In-The-Loop (HITL) Gate:** Seamlessly halts critical state transitions, freezing state memory variables to request supervisor authority before executing cash operations.
*   **General QA Agent:** Features an optimized query matcher to hook local documentation tables before relying on core LLM parameters.

---

## 🛠️ Tech Stack & Tooling

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Orchestration** | LangGraph / LangChain | Directed Acyclic Graph (DAG) State Machine |
| **Brain Core** | Ollama / Llama 3 | Localized Private Inference LLM Engine |
| **Database** | SQLite3 | Multi-table relational secure transactional store |
| **Interface** | Streamlit | Real-time monitoring and chat playground |
| **Testing** | Unittest | Automated state pipeline validation suite |

---

## 📂 Project Directory Structure

```text
├── app.py                # Streamlit Web Interface & State Hydration Engine
├── graph_engine.py       # LangGraph Core State Engine & Node Formulations
├── init_db.py            # Relational SQLite Database Initialization Script
├── test_agent.py         # Automated Test Suite with Assertion Anchors
├── french_retail.db      # Localized SQLite database (Generated locally)
└── README.md             # Systems documentation handbook

---
```
## Installation & Local Execution
## 1. Clone the repository & Install Dependencies
```bash
git clone https://github.com/Ama-JK/agentic_refund_bot.git
cd agentic_refund_bot
pip install langchain langchain-ollama langgraph streamlit sqlite3
```

## 2. Boot up local LLM Server
Ensure you have Ollama installed locally and running in the background:
```bash
ollama run llama3
```

## 3. Initialize Relational Databases
Run the seeding script to compile tables and insert transactional schema data:
```bash
python init_db.py
```

## 4. Run Automated Test Suite
Validate pipeline graph states, route isolation, and boundary assertions:
```bash
python test_agent.py
```

## 5. Fire up UI Playground
```bash
streamlit run app.py
```

## 🧪 Production Test Metrics

The automated verification engine checks 3 baseline production vectors using isolated thread checkpoints:

*   **`test_general_qa_shipping_path`**: Verifies dynamic SQL fetching against string token anchors (`[Fetched from Secure DB]`).
*   **`test_refund_rejected_path`**: Tests logic constraints against database mock profiles beyond the 30-day transactional boundary.
*   **`test_router_fallback_unknown_id`**: Asserts clean pipeline stabilization and graceful error messaging during unindexed query inquiries

```text
...
----------------------------------------------------------------------
Ran 3 tests in 4.521s

OK
```
