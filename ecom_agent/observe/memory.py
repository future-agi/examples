import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

class Memory:
    """Memory system for the e-commerce agent"""
    
    def __init__(self):
        self.memory_store: List[Dict[str, Any]] = []
    
    def add(self, entry_type: str, content: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add an entry to memory"""
        timestamp = datetime.now().isoformat()
        entry = {
            "id": len(self.memory_store),
            "timestamp": timestamp,
            "type": entry_type,
            "content": content
        }
        
        if metadata:
            entry["metadata"] = metadata
            
        self.memory_store.append(entry)
        return entry
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all memory entries"""
        return self.memory_store
    
    def get_by_type(self, entry_type: str) -> List[Dict[str, Any]]:
        """Get memory entries by type"""
        return [entry for entry in self.memory_store if entry["type"] == entry_type]
    
    def get_recent(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get the most recent memory entries"""
        return self.memory_store[-count:] if len(self.memory_store) >= count else self.memory_store
    
    def clear(self) -> None:
        """Clear all memory entries"""
        self.memory_store = []
