from typing import List, Dict, Any, Optional, Union
import logging
import uuid
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from qdrant_client.http.exceptions import UnexpectedResponse

# Import Document if available, otherwise define a minimal stub
try:
    from langchain.schema import Document
except ImportError:
    class Document:
        def __init__(self, page_content, metadata):
            self.page_content = page_content
            self.metadata = metadata

class QdrantRetriever:
    """
    Handles storage and retrieval of medical documents using Qdrant vector database.
    """
    def __init__(self, config):
        """
        Initialize the Qdrant retriever with configuration.
        Args:
            config: Configuration object containing Qdrant settings
        """
        self.logger = logging.getLogger(__name__)
        self.collection_name = config.rag.collection_name
        self.embedding_dim = config.rag.embedding_dim
        self.distance_metric = config.rag.distance_metric

           # Force in-memory mode for now
        self.client = QdrantClient(":memory:")

        
        # # Initialize Qdrant client
        # if getattr(config.rag, "use_local", True):
        #     self.client = QdrantClient(
        #         path=config.rag.local_path
        #     )
        # else:
        #     self.client = QdrantClient(
        #         url=getattr(config.rag, "url", None),
        #         api_key=getattr(config.rag, "api_key", None),
        #     )

        # Ensure collection exists
        self._ensure_collection()

    

    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [collection.name for collection in collections]
            if self.collection_name not in collection_names:
                self.logger.info(f"Creating new collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qdrant_models.VectorParams(
                        size=self.embedding_dim,
                        distance=self.distance_metric,
                    ),
                    optimizers_config=qdrant_models.OptimizersConfigDiff(
                        indexing_threshold=10000,
                    ),
                )
                self.logger.info(f"Collection {self.collection_name} created successfully")
        except Exception as e:
            self.logger.error(f"Error creating collection: {e}")
            raise

    def upsert_documents(self, documents: List[Dict[str, Any]]):
        """
        Insert or update documents in the vector database.
        Args:
            documents: List of document dictionaries containing:
                - id: Unique identifier
                - embedding: Vector embedding
                - metadata: Document metadata
                - content: Document content
        """
        try:
            points = []
            for doc in documents:
                points.append(
                    qdrant_models.PointStruct(
                        id=doc["id"],
                        vector=doc["embedding"],
                        payload={
                            "content": doc["content"],
                            "source": doc["metadata"].get("source", ""),
                            "specialty": doc["metadata"].get("specialty", ""),
                            "section": doc["metadata"].get("section", ""),
                            "publication_date": doc["metadata"].get("publication_date", ""),
                            "medical_entities": doc["metadata"].get("medical_entities", []),
                            "chunk_number": doc["metadata"].get("chunk_number", 0),
                            "total_chunks": doc["metadata"].get("total_chunks", 1),
                        }
                    )
                )
            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
                wait=True
            )
            self.logger.info(f"Successfully upserted {len(documents)} documents")
        except Exception as e:
            self.logger.error(f"Error upserting documents: {e}")
            raise

    # Update the retrieve method to properly return Document objects:
    def retrieve(self, query_embedding: np.ndarray, top_k: int = 5, **kwargs) -> List[Document]:
        """
        Retrieve similar documents based on query embedding.
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            **kwargs: Additional parameters (for compatibility)
            
        Returns:
            List of Document objects
        """
        try:
            # Handle the case where query_embedding might be passed as a dict
            if isinstance(query_embedding, dict):
                # If it's a dict, it might be from query_processor
                # Extract the actual embedding
                if 'embedding' in query_embedding:
                    query_embedding = query_embedding['embedding']
                else:
                    self.logger.error(f"Invalid query_embedding format: {type(query_embedding)}")
                    return []
            
            # Ensure query_embedding is a list
            if isinstance(query_embedding, np.ndarray):
                query_vector = query_embedding.tolist()
            else:
                query_vector = list(query_embedding)
            
            # Search in Qdrant
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k
            )
            
            # Convert to Document objects
            documents = []
            for result in search_results:
                # Extract content from payload
                content = result.payload.get('content', '')
                
                # Create metadata including the score
                metadata = {k: v for k, v in result.payload.items() if k != 'content'}
                metadata['score'] = result.score
                metadata['id'] = str(result.id)
                
                # Create Document object
                doc = Document(
                    page_content=content,
                    metadata=metadata
                )
                documents.append(doc)
            
            self.logger.info(f"Retrieved {len(documents)} documents for query")
            return documents
            
        except Exception as e:
            self.logger.error(f"Error retrieving documents: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return []

    def delete_documents(self, document_ids: List[Union[str, int]]):
        """
        Delete documents from the vector database by their IDs.
        Args:
            document_ids: List of document IDs to delete
        """
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=qdrant_models.PointIdsList(
                    points=document_ids
                ),
                wait=True
            )
            self.logger.info(f"Successfully deleted {len(document_ids)} documents")
        except Exception as e:
            self.logger.error(f"Error deleting documents: {e}")
            raise

    def wipe_collection(self):
        """Completely remove and recreate the collection for fresh start."""
        try:
            self.client.delete_collection(self.collection_name)
            self._ensure_collection()
            self.logger.info(f"Collection {self.collection_name} wiped and recreated")
        except Exception as e:
            self.logger.error(f"Error wiping collection: {e}")
            raise

    # Add this method to the QdrantRetriever class:

    def get_collection_info(self) -> Dict:
        """Get information about the collection."""
        try:
            collection = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": collection.vectors_count,
                "points_count": collection.points_count,
                "status": collection.status,
                "config": {
                    "size": collection.config.params.vectors.size,
                    "distance": collection.config.params.vectors.distance
                }
            }
        except Exception as e:
            self.logger.error(f"Error getting collection info: {e}")
            return {"error": str(e), "vectors_count": 0}

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Retrieve statistics of the collection.
        Returns:
            Dictionary containing collection statistics.
        """
        try:
            stats = self.client.get_collection(self.collection_name)
            self.logger.info(f"Collection stats retrieved successfully: {stats}")
            return stats.model_dump()
        except Exception as e:
            self.logger.error(f"Error getting collection stats: {e}")
            raise


    # Add these methods to the QdrantRetriever class:

    def add_documents(self, documents: List[Document]) -> int:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of documents with embeddings
            
        Returns:
            Number of documents added
        """
        if not documents:
            return 0
        
        points = []
        for idx, doc in enumerate(documents):
            if not hasattr(doc, 'metadata') or 'embedding' not in doc.metadata:
                self.logger.warning(f"Document {idx} missing embedding, skipping")
                continue
            
            point_id = str(uuid.uuid4())
            embedding = doc.metadata['embedding']
            
            # Remove embedding from metadata before storing
            metadata = {k: v for k, v in doc.metadata.items() if k != 'embedding'}
            metadata['content'] = doc.page_content
            
            points.append(
                qdrant_models.PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=metadata
                )
            )
        
        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            self.logger.info(f"Added {len(points)} documents to vector store")
        
        return len(points)



    def clear_collection(self):
        """Clear all documents from the collection."""
        try:
            # Delete and recreate the collection
            self.client.delete_collection(self.collection_name)
            self._create_collection()
            self.logger.info(f"Collection {self.collection_name} cleared successfully")
        except Exception as e:
            self.logger.error(f"Error clearing collection: {e}")
            raise