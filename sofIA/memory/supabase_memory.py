"""
Supabase Memory Manager - Persistent memory using Supabase
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from supabase import create_client, Client

class SupabaseMemoryManager:
    """Supabase-based memory management system for sofIA agent"""
    
    def __init__(self):
        # Initialize Supabase client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY environment variables are required")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
        # Table names
        self.conversations_table = "conversations"
        self.user_preferences_table = "user_preferences"
        self.transactions_table = "transactions"
        self.memory_summaries_table = "memory_summaries"
    
    def save_conversation(self, user_id: str, message: str, response: str, context: Dict[str, Any] = None) -> bool:
        """Save a conversation turn to Supabase"""
        try:
            conversation_data = {
                "user_id": user_id,
                "user_message": message,
                "agent_response": response,
                "context": context or {},
                "timestamp": datetime.now().isoformat(),
                "session_id": context.get("session_id") if context else None,
                "payment_state": context.get("payment_state") if context else None
            }
            
            result = self.supabase.table(self.conversations_table).insert(conversation_data).execute()
            return len(result.data) > 0
            
        except Exception as e:
            print(f"Error saving conversation: {e}")
            return False
    
    def get_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history for a user"""
        try:
            result = self.supabase.table(self.conversations_table)\
                .select("*")\
                .eq("user_id", user_id)\
                .order("timestamp", desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data or []
            
        except Exception as e:
            print(f"Error getting conversation history: {e}")
            return []
    
    def get_conversation_context(self, user_id: str) -> Dict[str, Any]:
        """Get conversation context and summary for a user"""
        try:
            # Get conversation count
            count_result = self.supabase.table(self.conversations_table)\
                .select("id", count="exact")\
                .eq("user_id", user_id)\
                .execute()
            
            conversation_count = count_result.count or 0
            
            # Get recent messages for context
            recent_messages = self.get_conversation_history(user_id, 5)
            
            # Get payment history
            payment_context = self._get_payment_context(user_id)
            
            # Extract topics and intents from recent messages
            recent_topics = self._extract_topics(recent_messages)
            recent_intents = self._extract_intents(recent_messages)
            
            return {
                "user_id": user_id,
                "is_new_user": conversation_count == 0,
                "conversation_count": conversation_count,
                "recent_topics": recent_topics,
                "recent_intents": recent_intents,
                "payment_history": payment_context,
                "last_updated": recent_messages[0]["timestamp"] if recent_messages else None
            }
            
        except Exception as e:
            print(f"Error getting conversation context: {e}")
            return {"user_id": user_id, "is_new_user": True, "conversation_count": 0}
    
    def save_user_preference(self, user_id: str, preference_type: str, value: Any) -> bool:
        """Save user preference to Supabase"""
        try:
            # Check if preference already exists
            existing = self.supabase.table(self.user_preferences_table)\
                .select("id")\
                .eq("user_id", user_id)\
                .eq("preference_type", preference_type)\
                .execute()
            
            preference_data = {
                "user_id": user_id,
                "preference_type": preference_type,
                "preference_value": json.dumps(value) if not isinstance(value, str) else value,
                "updated_at": datetime.now().isoformat()
            }
            
            if existing.data:
                # Update existing preference
                result = self.supabase.table(self.user_preferences_table)\
                    .update(preference_data)\
                    .eq("user_id", user_id)\
                    .eq("preference_type", preference_type)\
                    .execute()
            else:
                # Insert new preference
                result = self.supabase.table(self.user_preferences_table)\
                    .insert(preference_data)\
                    .execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            print(f"Error saving user preference: {e}")
            return False
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences from Supabase"""
        try:
            result = self.supabase.table(self.user_preferences_table)\
                .select("*")\
                .eq("user_id", user_id)\
                .execute()
            
            preferences = {}
            for pref in result.data or []:
                try:
                    # Try to parse as JSON, fallback to string
                    value = json.loads(pref["preference_value"])
                except (json.JSONDecodeError, TypeError):
                    value = pref["preference_value"]
                
                preferences[pref["preference_type"]] = value
            
            return preferences
            
        except Exception as e:
            print(f"Error getting user preferences: {e}")
            return {}
    
    def save_transaction(self, user_id: str, transaction_data: Dict[str, Any]) -> bool:
        """Save transaction to Supabase"""
        try:
            transaction_record = {
                "user_id": user_id,
                "transaction_id": transaction_data.get("transaction_id"),
                "amount": transaction_data.get("amount", 0.0),
                "currency": transaction_data.get("currency", "BRL"),
                "product": transaction_data.get("product", "Unknown"),
                "status": transaction_data.get("status", "completed"),
                "payment_method": transaction_data.get("payment_method", "sofIA"),
                "session_id": transaction_data.get("session_id"),
                "timestamp": datetime.now().isoformat()
            }
            
            result = self.supabase.table(self.transactions_table).insert(transaction_record).execute()
            return len(result.data) > 0
            
        except Exception as e:
            print(f"Error saving transaction: {e}")
            return False
    
    def get_transaction_history(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get transaction history for a user"""
        try:
            result = self.supabase.table(self.transactions_table)\
                .select("*")\
                .eq("user_id", user_id)\
                .order("timestamp", desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data or []
            
        except Exception as e:
            print(f"Error getting transaction history: {e}")
            return []
    
    def get_memory_summary(self, user_id: str) -> str:
        """Get a natural language summary of user's memory for AI context"""
        try:
            context = self.get_conversation_context(user_id)
            preferences = self.get_user_preferences(user_id)
            transactions = self.get_transaction_history(user_id, 3)
            
            summary_parts = []
            
            # User status
            if context["is_new_user"]:
                summary_parts.append("🆕 This is a new user with no previous conversation history.")
            else:
                summary_parts.append(f"👤 Returning user with {context['conversation_count']} previous messages.")
            
            # Recent topics
            if context["recent_topics"]:
                topics_str = ", ".join(context["recent_topics"][:3])
                summary_parts.append(f"💬 Recent topics: {topics_str}")
            
            # Payment history
            if context["payment_history"]["has_payment_history"]:
                payment_ctx = context["payment_history"]
                summary_parts.append(f"💳 {payment_ctx['total_transactions']} transactions, R$ {payment_ctx['total_amount']:.2f} total")
            
            # Recent transactions
            if transactions:
                recent_products = [t["product"] for t in transactions[:2]]
                total_amount = sum(t["amount"] for t in transactions)
                summary_parts.append(f"📊 Recent: {', '.join(recent_products)} (R$ {total_amount:.2f})")
            
            # Preferences
            if preferences:
                pref_items = [f"{k}: {v}" for k, v in list(preferences.items())[:3]]
                summary_parts.append(f"⚙️ Preferences: {', '.join(pref_items)}")
            
            return " | ".join(summary_parts) if summary_parts else "No previous memory available."
            
        except Exception as e:
            print(f"Error generating memory summary: {e}")
            return "Memory summary unavailable."
    
    def _get_payment_context(self, user_id: str) -> Dict[str, Any]:
        """Get payment-related context for user"""
        try:
            transactions = self.get_transaction_history(user_id, 10)
            
            if not transactions:
                return {"has_payment_history": False}
            
            total_amount = sum(t["amount"] for t in transactions)
            recent_amount = transactions[0]["amount"] if transactions else 0
            
            return {
                "has_payment_history": True,
                "total_transactions": len(transactions),
                "total_amount": total_amount,
                "recent_amount": recent_amount,
                "last_transaction_date": transactions[0]["timestamp"] if transactions else None
            }
            
        except Exception as e:
            print(f"Error getting payment context: {e}")
            return {"has_payment_history": False}
    
    def _extract_topics(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Extract conversation topics from recent messages"""
        topics = []
        for msg in messages:
            user_msg = msg.get("user_message", "").lower()
            if any(word in user_msg for word in ["café", "coffee"]):
                topics.append("coffee")
            elif any(word in user_msg for word in ["pix", "transfer"]):
                topics.append("pix_transfer")
            elif any(word in user_msg for word in ["almoço", "lunch"]):
                topics.append("lunch")
            elif any(word in user_msg for word in ["pagamento", "payment"]):
                topics.append("payment")
        return list(set(topics))
    
    def _extract_intents(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Extract payment intents from recent messages"""
        intents = []
        for msg in messages:
            context = msg.get("context", {})
            if context.get("payment_state"):
                intents.append(context["payment_state"])
        return list(set(intents))
    
    def create_tables(self) -> bool:
        """Create required tables in Supabase (for initial setup)"""
        # This would typically be done via Supabase dashboard or migrations
        # For now, we'll just return True and assume tables exist
        print("📋 Supabase tables should be created via dashboard or migrations")
        print("Required tables:")
        print(f"- {self.conversations_table}")
        print(f"- {self.user_preferences_table}")
        print(f"- {self.transactions_table}")
        print(f"- {self.memory_summaries_table}")
        return True
