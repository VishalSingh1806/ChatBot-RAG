from collections import deque
from typing import Dict, List, Optional
import json
import time

class ContextWindow:
    def __init__(self, max_size: int = 6):
        """Initialize context window with FIFO queue"""
        self.max_size = max_size
        self.sessions: Dict[str, deque] = {}
    
    def add_query(self, session_id: str, user_query: str, bot_response: str = None):
        """Add user query to session context window"""
        if session_id not in self.sessions:
            self.sessions[session_id] = deque(maxlen=self.max_size)
        
        # Add query-response pair with timestamp
        context_item = {
            "timestamp": time.time(),
            "user_query": user_query,
            "bot_response": bot_response,
            "role": "user"
        }
        
        self.sessions[session_id].append(context_item)
    
    def get_context(self, session_id: str) -> List[Dict]:
        """Get conversation context for session"""
        if session_id not in self.sessions:
            return []
        
        return list(self.sessions[session_id])
    
    def get_context_string(self, session_id: str) -> str:
        """Get formatted context string for LLM"""
        context = self.get_context(session_id)
        if not context:
            return ""
        
        context_str = "Previous conversation:\n"
        for item in context:
            context_str += f"User: {item['user_query']}\n"
            if item.get('bot_response'):
                context_str += f"Assistant: {item['bot_response']}\n"
        
        return context_str
    
    def clear_session(self, session_id: str):
        """Clear context for specific session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def update_response(self, session_id: str, bot_response: str):
        """Update the last query with bot response"""
        if session_id in self.sessions and self.sessions[session_id]:
            self.sessions[session_id][-1]["bot_response"] = bot_response

# Global context window instance
context_window = ContextWindow()