import json
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
# 2. DEFINE ARCHITECTURAL NODES
# ==========================================

# NODE 1: The Intent Router Agent
def router_node(state: AgentState) -> Dict:
    query = state["user_query"]
    llm = ChatOllama(model="llama3", temperature=0)
    
    system_prompt = (
        "You are an expert support router. Analyze the user's query and extract details.\n"
        "1. Identify the category: If they want a refund, return, or cancel an order, set category to 'refund'.\n"
        "   If they ask a general question, store hours, locations, or product details, set category to 'general_qa'.\n"
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

# ✨ NEW NODE: The General QA Specialist Agent!
def general_qa_agent_node(state: AgentState) -> Dict:
    query = state["user_query"]
    # We can give a slightly higher temperature for creative/helpful support answers
    llm = ChatOllama(model="llama3", temperature=0.3)
    
    system_prompt = (
        "You are a helpful customer service agent for a premium retail store called 'French Retail'.\n"
        "Answer the customer's general question politely, professionally, and concisely.\n"
        "If they ask for store hours: We are open Monday to Saturday from 9 AM to 8 PM.\n"
        "If they ask for locations: Our main flagship store is located in Paris, France.\n"
        "Keep the response under 3 sentences."
    )
    
    messages = [("system", system_prompt), ("human", query)]
    response = llm.invoke(messages)
    
    # Store the LLM's direct answer into final_output
    return {"final_output": response.content.strip()}

# NODE 3: The Data Retrieval Agent
def database_fetcher_node(state: AgentState) -> Dict:
    if state["order_id"] == "UNKNOWN":
        return {"api_response": {"status": "error", "message": "No valid order ID provided."}}
    try:
        with open("database.json", "r") as f:
            db = json.load(f)
        if state["order_id"] in db:
            return {"api_response": {"status": "success", "data": db[state["order_id"]]}}
        return {"api_response": {"status": "error", "message": "Order ID not found in database."}}
    except Exception as e:
        return {"api_response": {"status": "error", "message": str(e)}}

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
# 3. GRAPH COMPILATION PIPELINE (The Multi-Agent Map)
# ==========================================
workflow = StateGraph(AgentState)

# Register all nodes including our new QA Agent
workflow.add_node("router", router_node)
workflow.add_node("general_qa_agent", general_qa_agent_node) # 👈 Added
workflow.add_node("database_fetcher", database_fetcher_node)
workflow.add_node("policy_validator", policy_validator_node)
workflow.add_node("human_approval", human_approval_placeholder_node)
workflow.add_node("execute_refund", execute_refund_node)

# Graph Routing Logic
workflow.add_edge(START, "router")

# 🔀 CONDITIONAL EDGE: Router splits traffic based on LLM decision!
workflow.add_conditional_edges(
    "router", 
    lambda state: "database_fetcher" if state["category"] == "refund" else "general_qa_agent"
)

# QA Path directly goes to the end after answering
workflow.add_edge("general_qa_agent", END) # 👈 Added

# Refund Path follows the strict policy and human verification
workflow.add_edge("database_fetcher", "policy_validator")

def route_after_policy(state: AgentState):
    if "Refused" in state.get("final_output", "") or "rejected" in state.get("final_output", ""):
        return END
    return "human_approval"
    
workflow.add_conditional_edges("policy_validator", route_after_policy)
workflow.add_edge("human_approval", "execute_refund")
workflow.add_edge("execute_refund", END)

compiled_agent = workflow.compile(checkpointer=MemorySaver(), interrupt_before=["human_approval"])