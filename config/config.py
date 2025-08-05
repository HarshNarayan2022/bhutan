"""
Configuration loader for the Mental Health Chatbot
"""

import os
import yaml
from dataclasses import dataclass
from typing import Any, Dict, Optional
from pathlib import Path

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from sentence_transformers import SentenceTransformer


@dataclass
class RAGConfig:
    """Configuration for RAG agent"""
    def __init__(self, config_dict: Dict[str, Any]):
        self.config_dict = config_dict
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.3,
            google_api_key=os.environ.get("GOOGLE_API_KEY")
        )
        
        # Load from YAML if available
        if 'rag' in config_dict:
            rag_config = config_dict['rag']
            self.embedding_dim = rag_config.get('embedding_dim', 384)
            
            # Use SentenceTransformer for consistency
            self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            
            self.collection_name = rag_config.get('collection_name', 'mental_health_docs')
            self.chunk_size = rag_config.get('chunk_size', 256)
            self.chunk_overlap = rag_config.get('chunk_overlap', 32)
            self.reranker_model = rag_config.get('reranker_model', 'cross-encoder/ms-marco-MiniLM-L-6-v2')
            self.reranker_top_k = rag_config.get('reranker_top_k', 5)
            self.max_context_length = rag_config.get('max_context_length', 2048)
            self.include_sources = rag_config.get('include_sources', True)
            self.use_local = rag_config.get('use_local', True)
            self.url = rag_config.get('url', 'http://localhost:6333')
            self.distance_metric = rag_config.get('distance_metric', 'Cosine')  # Changed to 'Cosine'
            self.min_retrieval_confidence = rag_config.get('min_retrieval_confidence', 0.85)
            
            # Add missing attributes
            self.processed_docs_dir = rag_config.get('processed_docs_dir', 'processed_docs')
            self.knowledge_dir = rag_config.get('knowledge_dir', 'knowledge')
        else:
            # Default values if no YAML config
            self.embedding_dim = 384
            self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            self.collection_name = 'mental_health_docs'
            self.chunk_size = 256
            self.chunk_overlap = 32
            self.reranker_model = 'cross-encoder/ms-marco-MiniLM-L-6-v2'
            self.reranker_top_k = 5
            self.max_context_length = 2048
            self.include_sources = True
            self.use_local = True
            self.url = 'http://localhost:6333'
            self.distance_metric = 'Cosine'  # Changed to 'Cosine'
            self.min_retrieval_confidence = 0.85
            self.processed_docs_dir = 'processed_docs'
            self.knowledge_dir = 'knowledge'
            
        self.context_limit = 4


@dataclass
class ConversationConfig:
    """Configuration for Conversation agent"""
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.7,
            google_api_key=os.environ.get("GOOGLE_API_KEY")
        )


@dataclass
class WebSearchConfig:
    """Configuration for Web Search agent"""
    def __init__(self):
        self.context_limit = 4
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.5,
            google_api_key=os.environ.get("GOOGLE_API_KEY")
        )
        # Add Tavily API key configuration
        self.tavily_api_key = os.environ.get("TAVILY_API_KEY", "tvly-your-api-key-here")


@dataclass
class AgentDecisionConfig:
    """Configuration for Agent Decision system"""
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0,
            google_api_key=os.environ.get("GOOGLE_API_KEY")
        )


class Config:
    """Main configuration class that loads from YAML files"""
    
    def __init__(self):
        # Set API keys
        os.environ["GOOGLE_API_KEY"] = "AIzaSyDzBTzKt211XwMurywdk5HFCnFeeFxcRJ0"
        os.environ["TAVILY_API_KEY"] = "tvly-your-api-key-here"  # You need to replace this
        
        # Load YAML configurations
        self.config_dict = self._load_yaml_configs()
        
        # Initialize configurations
        self.rag = RAGConfig(self.config_dict)
        self.conversation = ConversationConfig()
        self.web_search = WebSearchConfig()
        self.agent_decision = AgentDecisionConfig()
        
        # General settings
        self.max_conversation_history = 20
        
    def _load_yaml_configs(self) -> Dict[str, Any]:
        """Load all YAML configuration files"""
        config_dict = {}
        config_dir = Path(__file__).parent
        
        # Load each YAML file
        yaml_files = ['agents.yaml', 'rag.yaml', 'tasks.yaml']
        for yaml_file in yaml_files:
            file_path = config_dir / yaml_file
            if file_path.exists():
                with open(file_path, 'r') as f:
                    data = yaml.safe_load(f)
                    if data:
                        config_dict.update(data)
        
        return config_dict
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get configuration for a specific agent"""
        return self.config_dict.get(agent_name, {})
    
    def get_task_config(self, task_name: str) -> Dict[str, Any]:
        """Get configuration for a specific task"""
        return self.config_dict.get(task_name, {})