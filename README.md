# 🇫🇷 Enterprise Refund Automation Engine (Built with LangGraph & Streamlit)

An advanced Agentic AI customer support system demonstrating a multi-agent state graph built with **LangGraph** featuring local mock database fetching, deterministic compliance validation, and a bulletproof **Human-in-the-Loop** approval checkpoint mechanism.

## 🛠️ Tech Stack & Concepts Demonstrated
- **LangGraph Orchestration:** State graph management using `StateGraph`, conditional edge routing, and automatic step interruption.
- **State Persistence:** Implemented short-term memory checkpointers via `MemorySaver` to pause and resume specific thread executions.
- **UI Decoupling (MVC):** Separate backend AI graph execution engine (`graph_engine.py`) integrated cleanly into a responsive frontend (`app.py`).
- **Streamlit Session State:** Preserving thread state contexts and controlling visual rendering stages seamlessly across manual UI refreshes.

## 🏃‍♂️ How to Run Locally

1. **Clone the repository and spin up the environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   pip install langgraph streamlit langchain_openai python-dotenv

## Run the Interactive Dashboard:
streamlit run app.py