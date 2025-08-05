import logging
from typing import List, Dict, Any
from sentence_transformers import CrossEncoder
from langchain_core.documents import Document

class Reranker:
    """
    Reranks retrieved documents using a cross-encoder model for more accurate results.
    """
    def __init__(self, config):
            """
            Initialize the reranker with configuration.
            Args:
                config: Configuration object containing reranker settings
            """
            self.logger = logging.getLogger(__name__)
            try:
                if not hasattr(config.rag, "reranker_model"):
                    raise ValueError("Missing 'reranker_model' in config.rag. Please add it to config/rag.yaml.")
                self.model_name = config.rag.reranker_model
                self.logger.info(f"Loading reranker model: {self.model_name}")
                self.model = CrossEncoder(self.model_name)
                self.top_k = getattr(config.rag, "reranker_top_k", 5)
            except Exception as e:
                self.logger.error(f"Error loading reranker model: {e}")
                raise

    def rerank(self, query: str, documents: List[Document], top_k: int = 5) -> List[Document]:
        """
        Rerank documents based on relevance to the query.
        
        Args:
            query: The user query
            documents: List of Document objects to rerank
            top_k: Number of top documents to return
            
        Returns:
            List of reranked Document objects
        """
        if not documents:
            return []
        
        try:
            # Create pairs of (query, document_content) for the reranker
            pairs = []
            for doc in documents:
                # Use doc.page_content instead of doc['content']
                content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
                pairs.append([query, content])
            
            # Get scores from the reranker
            scores = self.model.predict(pairs)
            
            # Combine documents with their scores
            doc_scores = list(zip(documents, scores))
            
            # Sort by score (descending)
            doc_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Return top_k documents
            reranked_docs = [doc for doc, score in doc_scores[:top_k]]
            
            self.logger.info(f"Reranked {len(documents)} documents, returning top {len(reranked_docs)}")
            return reranked_docs
            
        except Exception as e:
            self.logger.error(f"Error during reranking: {e}")
            self.logger.warning("Falling back to original ranking")
            return documents[:top_k]