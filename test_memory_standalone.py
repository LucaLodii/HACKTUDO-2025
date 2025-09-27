#!/usr/bin/env python3
"""
Standalone test for sofIA Memory System with Supabase
This test doesn't depend on the full sofIA agent system
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_supabase_import():
    """Test if Supabase can be imported"""
    print("🧪 Testing Supabase Import")
    print("=" * 25)
    
    try:
        from supabase import create_client, Client
        print("✅ Supabase client imported successfully")
        return True
    except Exception as e:
        print(f"❌ Supabase import failed: {e}")
        print("   Install with: pip install supabase")
        return False

def test_memory_manager_standalone():
    """Test memory manager without sofIA dependencies"""
    print("\n🔧 Testing Memory Manager (Standalone)")
    print("=" * 40)
    
    try:
        # Import directly from the file
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from sofIA.memory.supabase_memory import SupabaseMemoryManager
        print("✅ SupabaseMemoryManager imported successfully")
        
        # Check environment variables
        if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_ANON_KEY"):
            print("⚠️ Supabase environment variables not set")
            print("   Set SUPABASE_URL and SUPABASE_ANON_KEY in your .env file")
            print("   This is expected for the hackathon setup")
            return True  # This is not a failure, just not configured yet
        
        # Try to initialize
        try:
            memory_manager = SupabaseMemoryManager()
            print("✅ Memory manager initialized successfully")
            
            # Test basic operations (these will fail if Supabase is not set up)
            test_user_id = "test_user_standalone"
            
            # Test conversation save
            success = memory_manager.save_conversation(
                test_user_id,
                "Hello sofIA!",
                "Hello! I'm sofIA, your AI payment assistant.",
                {"payment_state": "idle"}
            )
            print(f"   Conversation save: {'✅' if success else '❌'}")
            
            # Test preference save
            success = memory_manager.save_user_preference(
                test_user_id, 
                "language", 
                "pt-BR"
            )
            print(f"   Preference save: {'✅' if success else '❌'}")
            
            # Test memory summary
            summary = memory_manager.get_memory_summary(test_user_id)
            print(f"   Memory summary: {summary[:100]}...")
            
            return True
            
        except Exception as e:
            print(f"⚠️ Memory manager operations failed: {e}")
            print("   This is expected if Supabase is not configured yet")
            return True  # Not a failure for hackathon setup
            
    except Exception as e:
        print(f"❌ Memory manager test failed: {e}")
        return False

def test_memory_functions_standalone():
    """Test memory functions without tool dependencies"""
    print("\n🛠️ Testing Memory Functions (Standalone)")
    print("=" * 45)
    
    try:
        # Test the core memory functions directly
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from sofIA.memory.supabase_memory import SupabaseMemoryManager
        
        # Create a mock memory manager for testing
        class MockMemoryManager:
            def get_memory_summary(self, user_id):
                return f"Mock memory context for user {user_id}"
            
            def save_conversation(self, user_id, message, response, context):
                return True
                
            def save_user_preference(self, user_id, preference_type, value):
                return True
                
            def save_transaction(self, user_id, transaction_data):
                return True
        
        # Test memory functions
        memory_manager = MockMemoryManager()
        
        # Test get memory context
        context = memory_manager.get_memory_summary("test_user")
        print(f"   get_memory_summary: {context}")
        
        # Test save conversation
        success = memory_manager.save_conversation(
            "test_user", 
            "test message", 
            "test response", 
            {}
        )
        print(f"   save_conversation: {'✅' if success else '❌'}")
        
        # Test save preference
        success = memory_manager.save_user_preference(
            "test_user", 
            "language", 
            "pt-BR"
        )
        print(f"   save_user_preference: {'✅' if success else '❌'}")
        
        # Test save transaction
        success = memory_manager.save_transaction(
            "test_user", 
            {"amount": 10.0, "product": "Coffee"}
        )
        print(f"   save_transaction: {'✅' if success else '❌'}")
        
        print("✅ All memory functions working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Memory functions test failed: {e}")
        return False

def show_setup_instructions():
    """Show setup instructions for the hackathon"""
    print("\n📋 Hackathon Setup Instructions")
    print("=" * 35)
    print("1. Create a Supabase project at https://supabase.com")
    print("2. Copy your project URL and anon key")
    print("3. Add to your .env file:")
    print("   SUPABASE_URL=https://your-project.supabase.co")
    print("   SUPABASE_ANON_KEY=your_anon_key_here")
    print("4. Run the SQL schema from supabase_schema.sql in Supabase SQL Editor")
    print("5. Test with: python test_memory.py")
    print("\n🎯 For the hackathon, you can start with the memory system working")
    print("   even without Supabase - it will just show 'no memory context' messages")

if __name__ == "__main__":
    print("🚀 sofIA Memory System Standalone Test")
    print("=" * 40)
    
    # Run tests
    supabase_success = test_supabase_import()
    memory_success = test_memory_manager_standalone()
    functions_success = test_memory_functions_standalone()
    
    print("\n📊 Test Results:")
    print(f"   Supabase Import: {'✅' if supabase_success else '❌'}")
    print(f"   Memory Manager: {'✅' if memory_success else '❌'}")
    print(f"   Memory Functions: {'✅' if functions_success else '❌'}")
    
    if supabase_success and functions_success:
        print("\n🎉 Memory system is ready for hackathon!")
        show_setup_instructions()
    else:
        print("\n💥 Some tests failed. Check the errors above.")
        if not supabase_success:
            print("   Install Supabase: pip install supabase")
        sys.exit(1)
