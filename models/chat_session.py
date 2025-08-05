from datetime import datetime
from pathlib import Path
import json
import uuid

class ChatSession:
    def __init__(self, user_name, session_id=None):
        self.session_id = session_id or str(uuid.uuid4())
        self.user_name = user_name
        self.start_time = datetime.now()
        self.messages = []
        self.session_data = {
            "emotion": None,
            "mental_health_status": None,
            "topics_discussed": set(),
            "agents_used": set(),
            "sentiment_scores": []
        }
    
    def add_message(self, role, content, agent=None, metadata=None):
        message = {
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content,
            "agent": agent,
            "metadata": metadata or {}
        }
        self.messages.append(message)
        
        if agent and hasattr(self.session_data["agents_used"], 'add'):
            self.session_data["agents_used"].add(agent)
    
    def add_topic(self, topic):
        """Safely add a topic"""
        if hasattr(self.session_data["topics_discussed"], 'add'):
            self.session_data["topics_discussed"].add(topic)
        else:
            # If it's a list, convert to set first
            topics = set(self.session_data.get("topics_discussed", []))
            topics.add(topic)
            self.session_data["topics_discussed"] = topics
    
    def to_dict(self):
        return {
            "session_id": self.session_id,
            "user_name": self.user_name,
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "duration_minutes": (datetime.now() - self.start_time).seconds // 60,
            "messages": self.messages,
            "total_messages": len(self.messages),
            "session_data": {
                **self.session_data,
                "topics_discussed": list(self.session_data["topics_discussed"]) if isinstance(self.session_data["topics_discussed"], set) else self.session_data["topics_discussed"],
                "agents_used": list(self.session_data["agents_used"]) if isinstance(self.session_data["agents_used"], set) else self.session_data["agents_used"]
            }
        }
    
    @classmethod
    def from_dict(cls, data, user_name=None):
        """Create a ChatSession from dictionary data"""
        session = cls(user_name or data.get('user_name', 'Guest'), data.get('session_id'))
        session.messages = data.get('messages', [])
        
        # Reconstruct session_data with proper types
        stored_data = data.get('session_data', {})
        session.session_data = {
            "emotion": stored_data.get('emotion'),
            "mental_health_status": stored_data.get('mental_health_status'),
            "topics_discussed": set(stored_data.get('topics_discussed', [])),
            "agents_used": set(stored_data.get('agents_used', [])),
            "sentiment_scores": stored_data.get('sentiment_scores', [])
        }
        
        return session
    
    def save(self, directory="chat_sessions"):
        Path(directory).mkdir(exist_ok=True)
        filename = f"{directory}/chat_{self.user_name}_{self.start_time.strftime('%Y%m%d_%H%M%S')}_{self.session_id[:8]}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        
        return filename