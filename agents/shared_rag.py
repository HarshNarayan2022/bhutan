import logging
import threading
import time
from sentence_transformers import SentenceTransformer
from langchain_google_genai import ChatGoogleGenerativeAI
from config.config import Config
from agents.rag_agent import MedicalRAG

logger = logging.getLogger(__name__)

class LazyEmbeddingModel:
    """Lazy loading wrapper for SentenceTransformer model"""
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        
    def _ensure_loaded(self):
        if self._model is None:
            logger.info(f"📊 Loading embedding model: {self.model_name}...")
            self._model = SentenceTransformer(self.model_name)
            logger.info("✅ Embedding model loaded successfully")
        return self._model
        
    def encode(self, *args, **kwargs):
        model = self._ensure_loaded()
        return model.encode(*args, **kwargs)
        
    def __getattr__(self, name):
        # Delegate all other attributes to the actual model
        model = self._ensure_loaded()
        return getattr(model, name)

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
            
            try:
                # Initialize config
                self.config = Config()
                
                # Initialize models (lazy loading for memory optimization)
                logger.info("📊 Embedding model will be loaded when needed...")
                self.embedding_model = LazyEmbeddingModel("all-MiniLM-L6-v2")
                
                logger.info("🤖 Loading LLM...")
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash", 
                    temperature=0.1,
                    max_tokens=1024
                )
                
                # Initialize RAG (will get embedding model when needed)
                logger.info("📚 Initializing MedicalRAG...")
                # Pass the lazy embedding model
                self.rag = MedicalRAG(self.config, self.llm, self.embedding_model)
                
                # Ensure knowledge is ingested
                self._ensure_knowledge_ingested()
                
                SharedRAG._initialized = True
                SharedRAG._initialization_time = current_time
                logger.info(f"✅ Shared RAG instance ready in {time.time() - current_time:.2f}s")
                
            except Exception as e:
                logger.error(f"❌ Error initializing SharedRAG: {str(e)}")
                raise e
    
    def get_embedding_model(self):
        """Get the embedding model (lazy loading wrapper)"""
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
                # Test retrieval with a simple query using lazy-loaded embedding model
                logger.info("✅ Knowledge base ready (testing embedding on-demand)")
                # The embedding model will load automatically when needed
                
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