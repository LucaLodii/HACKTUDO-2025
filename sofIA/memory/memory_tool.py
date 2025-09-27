"""
Memory Tool - Tool for agents to access and manage Supabase memory
"""

from google.adk.tools import Tool
from typing import Dict, Any, List
import json

from .supabase_memory import SupabaseMemoryManager

# Initialize Supabase memory manager
memory_manager = SupabaseMemoryManager()

def get_user_memory_context(user_id: str) -> str:
    """Get comprehensive memory context for a user"""
    try:
        return memory_manager.get_memory_summary(user_id)
    except Exception as e:
        return f"Memory context error: {str(e)}"

def remember_conversation_turn(user_id: str, user_message: str, agent_response: str, context: Dict[str, Any] = None) -> str:
    """Remember a conversation turn"""
    try:
        success = memory_manager.save_conversation(user_id, user_message, agent_response, context)
        return f"✅ Conversation turn remembered for user {user_id}" if success else f"❌ Failed to remember conversation for user {user_id}"
    except Exception as e:
        return f"❌ Failed to remember conversation: {str(e)}"

def remember_user_preference(user_id: str, preference_type: str, value: str) -> str:
    """Remember a user preference"""
    try:
        success = memory_manager.save_user_preference(user_id, preference_type, value)
        return f"✅ Preference '{preference_type}: {value}' remembered for user {user_id}" if success else f"❌ Failed to remember preference for user {user_id}"
    except Exception as e:
        return f"❌ Failed to remember preference: {str(e)}"

def remember_transaction(user_id: str, transaction_data: Dict[str, Any]) -> str:
    """Remember a completed transaction"""
    try:
        success = memory_manager.save_transaction(user_id, transaction_data)
        return f"✅ Transaction remembered for user {user_id}" if success else f"❌ Failed to remember transaction for user {user_id}"
    except Exception as e:
        return f"❌ Failed to remember transaction: {str(e)}"

def get_recent_conversation(user_id: str, limit: int = 3) -> str:
    """Get recent conversation history"""
    try:
        recent_messages = memory_manager.get_conversation_history(user_id, limit)
        
        if not recent_messages:
            return "No recent conversation history available."
        
        conversation_text = []
        for msg in recent_messages:
            user_msg = msg.get("user_message", "")
            agent_msg = msg.get("agent_response", "")
            timestamp = msg.get("timestamp", "")
            
            conversation_text.append(f"[{timestamp[:19]}] User: {user_msg}")
            conversation_text.append(f"[{timestamp[:19]}] sofIA: {agent_msg[:100]}...")
        
        return "\n".join(conversation_text)
        
    except Exception as e:
        return f"Error retrieving conversation: {str(e)}"

def get_user_insights(user_id: str) -> str:
    """Get user insights and patterns"""
    try:
        # Get conversation context
        conv_context = memory_manager.get_conversation_context(user_id)
        
        # Get transaction history
        transactions = memory_manager.get_transaction_history(user_id, 10)
        
        # Get preferences
        preferences = memory_manager.get_user_preferences(user_id)
        
        insights = []
        
        # User engagement
        if conv_context["conversation_count"] > 10:
            insights.append("🌟 Highly engaged user with extensive conversation history")
        elif conv_context["conversation_count"] > 3:
            insights.append("⭐ Regular user with good conversation history")
        
        # Spending patterns
        if transactions:
            total_amount = sum(t["amount"] for t in transactions)
            avg_amount = total_amount / len(transactions)
            insights.append(f"💳 {len(transactions)} transactions, avg R$ {avg_amount:.2f}")
        
        # Recent activity
        if conv_context.get("recent_topics"):
            topics = conv_context["recent_topics"]
            if "coffee" in topics:
                insights.append("☕ Coffee enthusiast")
            if "pix_transfer" in topics:
                insights.append("💸 Frequent PIX user")
        
        # Preferences
        if preferences:
            if "language" in preferences:
                insights.append(f"🗣️ Prefers {preferences['language']}")
            if "payment_method" in preferences:
                insights.append(f"💳 Prefers {preferences['payment_method']}")
        
        return " | ".join(insights) if insights else "No specific insights available yet."
        
    except Exception as e:
        return f"Error generating insights: {str(e)}"

def get_user_preferences(user_id: str) -> str:
    """Get user preferences as formatted string"""
    try:
        preferences = memory_manager.get_user_preferences(user_id)
        
        if not preferences:
            return "No preferences set yet."
        
        pref_items = [f"{k}: {v}" for k, v in preferences.items()]
        return "User preferences: " + ", ".join(pref_items)
        
    except Exception as e:
        return f"Error retrieving preferences: {str(e)}"

def get_transaction_summary(user_id: str) -> str:
    """Get transaction summary for user"""
    try:
        transactions = memory_manager.get_transaction_history(user_id, 5)
        
        if not transactions:
            return "No transaction history available."
        
        total_amount = sum(t["amount"] for t in transactions)
        recent_products = [t["product"] for t in transactions[:3]]
        
        return f"Recent purchases: {', '.join(recent_products)} (Total: R$ {total_amount:.2f})"
        
    except Exception as e:
        return f"Error retrieving transaction summary: {str(e)}"

# Create the memory tool
memory_tool = Tool(
    name="memory_tool",
    description="Access and manage user memory, conversation history, preferences, and transaction data using Supabase",
    parameters={
        "action": {
            "type": "string",
            "description": "Memory action to perform",
            "enum": [
                "get_context",
                "remember_conversation", 
                "remember_preference",
                "remember_transaction",
                "get_recent_conversation",
                "get_insights",
                "get_preferences",
                "get_transaction_summary"
            ]
        },
        "user_id": {
            "type": "string", 
            "description": "User ID for memory operations"
        },
        "user_message": {
            "type": "string",
            "description": "User message (for conversation memory)"
        },
        "agent_response": {
            "type": "string", 
            "description": "Agent response (for conversation memory)"
        },
        "context": {
            "type": "object",
            "description": "Additional context data"
        },
        "preference_type": {
            "type": "string",
            "description": "Type of preference to remember"
        },
        "preference_value": {
            "type": "string",
            "description": "Value of preference to remember"
        },
        "transaction_data": {
            "type": "object",
            "description": "Transaction data to remember"
        },
        "limit": {
            "type": "integer",
            "description": "Limit for recent conversation retrieval",
            "default": 3
        }
    },
    function=lambda action, user_id, **kwargs: {
        "get_context": lambda: get_user_memory_context(user_id),
        "remember_conversation": lambda: remember_conversation_turn(
            user_id, 
            kwargs.get("user_message", ""), 
            kwargs.get("agent_response", ""), 
            kwargs.get("context")
        ),
        "remember_preference": lambda: remember_user_preference(
            user_id, 
            kwargs.get("preference_type", ""), 
            kwargs.get("preference_value", "")
        ),
        "remember_transaction": lambda: remember_transaction(
            user_id, 
            kwargs.get("transaction_data", {})
        ),
        "get_recent_conversation": lambda: get_recent_conversation(
            user_id, 
            kwargs.get("limit", 3)
        ),
        "get_insights": lambda: get_user_insights(user_id),
        "get_preferences": lambda: get_user_preferences(user_id),
        "get_transaction_summary": lambda: get_transaction_summary(user_id)
    }[action]()
)
