import faiss
import numpy as np
import json
import os
from typing import List, Dict, Any, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class FAISSIndex:
    """
    FAISS index for efficient similarity search
    Enhanced with advanced retrieval capabilities from the workflow diagram
    """
    
    def __init__(self, embedding_dim: int = 512, index_type: str = "HNSW"):
        self.embedding_dim = embedding_dim
        self.index_type = index_type
        self.index = None
        self.product_metadata = []
        self.index_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "index")
        
        # Create index directory if it doesn't exist
        os.makedirs(self.index_path, exist_ok=True)
        
        self._initialize_index()
        self._load_existing_index()
    
    def _initialize_index(self):
        """
        Initialize FAISS index based on type
        """
        if self.index_type == "HNSW":
            # HNSW index for fast approximate search
            self.index = faiss.IndexHNSWFlat(self.embedding_dim, 32)  # dimension, M (number of connections)
            self.index.hnsw.efConstruction = 200
            self.index.hnsw.efSearch = 100
        elif self.index_type == "IVF":
            # IVF index for large datasets
            quantizer = faiss.IndexFlatIP(self.embedding_dim)
            self.index = faiss.IndexIVFFlat(quantizer, self.embedding_dim, 100)
        else:
            # Default flat index
            self.index = faiss.IndexFlatIP(self.embedding_dim)
        
        logger.info(f"Initialized {self.index_type} index with dimension {self.embedding_dim}")
    
    def _load_existing_index(self):
        """
        Load existing index and metadata if available
        """
        index_file = os.path.join(self.index_path, "products.index")
        metadata_file = os.path.join(self.index_path, "metadata.json")
        
        if os.path.exists(index_file) and os.path.exists(metadata_file):
            try:
                # Load FAISS index
                self.index = faiss.read_index(index_file)
                
                # Load metadata
                with open(metadata_file, 'r') as f:
                    self.product_metadata = json.load(f)
                
                logger.info(f"Loaded existing index with {len(self.product_metadata)} products")
                
            except Exception as e:
                logger.warning(f"Failed to load existing index: {e}")
                self._initialize_index()
    
    def add_product(self, embedding: np.ndarray, metadata: Dict[str, Any]):
        """
        Add a product embedding and metadata to the index
        """
        if embedding.ndim == 1:
            embedding = embedding.reshape(1, -1)
        
        # Normalize embedding
        embedding = embedding / np.linalg.norm(embedding, axis=1, keepdims=True)
        
        # Add to FAISS index
        self.index.add(embedding.astype(np.float32))
        
        # Add metadata
        self.product_metadata.append(metadata)
        
        logger.debug(f"Added product {metadata.get('product_id', 'unknown')} to index")
    
    def add_batch_products(self, embeddings: np.ndarray, metadata_list: List[Dict[str, Any]]):
        """
        Add multiple products to the index
        """
        # Normalize embeddings
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        
        # Add to FAISS index
        self.index.add(embeddings.astype(np.float32))
        
        # Add metadata
        self.product_metadata.extend(metadata_list)
        
        logger.info(f"Added {len(metadata_list)} products to index")
    
    def search(
        self, 
        query_embedding: np.ndarray, 
        top_k: int = 10,
        filter_categories: Optional[List[str]] = None,
        min_score: float = 0.0
    ) -> Tuple[List[Dict[str, Any]], np.ndarray]:
        """
        Search for similar products with enhanced filtering
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            filter_categories: Optional category filter
            min_score: Minimum similarity score threshold
            
        Returns:
            Tuple of (results, scores)
        """
        if len(self.product_metadata) == 0:
            return [], np.array([])
        
        # Normalize query embedding
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
        
        # Search with larger k for filtering
        search_k = min(top_k * 3, len(self.product_metadata))
        
        # Perform search
        distances, indices = self.index.search(query_embedding.astype(np.float32), search_k)
        
        # Convert distances to similarity scores (for IP index)
        scores = distances[0]  # FAISS returns distances, for IP this is similarity
        indices = indices[0]
        
        # Filter results
        filtered_results = []
        filtered_scores = []
        
        for idx, score in zip(indices, scores):
            if idx >= len(self.product_metadata):
                continue
                
            metadata = self.product_metadata[idx]
            
            # Apply score threshold
            if score < min_score:
                continue
            
            # Apply category filter
            if filter_categories and metadata.get('category') not in filter_categories:
                continue
            
            # Add similarity score to metadata - ensure all values are Python types
            result = {}
            for k, v in metadata.items():
                if isinstance(v, np.ndarray):
                    result[k] = v.tolist()
                elif isinstance(v, (np.float32, np.float64)):
                    result[k] = float(v)
                elif isinstance(v, (np.int32, np.int64)):
                    result[k] = int(v)
                else:
                    result[k] = v
            result['similarity_score'] = float(score)
            
            filtered_results.append(result)
            filtered_scores.append(score)
            
            # Stop when we have enough results
            if len(filtered_results) >= top_k:
                break
        
        return filtered_results, np.array(filtered_scores)
    
    def search_with_reranking(
        self,
        query_embedding: np.ndarray,
        reranker_model = None,
        top_k: int = 10,
        rerank_top_k: int = 50
    ) -> Tuple[List[Dict[str, Any]], np.ndarray]:
        """
        Search with optional neural reranking (as shown in workflow diagram)
        
        Args:
            query_embedding: Query embedding
            reranker_model: Optional reranking model
            top_k: Final number of results
            rerank_top_k: Number of candidates for reranking
            
        Returns:
            Reranked results and scores
        """
        # Initial retrieval
        initial_results, initial_scores = self.search(query_embedding, rerank_top_k)
        
        if not reranker_model or len(initial_results) <= top_k:
            return initial_results[:top_k], initial_scores[:top_k]
        
        # Extract embeddings for reranking (this would need to be stored separately)
        # For now, we'll just return the initial results
        # In a full implementation, you'd store product embeddings separately
        
        return initial_results[:top_k], initial_scores[:top_k]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get index statistics
        """
        return {
            "total_products": len(self.product_metadata),
            "embedding_dim": self.embedding_dim,
            "index_type": self.index_type,
            "index_size_mb": self.index.ntotal * self.embedding_dim * 4 / (1024 * 1024) if self.index else 0
        }
    
    def save_index(self):
        """
        Save index and metadata to disk
        """
        try:
            index_file = os.path.join(self.index_path, "products.index")
            metadata_file = os.path.join(self.index_path, "metadata.json")
            
            # Save FAISS index
            faiss.write_index(self.index, index_file)
            
            # Save metadata
            with open(metadata_file, 'w') as f:
                json.dump(self.product_metadata, f, indent=2)
            
            logger.info(f"Saved index with {len(self.product_metadata)} products")
            
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
            raise
    
    def clear_index(self):
        """
        Clear all data from the index
        """
        self._initialize_index()
        self.product_metadata = []
        logger.info("Cleared index")
    
    def update_product(self, product_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Update product metadata (embedding update requires full rebuild)
        
        Args:
            product_id: Product ID to update
            metadata: New metadata
            
        Returns:
            True if updated, False if not found
        """
        for i, existing_metadata in enumerate(self.product_metadata):
            if existing_metadata.get('product_id') == product_id:
                self.product_metadata[i] = metadata
                logger.info(f"Updated product {product_id} metadata")
                return True
        
        logger.warning(f"Product {product_id} not found for update")
        return False
    
    def remove_product(self, product_id: str) -> bool:
        """
        Remove product from index (metadata only - FAISS doesn't support efficient removal)
        
        Args:
            product_id: Product ID to remove
            
        Returns:
            True if removed, False if not found
        """
        # Find and remove from metadata
        for i, metadata in enumerate(self.product_metadata):
            if metadata.get('product_id') == product_id:
                self.product_metadata.pop(i)
                logger.info(f"Removed product {product_id} from metadata. Index rebuild recommended.")
                return True
        
        logger.warning(f"Product {product_id} not found in index")
        return False
    
    def rebuild_index(self, embeddings: np.ndarray, metadata_list: List[Dict[str, Any]]):
        """
        Rebuild the entire index with new data
        
        Args:
            embeddings: All product embeddings
            metadata_list: All product metadata
        """
        logger.info("Rebuilding index...")
        
        # Clear existing index
        self._initialize_index()
        self.product_metadata = []
        
        # Add all products
        self.add_batch_products(embeddings, metadata_list)
        
        # Save to disk
        self.save_index()
        
        logger.info("Index rebuild complete")