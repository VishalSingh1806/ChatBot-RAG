
"""
Search Engine Configuration
Allows easy switching between different search modes
"""

import os
from enum import Enum

class SearchMode(Enum):
    TRADITIONAL = "traditional"  # Original database search + LLM refinement
    HYBRID = "hybrid"           # 60% LLM + 40% Database (simultaneous)
    SEQUENTIAL_HYBRID = "sequential_hybrid"  # DB first (40%), then LLM (60%) if needed
    LLM_ONLY = "llm_only"      # 100% LLM knowledge
    DB_ONLY = "db_only"        # 100% Database search

class SearchConfig:
    def __init__(self):
        # Default search mode - can be changed via environment variable
        self.default_mode = SearchMode(os.getenv("SEARCH_MODE", "hybrid"))
        
        # Hybrid search weights - ALWAYS 60% LLM + 40% Database
        self.llm_weight = 0.6  # Fixed 60%
        self.db_weight = 0.4   # Fixed 40%
    
    def get_search_mode(self) -> SearchMode:
        """Get the current search mode"""
        return self.default_mode
    
    def set_search_mode(self, mode: SearchMode):
        """Set the search mode"""
        self.default_mode = mode
    
    def get_weights(self) -> tuple:
        """Get LLM and DB weights for hybrid search"""
        return self.llm_weight, self.db_weight
    
    def set_weights(self, llm_weight: float, db_weight: float):
        """Set custom weights for hybrid search"""
        total = llm_weight + db_weight
        self.llm_weight = llm_weight / total
        self.db_weight = db_weight / total

# Global configuration instance
search_config = SearchConfig()

def get_search_config() -> SearchConfig:
    """Get the global search configuration"""
    return search_config