from pathlib import Path
from typing import Dict, Any, List, Optional
from sentence_transformers import SentenceTransformer
import logging
from config.config import Config

from .vector_store import QdrantRetriever
from .document_processor import MedicalDocumentProcessor
from .query_processor import QueryProcessor
from .reranker import Reranker
from .response_generator import ResponseGenerator
from .data_ingestion import MedicalDataIngestion
import json

from dotenv import load_dotenv
load_dotenv()


class MedicalRAG:
    """
    Medical Retrieval-Augmented Generation system that integrates all components.
    """
    def __init__(self, config: Config, llm, embedding_model):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        self.config = config
        self.llm = llm
        self.embedding_model = embedding_model or SentenceTransformer("all-MiniLM-L6-v2")

        if not self.embedding_model:
            raise ValueError("Embedding model is required for document processing")
        
        # Get chunking parameters from config
        self.chunk_size = getattr(config.rag, 'chunk_size', 256)
        self.chunk_overlap = getattr(config.rag, 'chunk_overlap', 50)
        self.chunking_strategy = getattr(config.rag, 'chunking_strategy', 'hybrid')
        
        # Ensure processed docs directory exists
        self.processed_docs_dir = Path(getattr(config.rag, 'processed_docs_dir', 'processed_docs'))
        self.processed_docs_dir.mkdir(exist_ok=True)
        
        # Initialize CrewAI integration
        self.crewai_enabled = True
        try:
            self._initialize_crewai_agents()
            self.logger.info("✅ CrewAI agents initialized successfully")
        except Exception as e:
            self.logger.warning(f"⚠️ CrewAI agents not available: {e}")
            self.crewai_enabled = False
        
        # Initialize core components
        try:
            self.retriever = QdrantRetriever(config)
            self.document_processor = MedicalDocumentProcessor(config, self.embedding_model)
            self.query_processor = QueryProcessor(config, self.embedding_model)
            self.reranker = Reranker(config)
            self.response_generator = ResponseGenerator(config, llm)
            self.data_ingestion = MedicalDataIngestion()
            
            self.logger.info(f"✅ MedicalRAG initialized - Embedding dim: {getattr(config.rag, 'embedding_dim', 'unknown')}")
            
        except Exception as e:
            self.logger.error(f"❌ Error initializing MedicalRAG components: {e}")
            raise

    def _initialize_crewai_agents(self):
        """Initialize CrewAI agents from crew_ai module"""
        from crew_ai.chatbot import (
            run_crisis_check,
            run_condition_classification,
            run_user_profile_retrieval,
            run_recommendations
        )
        
        # Store CrewAI functions
        self.run_crisis_check = run_crisis_check
        self.run_condition_classification = run_condition_classification
        self.run_user_profile_retrieval = run_user_profile_retrieval
        self.run_recommendations = run_recommendations

    def ingest_knowledge_folder(self, folder_path: str) -> Dict[str, Any]:
        """
        Ingest all documents from a knowledge folder.
        """
        folder = Path(folder_path)
        if not folder.exists():
            self.logger.error(f"Knowledge folder not found: {folder_path}")
            return {"error": f"Folder not found: {folder_path}"}
        
        ingestion_results = {
            "total_files": 0,
            "successful": 0,
            "failed": 0,
            "files": [],
            "total_chunks": 0
        }
        
        # Get all supported files
        supported_extensions = ['.txt', '.pdf', '.md', '.json', '.csv']
        files = []
        for ext in supported_extensions:
            files.extend(folder.glob(f'*{ext}'))
        
        ingestion_results["total_files"] = len(files)
        
        if not files:
            self.logger.warning(f"No supported files found in {folder_path}")
            return ingestion_results
        
        self.logger.info(f"Found {len(files)} files to ingest")
        
        for file_path in files:
            try:
                self.logger.info(f"Ingesting {file_path.name}...")
                
                # Load and process document
                documents = self.data_ingestion.load_document(str(file_path))
                if not documents:
                    self.logger.warning(f"No content extracted from {file_path.name}")
                    ingestion_results["failed"] += 1
                    continue
                
                # Create chunks
                chunks = self.document_processor.process_documents(documents)
                self.logger.info(f"Created {len(chunks)} chunks from {file_path.name}")
                
                # Store in vector database
                stored_count = self.retriever.add_documents(chunks)
                
                ingestion_results["successful"] += 1
                ingestion_results["total_chunks"] += len(chunks)
                ingestion_results["files"].append({
                    "name": file_path.name,
                    "status": "success",
                    "chunks": len(chunks),
                    "stored": stored_count
                })
                
            except Exception as e:
                self.logger.error(f"Error ingesting {file_path.name}: {str(e)}")
                ingestion_results["failed"] += 1
                ingestion_results["files"].append({
                    "name": file_path.name,
                    "status": "error",
                    "error": str(e)
                })
        
        self.logger.info(f"Ingestion complete: {ingestion_results['successful']}/{ingestion_results['total_files']} files processed")
        return ingestion_results

    def process_query(self, query: str, user_emotion: Optional[str] = None, 
                    mental_health_status: Optional[str] = None,
                    user_context: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """Process a query using the RAG pipeline with emotion and health status awareness."""
        try:
            # Extract and validate parameters
            user_emotion = user_emotion or 'neutral'
            mental_health_status = mental_health_status or 'Unknown'
            user_context = user_context or {}
            
            self.logger.info(f"[RAG] Processing query: {query[:50]}...")
            self.logger.info(f"[RAG] User emotion: {user_emotion}, Status: {mental_health_status}")
            
            # Process query metadata (NOT recursive call)
            query_metadata = self.query_processor.process_query(query)
            enhanced_query = query_metadata.get('expanded_query', query)
            
            print(f"[RAG] Enhanced query: {enhanced_query}")
            
            # Generate embedding and retrieve documents
            query_embedding = self.embedding_model.encode(enhanced_query)
            retrieved_docs = self.retriever.retrieve(
                query_embedding,
                top_k=getattr(self.config.rag, 'top_k', 5),
                metadata_filter=query_metadata.get('filters', {})
            )
            
            print(f"[RAG] Retrieved {len(retrieved_docs)} documents")
            
            # Debug first document
            if retrieved_docs:
                doc = retrieved_docs[0]
                if hasattr(doc, 'page_content'):
                    print(f"[RAG] Top doc: {doc.page_content[:100]}...")
                else:
                    print(f"[RAG] Top doc: {str(doc)[:100]}...")
            else:
                print("[RAG] ⚠️ No documents retrieved!")
            
            # Rerank if enabled
            if self.reranker and retrieved_docs:
                print("[RAG] Reranking documents...")
                reranked_docs = self.reranker.rerank(query, retrieved_docs)
            else:
                reranked_docs = retrieved_docs
            
            # Generate response
            response_data = self.response_generator.generate_response(
                query=query,
                retrieved_docs=reranked_docs, 
                user_emotion=user_emotion,
                mental_health_status=mental_health_status,
                user_context=user_context
            )
            
            # Calculate final confidence
            confidence = response_data.get("confidence", 0.5)
            
            # Boost confidence for personal emotional queries
            if user_emotion not in ['neutral', 'neutral/unsure'] and any(
                phrase in query.lower() for phrase in ["i am", "i feel", "i'm", "my", "me"]
            ):
                confidence_boost = 0.1
                confidence = min(confidence + confidence_boost, 1.0)
                self.logger.info(f"[RAG] Boosted confidence by {confidence_boost} for personal query")
            
            response_data["confidence"] = confidence
            
            print(f"[RAG] Final confidence: {confidence}")
            print(f"[RAG] Response: {response_data.get('response', '')[:100]}...")
            
            return response_data
            
        except Exception as e:
            self.logger.error(f"[RAG] Error processing query: {e}")
            import traceback
            traceback.print_exc()
            return self._generate_error_response(str(e))

    def process_query_with_crewai(self, query: str, user_context: dict = None) -> Dict[str, Any]:
        """Enhanced query processing using CrewAI agents"""
        try:
            if not self.crewai_enabled:
                self.logger.info("[CrewAI] Not enabled, falling back to regular RAG")
                return self.process_query(
                    query, 
                    user_emotion=user_context.get('emotion', 'neutral'),
                    mental_health_status=user_context.get('mental_health_status', 'Unknown'),
                    user_context=user_context
                )
            
            self.logger.info(f"[CrewAI] Processing with agents: {query[:50]}...")
            
            # Step 1: Crisis Detection
            crisis_result = self.run_crisis_check(query)
            is_crisis = crisis_result.get("is_crisis", False)
            
            if is_crisis:
                self.logger.warning("[CrewAI] 🚨 Crisis detected")
                crisis_rec = self.run_recommendations(
                    query, 
                    user_profile=json.dumps(user_context or {}), 
                    condition="Crisis", 
                    answers="{}", 
                    interpretation="N/A", 
                    is_crisis="true"
                )
                return {
                    "response": crisis_rec.get("recommendation", 
                        "🆘 Please contact emergency services immediately: 112 or National Mental Health Program: 1717"),
                    "confidence": 0.95,
                    "method": "crewai_crisis",
                    "agent": "Crisis Detection Agent",
                    "is_crisis": True,
                    "condition": "crisis",
                    "sources": []
                }
            
            # Step 2: Get user profile
            user_id = user_context.get('user_id', 'anon_user')
            try:
                user_profile = self.run_user_profile_retrieval(query, user_id)
            except:
                user_profile = {
                    "id": user_id,
                    "name": user_context.get('name', 'User'),
                    "preferences": "General mental health support"
                }
            
            # Step 3: Classify condition
            try:
                condition_result = self.run_condition_classification(query, json.dumps(user_profile))
                condition = condition_result.get("condition", "general").lower()
            except:
                condition = "general"
            
            self.logger.info(f"[CrewAI] Classified condition: {condition}")
            
            # Step 4: Get RAG results for context
            rag_result = self.process_query(
                query, 
                user_emotion=user_context.get('emotion', 'neutral'),
                mental_health_status=user_context.get('mental_health_status', 'Unknown'),
                user_context=user_context
            )
            
            # Step 5: Generate final recommendation
            final_rec = self.run_recommendations(
                query,
                json.dumps(user_profile),
                condition,
                json.dumps(user_context.get('assessment_answers', {})),
                user_context.get('mental_health_status', 'Unknown'),
                is_crisis="false"
            )
            
            # Combine RAG and CrewAI insights
            combined_response = final_rec.get("recommendation", rag_result.get("response", ""))
            
            return {
                "response": combined_response,
                "confidence": max(rag_result.get("confidence", 0.5), 0.85),
                "method": "crewai_enhanced",
                "agent": "CrewAI Enhanced System",
                "sources": rag_result.get("sources", []),
                "condition": condition,
                "is_crisis": False,
                "rag_confidence": rag_result.get("confidence", 0.5)
            }
            
        except Exception as e:
            self.logger.error(f"[CrewAI] Processing failed: {e}")
            # Fallback to regular RAG
            return self.process_query(
                query, 
                user_emotion=user_context.get('emotion', 'neutral'),
                mental_health_status=user_context.get('mental_health_status', 'Unknown'),
                user_context=user_context
            )

    def _generate_error_response(self, error_message: str) -> Dict[str, Any]:
        """Generate a fallback error response when RAG processing fails."""
        return {
            "response": "I apologize, but I'm experiencing some technical difficulties. For immediate mental health support in Bhutan, please contact:\n\n• National Mental Health Program: 1717 (24/7)\n• Emergency Services: 112\n\nYour mental health matters, and help is available.",
            "confidence": 0.0,
            "sources": [],
            "method": "error_fallback",
            "error": error_message
        }