"""
Custom JSON Encoder for Banking AI Agent
Handles serialization of enums and other custom objects
"""

import json
from enum import Enum
from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import Any

class BankingAIEncoder(json.JSONEncoder):
    """Custom JSON encoder for Banking AI Agent objects"""
    
    def default(self, obj: Any) -> Any:
        """Convert objects to JSON-serializable format"""
        
        # Handle Enum objects
        if isinstance(obj, Enum):
            return obj.value
        
        # Handle dataclass objects
        if is_dataclass(obj):
            return asdict(obj)
        
        # Handle datetime objects
        if isinstance(obj, datetime):
            return obj.isoformat()
        
        # Handle sets
        if isinstance(obj, set):
            return list(obj)
        
        # Let the base class handle other objects
        return super().default(obj)

def safe_json_dumps(obj: Any, **kwargs) -> str:
    """Safely serialize object to JSON string"""
    return json.dumps(obj, cls=BankingAIEncoder, **kwargs)

def safe_json_loads(json_str: str) -> Any:
    """Safely deserialize JSON string to object"""
    return json.loads(json_str)

