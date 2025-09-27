#!/usr/bin/env python3
"""
Simple test for sofIA Memory System with Supabase (without full agent dependencies)
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_memory_imports():
    """Test if memory system can be imported without full agent dependencies"""
    print("🧪 Testing sofIA Memory System Imports")
    print("=" * 40)
    
    try:
        # Test direct import of memory components
        from sofIA.memory.supabase_memory import SupabaseMemoryManager
        print("✅ SupabaseMemoryManager imported successfully")
        
        from sofIA.memory.memory_tool import memory_tool
        print("✅ Memory tool imported successfully")
        
        print("\n✅ All memory imports successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ Memory import failed: {e}")
        return False

def test_memory_initialization():
    """Test memory manager initialization"""
    print("\n🔧 Testing Memory Manager Initialization")
    print("=" * 40)
    
    try:
        from sofIA.memory.supabase_memory import SupabaseMemoryManager
        
        # Check if environment variables are set
        if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_ANON_KEY"):
            print("⚠️ Supabase environment variables not set")
            print("   Set SUPABASE_URL and SUPABASE_ANON_KEY in your .env file")
            return False
        
        # Try to initialize (this will fail if Supabase is not accessible)
        try:
            memory_manager = SupabaseMemoryManager()
            print("✅ Memory manager initialized successfully")
            return True
        except Exception as e:
            print(f"⚠️ Memory manager initialization failed: {e}")
            print("   This is expected if Supabase is not configured yet")
            return False
            
    except Exception as e:
        print(f"❌ Memory initialization test failed: {e}")
        return False

def test_memory_tool_functions():
    """Test memory tool function definitions"""
    print("\n🛠️ Testing Memory Tool Functions")
    print("=" * 35)
    
    try:
        from sofIA.memory.memory_tool import (
            get_user_memory_context,
            remember_conversation_turn,
            remember_user_preference,
            remember_transaction,
            get_recent_conversation,
            get_user_insights
        )
        
        print("✅ All memory tool functions imported successfully")
        
        # Test function signatures
        test_user_id = "test_user"
        
        # These should work even without Supabase connection
        context = get_user_memory_context(test_user_id)
        print(f"   get_user_memory_context: {context[:50]}...")
        
        conv_result = remember_conversation_turn(
            test_user_id, 
            "test message", 
            "test response"
        )
        print(f"   remember_conversation_turn: {conv_result[:50]}...")
        
        print("✅ Memory tool functions working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Memory tool test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 sofIA Memory System Simple Test")
    print("=" * 35)
    
    # Run tests
    import_success = test_memory_imports()
    init_success = test_memory_initialization()
    tool_success = test_memory_tool_functions()
    
    print("\n📊 Test Results:")
    print(f"   Imports: {'✅' if import_success else '❌'}")
    print(f"   Initialization: {'✅' if init_success else '⚠️'}")
    print(f"   Tool Functions: {'✅' if tool_success else '❌'}")
    
    if import_success and tool_success:
        print("\n🎉 Memory system is ready! You can now:")
        print("   1. Set up your Supabase project")
        print("   2. Run the SQL schema from supabase_schema.sql")
        print("   3. Set SUPABASE_URL and SUPABASE_ANON_KEY in .env")
        print("   4. Run the full test with: python test_memory.py")
    else:
        print("\n💥 Some tests failed. Check the errors above.")
        sys.exit(1)
