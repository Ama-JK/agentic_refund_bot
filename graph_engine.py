import json
import sqlite3
from typing import Dict, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_ollama import ChatOllama

# ==========================================
# 1. DEFINE THE CORE GRAPH STATE
# ==========================================
class AgentState(TypedDict):
    user_query: str
    order_id: str
    category: str
    api_response: dict
    api_errors: list
    human_approved: bool
    final_output: str

# ==========================================
# 2. DEFINE ARCHITECTURAL NODES (WITH REAL SQL DATABASE!)
# ==========================================

# NODE 1: The Intent Router Agent
def router_node(state: AgentState) -> Dict:
    query = state["user_query"]
    llm = ChatOllama(model="llama3", temperature=0)
    
    system_prompt = (
        "You are an expert support router. Analyze the user's query and extract details.\n"
        "1. Identify the category: If they want a refund, return, or cancel an order, set category to 'refund'.\n"
        "   If they ask a general question, store hours, locations, shipping, or contact details, set category to 'general_qa'.\n"
        "2. Extract the Order ID: Look for any ID starting with 'FR-' followed by numbers (e.g., FR-10243). If not found, set order_id to 'UNKNOWN'.\n"
        "Return ONLY a valid JSON string with keys 'category' and 'order_id'. Do not write any explanations."
    )
    
    messages = [("system", system_prompt), ("human", query)]
    
    try:
        response = llm.invoke(messages)
        raw_content = response.content.strip()
        if "{" in raw_content and "}" in raw_content:
            raw_content = raw_content[raw_content.find("{"):raw_content.rfind("}")+1]
        ai_data = json.loads(raw_content)
        return {
            "category": ai_data.get("category", "general_qa"), 
            "order_id": ai_data.get("order_id", "UNKNOWN")
        }
    except Exception as e:
        print(f"LLM Router Error: {e}. Falling back to rules.")
        if "FR-" in query.upper():
            return {"category": "refund", "order_id": query.upper()[query.upper().find("FR-"):query.upper().find("FR-")+8]}
        return {"category": "general_qa", "order_id": "UNKNOWN"}

# ✨ UPDATED NODE: QA Agent fetching Dynamic Knowledge Base from SQL!
def general_qa_agent_node(state: AgentState) -> Dict:
    query = state["user_query"]
    llm = ChatOllama(model="llama3", temperature=0)
    
    # Ask LLM to pick the right database keyword based on user query
    keyword_prompt = (
        "Analyze the user query and pick exactly ONE keyword that matches their intent from this list: "
        "['hours', 'location', 'shipping', 'contact', 'details']. If none match, return 'UNKNOWN'.\n"
        "Return ONLY the single word. No punctuation, no explanation."
    )
    
    try:
        db_keyword = llm.invoke([("system", keyword_prompt), ("human", query)]).content.strip().lower()
        
        # Connect to the real SQLite DB and fetch the actual policy text
        conn = sqlite3.connect("french_retail.db")
        cursor = conn.cursor()
        cursor.execute("SELECT response_text FROM faq_store WHERE keyword = ?", (db_keyword,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            # Found inside the real Database!
            return {"final_output": f"[Fetched from Secure DB] {row[0]}"}
    except Exception as db_err:
        print(f"Database QA Error: {db_err}")
        
    # Fallback to LLM general knowledge if not found in database
    system_prompt = (
        "You are a polite retail support agent for 'French Retail'.\n"
        "If you don't know the specific answer based on the store, just say: "
        "'Thank you for contacting French Retail. For store details, please specify if you need our location, hours, or shipping policies.'\n"
        "Do not invent random shop names like Blooming Delights or fake US addresses."
    )
    response = llm.invoke([("system", system_prompt), ("human", query)])
    return {"final_output": response.content.strip()}

# 🗄️ UPDATED NODE: Data Retrieval Agent fetching from real SQL 'orders' table!
def database_fetcher_node(state: AgentState) -> Dict:
    order_id = state["order_id"]
    if order_id == "UNKNOWN":
        return {"api_response": {"status": "error", "message": "No valid order ID provided."}}
        
    try:
        # Connecting to the real SQLite DB file
        conn = sqlite3.connect("french_retail.db")
        cursor = conn.cursor()
        
        # SQL Query Injection Guard via parameterized query
        cursor.execute("SELECT customer_name, amount, days_passed FROM orders WHERE order_id = ?", (order_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            # Structuring the database row into our AgentState schema format
            return {
                "api_response": {
                    "status": "success",
                    "data": {
                        "customer": row[0],
                        "amount": row[1],
                        "days_passed": row[2]
                    }
                }
            }
        else:
            return {"api_response": {"status": "error", "message": f"Order ID {order_id} not found in SQL database."}}
            
    except Exception as e:
        return {"api_response": {"status": "error", "message": f"SQL Database Error: {str(e)}"}}

# NODE 4: The Compliance Agent
def policy_validator_node(state: AgentState) -> Dict:
    api_data = state["api_response"]
    if api_data.get("status") == "error":
        return {"final_output": f"Refused: {api_data.get('message')}", "human_approved": False}
    
    days = api_data["data"]["days_passed"]
    customer_name = api_data["data"]["customer"]
    amount = api_data["data"]["amount"]
    
    if days > 30:
        return {
            "final_output": f"Dear {customer_name}, your refund request for €{amount} is rejected because the 30-day return window passed ({days} days ago).",
            "human_approved": False
        }
    return {"human_approved": False}

# NODE 5 & 6: HITL Gate and Fulfillment
def human_approval_placeholder_node(state: AgentState) -> Dict:
    return {"human_approved": True}

def execute_refund_node(state: AgentState) -> Dict:
    customer_name = state["api_response"]["data"]["customer"]
    amount = state["api_response"]["data"]["amount"]
    return {"final_output": f"Succès! Refund of €{amount} approved and processed for {customer_name}."}

# ==========================================
# 3. GRAPH COMPILATION PIPELINE
# ==========================================
workflow = StateGraph(AgentState)

workflow.add_node("router", router_node)
workflow.add_node("general_qa_agent", general_qa_agent_node)
workflow.add_node("database_fetcher", database_fetcher_node)
workflow.add_node("policy_validator", policy_validator_node)
workflow.add_node("human_approval", human_approval_placeholder_node)
workflow.add_node("execute_refund", execute_refund_node)

workflow.add_edge(START, "router")
workflow.add_conditional_edges("router", lambda state: "database_fetcher" if state["category"] == "refund" else "general_qa_agent")
workflow.add_edge("general_qa_agent", END)
workflow.add_edge("database_fetcher", "policy_validator")

def route_after_policy(state: AgentState):
    if "Refused" in state.get("final_output", "") or "rejected" in state.get("final_output", ""):
        return END
    return "human_approval"
    
workflow.add_conditional_edges("policy_validator", route_after_policy)
workflow.add_edge("human_approval", "execute_refund")
workflow.add_edge("execute_refund", END)

compiled_agent = workflow.compile(checkpointer=MemorySaver(), interrupt_before=["human_approval"])