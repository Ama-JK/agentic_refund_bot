import streamlit as st
import json
# MAGIC LINE: graph_engine ஃபைல்ல இருந்து கம்பைல் ஆன ஏஜென்ட்டை இங்க இம்போர்ட் பண்றோம்!
from graph_engine import compiled_agent

# ==========================================
# STREAMLIT INTERACTIVE UI LAYOUT
# ==========================================
st.set_page_config(page_title="Agentic AI Support - France Tech", page_icon="🇫🇷", layout="centered")

st.title("🇫🇷 Agentic AI: Customer Support Portal")
st.subheader("Enterprise Refund Automation Engine (Built with LangGraph)")
st.write("This dashboard demonstrates a production-grade multi-agent workflow with structural policy checks and a **Human-in-the-Loop** approval mechanism.")

st.divider()

if "agent_thread" not in st.session_state:
    st.session_state.agent_thread = {"configurable": {"thread_id": "streamlit_user_session_v3"}}
if "current_stage" not in st.session_state:
    st.session_state.current_stage = "INPUT_STAGE"
if "latest_output" not in st.session_state:
    st.session_state.latest_output = ""
if "order_details" not in st.session_state:
    st.session_state.order_details = None

# STAGE 1: USER INPUT STAGE
if st.session_state.current_stage == "INPUT_STAGE":
    st.info("💡 **Demo Testing Guide:**\n"
            "- Enter **FR-10243** (Anand - 12 days passed) to see the **Human Approval Loop** pass.\n"
            "- Enter **FR-99999** (Marie - 45 days passed) to see the **Automatic Policy Rejection** work.")
    
    user_query = st.text_area("Customer Support Message:", 
                              value="Bonjour! I want a refund for my order FR-10243 please.")
    
    if st.button("🚀 Launch Autonomous Agent Pipeline"):
        st.write("---")
        st.write("### 🤖 Live Execution logs:")
        
        initial_state = {
            "user_query": user_query,
            "api_errors": [],
            "human_approved": False,
            "final_output": ""
        }
        
        # இங்க நம்ம graph_engine-ஓட ஏஜென்ட் தான் ரன் ஆகுது!
        for event in compiled_agent.stream(initial_state, st.session_state.agent_thread):
            for node_name, state_update in event.items():
                st.caption(f"✔️ Finished executing architectural node: `{node_name}`")
                if "final_output" in state_update and state_update["final_output"]:
                    st.session_state.latest_output = state_update["final_output"]

        graph_state = compiled_agent.get_state(st.session_state.agent_thread)
        
        if graph_state.next:
            st.session_state.current_stage = "FROZEN_STAGE"
            st.session_state.order_details = graph_state.values.get("api_response", {}).get("data", {})
            st.rerun()
        else:
            st.session_state.current_stage = "COMPLETED_STAGE"
            st.rerun()

# STAGE 2: ADMIN GUARDRAIL / FROZEN STAGE
elif st.session_state.current_stage == "FROZEN_STAGE":
    st.warning("⚠️ **LANGGRAPH NOTIFICATION: FLOW INTERRUPTED (FREEZE MODE ACTIVE)**")
    st.write("The autonomous agent has paused the system. A human manager must verify this high-value refund before execution.")
    
    with st.expander("🛠️ Manager Control Dashboard", expanded=True):
        st.write("### Review Order Details (Fetched dynamically from database.json)")
        st.json(st.session_state.order_details)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Approve Refund & Resume Graph Execution", type="primary"):
                st.success("Manager permission granted! Resuming agent stream...")
                
                compiled_agent.update_state(st.session_state.agent_thread, {"human_approved": True}, as_node="human_approval")
                
                for event in compiled_agent.stream(None, st.session_state.agent_thread):
                    for node_name, state_update in event.items():
                        st.caption(f"✔️ Finished executing post-interrupt node: `{node_name}`")
                        if "final_output" in state_update:
                            st.session_state.latest_output = state_update["final_output"]
                
                st.session_state.current_stage = "COMPLETED_STAGE"
                st.rerun()
        
        with col2:
            if st.button("❌ Deny Refund & Cancel", type="secondary"):
                st.session_state.latest_output = "Refund request manually cancelled by Admin Manager."
                st.session_state.current_stage = "COMPLETED_STAGE"
                st.rerun()

# STAGE 3: WORKFLOW COMPLETED STAGE
elif st.session_state.current_stage == "COMPLETED_STAGE":
    st.success("🎉 **Workflow Execution Completed Successfully!**")
    st.write("### Final Customer Output:")
    st.info(st.session_state.latest_output)
    
    if st.button("🔄 Reset Demo Hub"):
        st.session_state.current_stage = "INPUT_STAGE"
        st.session_state.latest_output = ""
        st.session_state.order_details = None
        st.rerun()