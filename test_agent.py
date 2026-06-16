import unittest
from graph_engine import compiled_agent

class TestRetailAgentPipeline(unittest.TestCase):

    def setUp(self):
        """
        Fixturing method: Executed automatically before every single test case.
        Provides a unique thread_id to configure and isolate LangGraph memory checkpoints.
        """
        self.config = {"configurable": {"thread_id": "test_session_123"}}

    def test_general_qa_shipping_path(self):
        """
        Test Case 1: Dynamic Knowledge Base Retrieval.
        Verifies if customer queries regarding shipping successfully route to the 
        General QA Agent and pull accurate policy data from the SQLite FAQ database.
        """
        inputs = {"user_query": "Can you tell me how long shipping takes?"}
        
        # Invoke the active multi-agent compilation workflow
        output_state = compiled_agent.invoke(inputs, config=self.config)
        
        # State Assertions: Validate routing behavior and payload content integrity
        self.assertEqual(output_state["category"], "general_qa")
        self.assertIn("[Fetched from Secure DB]", output_state["final_output"])
        self.assertIn("3-5 business days", output_state["final_output"])

    def test_refund_rejected_path(self):
        """
        Test Case 2: Expired Policy Enforcement Engine.
        Verifies if an invalid order (e.g., John's order which has passed 45 days) 
        is safely fetched from the SQL orders table and rejected automatically by compliance node.
        """
        inputs = {"user_query": "I need a refund for FR-99821"}
        
        output_state = compiled_agent.invoke(inputs, config=self.config)
        
        # State Assertions: Ensure strict evaluation of the 30-day return window boundary
        self.assertEqual(output_state["category"], "refund")
        self.assertEqual(output_state["order_id"], "FR-99821")
        self.assertIn("rejected because the 30-day return window passed", output_state["final_output"])

    def test_router_fallback_unknown_id(self):
        """
        Test Case 3: Graceful Exception Handling and Fallback Architecture.
        Verifies if an unregistered/non-existent Order ID is handled securely at the 
        database node without throwing critical KeyErrors or crashing the operational pipeline.
        """
        inputs = {"user_query": "Please refund my order FR-00000"}
        
        output_state = compiled_agent.invoke(inputs, config=self.config)
        
        # State Assertions: Confirm structured error response messaging
        self.assertEqual(output_state["category"], "refund")
        self.assertIn("Refused: Order ID FR-00000 not found", output_state["final_output"])

if __name__ == "__main__":
    # Execute the test suite discovery engine
    unittest.main()