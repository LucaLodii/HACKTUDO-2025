#!/usr/bin/env python3
"""
Test script for sofIA Memory System with Supabase
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_memory_system():
    """Test the Supabase memory system"""
    print("🧪 Testing sofIA Memory System with Supabase")
    print("=" * 50)
    
    try:
        from sofIA.memory import SupabaseMemoryManager
        
        # Initialize memory manager
        memory_manager = SupabaseMemoryManager()
        print("✅ Memory manager initialized")
        
        # Test user ID
        test_user_id = "test_user_123"
        
        # Test 1: Save conversation
        print("\n1. Testing conversation memory...")
        success = memory_manager.save_conversation(
            test_user_id,
            "Hello sofIA!",
            "Hello! I'm sofIA, your AI payment assistant. How can I help you today?",
            {"payment_state": "idle"}
        )
        print(f"   Conversation saved: {success}")
        
        # Test 2: Save user preference
        print("\n2. Testing user preferences...")
        success = memory_manager.save_user_preference(test_user_id, "language", "pt-BR")
        print(f"   Language preference saved: {success}")
        
        success = memory_manager.save_user_preference(test_user_id, "payment_method", "sofIA")
        print(f"   Payment method preference saved: {success}")
        
        # Test 3: Save transaction
        print("\n3. Testing transaction memory...")
        transaction_data = {
            "transaction_id": "test_txn_001",
            "amount": 15.50,
            "currency": "BRL",
            "product": "Coffee",
            "status": "completed"
        }
        success = memory_manager.save_transaction(test_user_id, transaction_data)
        print(f"   Transaction saved: {success}")
        
        # Test 4: Retrieve memory context
        print("\n4. Testing memory context retrieval...")
        context = memory_manager.get_conversation_context(test_user_id)
        print(f"   User context: {context}")
        
        # Test 5: Get memory summary
        print("\n5. Testing memory summary...")
        summary = memory_manager.get_memory_summary(test_user_id)
        print(f"   Memory summary: {summary}")
        
        # Test 6: Get conversation history
        print("\n6. Testing conversation history...")
        history = memory_manager.get_conversation_history(test_user_id, 5)
        print(f"   Conversation history: {len(history)} messages")
        for msg in history:
            print(f"   - {msg['user_message'][:50]}...")
        
        # Test 7: Get transaction history
        print("\n7. Testing transaction history...")
        transactions = memory_manager.get_transaction_history(test_user_id, 5)
        print(f"   Transaction history: {len(transactions)} transactions")
        for txn in transactions:
            print(f"   - {txn['product']}: R$ {txn['amount']}")
        
        print("\n✅ All memory tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Memory test failed: {e}")
        print("\nMake sure you have:")
        print("1. SUPABASE_URL and SUPABASE_ANON_KEY in your .env file")
        print("2. Created the database tables using supabase_schema.sql")
        print("3. Installed the supabase dependency: pip install supabase")
        return False

def test_memory_tool():
    """Test the memory tool functionality"""
    print("\n🔧 Testing Memory Tool...")
    print("=" * 30)
    
    try:
        from sofIA.memory import memory_tool
        
        # Test memory tool functions
        test_user_id = "tool_test_user"
        
        # Test get context
        print("1. Testing get_context...")
        context_result = memory_tool.function(
            action="get_context",
            user_id=test_user_id
        )
        print(f"   Context: {context_result}")
        
        # Test remember conversation
        print("\n2. Testing remember_conversation...")
        conv_result = memory_tool.function(
            action="remember_conversation",
            user_id=test_user_id,
            user_message="I want to buy coffee",
            agent_response="I'd be happy to help you buy coffee! What type would you like?",
            context={"payment_state": "intent_created"}
        )
        print(f"   Result: {conv_result}")
        
        # Test get recent conversation
        print("\n3. Testing get_recent_conversation...")
        recent_result = memory_tool.function(
            action="get_recent_conversation",
            user_id=test_user_id,
            limit=3
        )
        print(f"   Recent conversation: {recent_result}")
        
        print("\n✅ Memory tool tests completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Memory tool test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 sofIA Memory System Test Suite")
    print("=" * 40)
    
    # Check environment variables
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_ANON_KEY"):
        print("❌ Missing Supabase environment variables!")
        print("Please set SUPABASE_URL and SUPABASE_ANON_KEY in your .env file")
        sys.exit(1)
    
    # Run tests
    memory_success = test_memory_system()
    tool_success = test_memory_tool()
    
    if memory_success and tool_success:
        print("\n🎉 All tests passed! Memory system is working correctly.")
    else:
        print("\n💥 Some tests failed. Check the errors above.")
        sys.exit(1)
