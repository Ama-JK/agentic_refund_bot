import json
from typing import Dict, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
# Importing ChatOllama to communicate with our locally running Llama 3 model
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
# 2. DEFINE ARCHITECTURAL NODES (WITH LOCAL LLM!)
# ==========================================
def router_node(state: AgentState) -> Dict:
    query = state["user_query"]
    
    # Initializing the local Llama 3 model with zero temperature for deterministic outputs
    llm = ChatOllama(model="llama3", temperature=0)
    
    # System prompt directing the LLM to act as a structured router and extract data as JSON
    system_prompt = (
        "You are an expert support router. Analyze the user's query and extract details.\n"
        "1. Identify the category: If they want a refund or return, set category to 'refund'. Otherwise, set it to 'general_qa'.\n"
        "2. Extract the Order ID: Look for any ID starting with 'FR-' followed by numbers (e.g., FR-10243). If not found, set order_id to 'UNKNOWN'.\n"
        "Return ONLY a valid JSON string with keys 'category' and 'order_id'. Do not write any explanations."
    )
    
    messages = [
        ("system", system_prompt),
        ("human", query)
    ]
    
    try:
        response = llm.invoke(messages)
        raw_content = response.content.strip()
        
        # Sanitizing the LLM output to ensure only the raw JSON block is parsed
        if "{" in raw_content and "}" in raw_content:
            raw_content = raw_content[raw_content.find("{"):raw_content.rfind("}")+1]
            
        ai_data = json.loads(raw_content)
        return {
            "category": ai_data.get("category", "general_qa"), 
            "order_id": ai_data.get("order_id", "UNKNOWN")
        }
    except Exception as e:
        # Robust fallback mechanism to regex/rule-based routing if the local LLM fails or times out
        print(f"LLM Error: {e}. Falling back to rule-based routing.")
        extracted_order = "UNKNOWN"
        if "FR-" in query.upper():
            start_idx = query.upper().find("FR-")
            extracted_order = query.upper()[start_idx:start_idx+8]
        if "REFUND" in query.upper() or "RETURN" in query.upper():
            return {"category": "refund", "order_id": extracted_order}
        return {"category": "general_qa", "order_id": extracted_order}

def database_fetcher_node(state: AgentState) -> Dict:
    if state["order_id"] == "UNKNOWN":
        return {"api_response": {"status": "error", "message": "No valid order ID provided."}}
    try:
        with open("database.json", "r") as f:
            db = json.load(f)
        if state["order_id"] in db:
            return {"api_response": {"status": "success", "data": db[state["order_id"]]}}
        else:
            return {"api_response": {"status": "error", "message": "Order ID not found in database."}}
    except Exception as e:
        return {"api_response": {"status": "error", "message": str(e)}}

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
    else:
        return {"human_approved": False}

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
workflow.add_node("database_fetcher", database_fetcher_node)
workflow.add_node("policy_validator", policy_validator_node)
workflow.add_node("human_approval", human_approval_placeholder_node)
workflow.add_node("execute_refund", execute_refund_node)

workflow.add_edge(START, "router")
workflow.add_conditional_edges("router", lambda state: "database_fetcher" if state["category"] == "refund" else END)
workflow.add_edge("database_fetcher", "policy_validator")

def route_after_policy(state: AgentState):
    if "Refused" in state.get("final_output", "") or "rejected" in state.get("final_output", ""):
        return END
    return "human_approval"
    
workflow.add_conditional_edges("policy_validator", route_after_policy)
workflow.add_edge("human_approval", "execute_refund")
workflow.add_edge("execute_refund", END)

compiled_agent = workflow.compile(checkpointer=MemorySaver(), interrupt_before=["human_approval"])