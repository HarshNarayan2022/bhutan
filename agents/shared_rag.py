import logging
import threading
import time
from sentence_transformers import SentenceTransformer
from langchain_google_genai import ChatGoogleGenerativeAI
from config.config import Config
from agents.rag_agent import MedicalRAG

logger = logging.getLogger(__name__)

class SharedRAG:
    """Singleton RAG instance for sharing across FastAPI and Flask backends."""
    
    _instance = None
    _lock = threading.Lock()
    _initialized = False
    _initialization_time = None
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(SharedRAG, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            current_time = time.time()
            logger.info("🚀 Initializing shared RAG instance...")
            
            # Initialize config
            self.config = Config()
            
            # Initialize models (lazy loading for memory optimization)
            logger.info("📊 Embedding model will be loaded when needed...")
            self.embedding_model = None
            
            logger.info("🤖 Loading LLM...")
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash", 
                temperature=0.1,
                max_tokens=1024
            )
            
            # Initialize RAG
            logger.info("📚 Initializing MedicalRAG...")
            self.rag = MedicalRAG(self.config, self.llm, self.get_embedding_model)
            
            # Ensure knowledge is ingested
            self._ensure_knowledge_ingested()
            
            SharedRAG._initialized = True
            SharedRAG._initialization_time = current_time
            logger.info(f"✅ Shared RAG instance ready in {time.time() - current_time:.2f}s")
        except Exception as e:
            logger.error(f"❌ Error initializing SharedRAG: {str(e)}")
            raise e
    
    def get_embedding_model(self):
        """Lazy load the embedding model only when needed"""
        if self.embedding_model is None:
            try:
                logger.info("📊 Loading embedding model...")
                self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("✅ Embedding model loaded successfully")
            except Exception as e:
                logger.error(f"⚠️ Failed to load embedding model: {e}")
                return None
        return self.embedding_model
    
    def _ensure_knowledge_ingested(self):
        """Ensure knowledge base is populated."""
        try:
            # Check if collection has documents
            collection_info = self.rag.retriever.get_collection_info()
            existing_vectors = collection_info.get('points_count', 0)
            
            logger.info(f"📋 Collection status: {existing_vectors} documents")
            
            if existing_vectors == 0:
                logger.info("📥 Empty collection, ingesting knowledge...")
                result = self.rag.ingest_knowledge_folder("knowledge")
                logger.info(f"✅ Ingestion complete: {result.get('successful', 0)} files processed")
            else:
                # Test retrieval with a simple query
                test_embedding = self.rag.embedding_model.encode("depression")
                test_results = self.rag.retriever.retrieve(test_embedding, top_k=1)
                logger.info(f"✅ Knowledge base ready: {len(test_results)} test results")
                
        except Exception as e:
            logger.error(f"❌ Error checking/ingesting knowledge: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def get_rag(self):
        """Get the RAG instance."""
        current_time = time.time()
        
        # Check if recently initialized (within 30 seconds)
        if (self._initialized and 
            self._initialization_time and 
            (current_time - self._initialization_time) < 30):
            logger.info(f"⚡ RAG ready ({current_time - self._initialization_time:.1f}s ago)")
        
        return self.rag
    
    def reingest_knowledge(self):
        """Force re-ingestion of knowledge base."""
        try:
            logger.info("🔄 Force reingesting knowledge...")
            self.rag.retriever.clear_collection()
            result = self.rag.ingest_knowledge_folder("knowledge")
            logger.info(f"✅ Reingestion complete: {result}")
            return result
        except Exception as e:
            logger.error(f"❌ Error reingesting knowledge: {e}")
            raise

    def get_status(self):
        """Get system status for debugging."""
        try:
            collection_info = self.rag.retriever.get_collection_info()
            return {
                "initialized": self._initialized,
                "initialization_time": self._initialization_time,
                "collection_points": collection_info.get('points_count', 0),
                "crewai_enabled": getattr(self.rag, 'crewai_enabled', False),
                "embedding_model": str(type(self.embedding_model)),
                "llm_model": str(type(self.llm))
            }
        except Exception as e:
            return {"error": str(e)}

# Create singleton instance
shared_rag_instance = SharedRAG()