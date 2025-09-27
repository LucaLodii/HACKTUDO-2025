#!/usr/bin/env python3
"""
Test Supabase Connection for sofIA Memory System

This script tests the connection to Supabase and verifies the memory system works.
"""

import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_supabase_connection():
    """Test basic Supabase connection"""
    print("🔧 Testing Supabase Connection...")
    print("=" * 50)
    
    # Check environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    print(f"Supabase URL: {supabase_url}")
    print(f"API Key: {'✅ Set' if supabase_key else '❌ Missing'}")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials")
        return False
    
    try:
        from supabase import create_client, Client
        
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Supabase client created successfully")
        
        # Test connection by querying a table
        try:
            result = supabase.table("conversations").select("*").limit(1).execute()
            print("✅ Database connection successful")
            print(f"📊 Found {len(result.data)} conversation records")
            return True
        except Exception as e:
            print(f"❌ Database query failed: {e}")
            print("💡 Make sure you've run the SQL schema in Supabase")
            return False
            
    except ImportError:
        print("❌ Supabase Python client not installed")
        print("💡 Run: pip install supabase")
        return False
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

def test_memory_system():
    """Test the sofIA memory system"""
    print("\n🧠 Testing sofIA Memory System...")
    print("=" * 50)
    
    try:
        from sofIA.memory.supabase_memory import SupabaseMemoryManager
        
        # Initialize memory manager
        memory_manager = SupabaseMemoryManager()
        
        if memory_manager.supabase is None:
            print("❌ Memory manager using mock mode")
            return False
        
        print("✅ Memory manager initialized with Supabase")
        
        # Test saving a conversation
        test_user_id = "test_user_123"
        test_message = "Hello sofIA!"
        test_response = "Hello! I'm sofIA, your AI payment assistant."
        
        success = memory_manager.save_conversation(
            user_id=test_user_id,
            message=test_message,
            response=test_response,
            context={"payment_state": "idle", "test": True}
        )
        
        if success:
            print("✅ Conversation saved successfully")
        else:
            print("❌ Failed to save conversation")
            return False
        
        # Test retrieving conversation history
        history = memory_manager.get_conversation_history(test_user_id, limit=5)
        print(f"✅ Retrieved {len(history)} conversation records")
        
        # Test getting conversation context
        context = memory_manager.get_conversation_context(test_user_id)
        print(f"✅ Retrieved conversation context: {context.get('conversation_count', 0)} conversations")
        
        return True
        
    except Exception as e:
        print(f"❌ Memory system test failed: {e}")
        return False

def test_agent_integration():
    """Test agent integration with memory system"""
    print("\n🤖 Testing Agent Integration...")
    print("=" * 50)
    
    try:
        from sofIA.memory.memory_tool import memory_tool
        
        # Test memory tool
        test_user_id = "agent_test_user"
        
        # Test getting context
        context_result = memory_tool.execute(
            action="get_context",
            user_id=test_user_id
        )
        
        print("✅ Memory tool executed successfully")
        print(f"📊 Context result: {type(context_result)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent integration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 sofIA Supabase Memory System Test")
    print("=" * 60)
    
    # Test 1: Basic connection
    connection_ok = test_supabase_connection()
    
    if not connection_ok:
        print("\n❌ Basic connection failed. Please check your Supabase setup.")
        return
    
    # Test 2: Memory system
    memory_ok = test_memory_system()
    
    if not memory_ok:
        print("\n❌ Memory system test failed.")
        return
    
    # Test 3: Agent integration
    agent_ok = test_agent_integration()
    
    if not agent_ok:
        print("\n❌ Agent integration test failed.")
        return
    
    print("\n🎉 All tests passed!")
    print("✅ Supabase connection working")
    print("✅ Memory system functional")
    print("✅ Agent integration working")
    print("\n🚀 Your sofIA memory system is ready for the hackathon!")

if __name__ == "__main__":
    main()
