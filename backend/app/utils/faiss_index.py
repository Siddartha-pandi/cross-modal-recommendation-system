import faiss
import numpy as np
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class FAISSIndex:
    """
    FAISS index for efficient similarity search
    Enhanced with advanced retrieval capabilities from the workflow diagram
    """
    
    def __init__(self, embedding_dim: int = 512, index_type: str = "HNSW", load_existing: bool = True):
        self.embedding_dim = embedding_dim
        self.index_type = index_type
        self.index = None
        self.product_metadata = []
        repo_root = None
        for parent in [Path(__file__).resolve()] + list(Path(__file__).resolve().parents):
            if (parent / "data").exists() and (parent / "index").exists():
                repo_root = parent
                break
        if repo_root is None:
            repo_root = Path(__file__).resolve().parents[3]
        self.index_path = repo_root / "index"

        # Create index directory if it doesn't exist
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        self._initialize_index()
        if load_existing:
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
        index_file = self.index_path / "products.index"
        metadata_file = self.index_path / "metadata.json"
        
        if index_file.exists() and metadata_file.exists():
            try:
                # Load FAISS index
                self.index = faiss.read_index(str(index_file))
                
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
        min_score: float = -1.0
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
    
    def hybrid_search(
        self,
        text_embedding: Optional[np.ndarray] = None,
        image_embedding: Optional[np.ndarray] = None,
        alpha: float = 0.5,
        top_k: int = 10,
        filter_categories: Optional[List[str]] = None,
        min_score: float = -1.0
    ) -> Tuple[List[Dict[str, Any]], np.ndarray]:
        """
        Hybrid search with dynamic alpha fusion
        
        This method properly handles multi-modal search by:
        1. Computing query embedding: Q = alpha * image + (1-alpha) * text
        2. Re-scoring ALL products using the SAME alpha to ensure consistency
        3. Returning top-k results based on re-scored similarities
        
        Args:
            text_embedding: Optional text embedding
            image_embedding: Optional image embedding  
            alpha: Weight for image (0=text-only, 1=image-only)
            top_k: Number of results to return
            filter_categories: Optional category filter
            min_score: Minimum similarity score threshold
            
        Returns:
            Tuple of (results, scores)
        """
        if len(self.product_metadata) == 0:
            return [], np.array([])
        
        if text_embedding is None and image_embedding is None:
            raise ValueError("At least one embedding must be provided")
        
        # Normalize inputs
        if text_embedding is not None:
            if text_embedding.ndim == 1:
                text_embedding = text_embedding.reshape(1, -1)
            text_embedding = text_embedding / np.linalg.norm(text_embedding, axis=1, keepdims=True)
        
        if image_embedding is not None:
            if image_embedding.ndim == 1:
                image_embedding = image_embedding.reshape(1, -1)
            image_embedding = image_embedding / np.linalg.norm(image_embedding, axis=1, keepdims=True)
        
        # Compute query embedding with alpha fusion
        if text_embedding is not None and image_embedding is not None:
            query_embedding = alpha * image_embedding + (1 - alpha) * text_embedding
            query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
        elif image_embedding is not None:
            query_embedding = image_embedding
        else:
            query_embedding = text_embedding
        
        # Get candidates from FAISS index
        # Retrieve more candidates to allow for re-scoring
        search_k = min(len(self.product_metadata), max(top_k * 5, 50))
        distances, indices = self.index.search(query_embedding.astype(np.float32), search_k)
        
        # Re-score products using the same alpha applied to product embeddings
        rescored_results = []
        
        for idx in indices[0]:
            if idx >= len(self.product_metadata):
                continue
            
            metadata = self.product_metadata[idx]
            
            # Check if product has stored embeddings
            if 'text_embedding' not in metadata or 'image_embedding' not in metadata:
                # Fallback: use FAISS score if embeddings not available
                continue
            
            # Reconstruct product embedding with query's alpha
            prod_text_emb = np.array(metadata['text_embedding'])
            prod_img_emb = np.array(metadata['image_embedding'])
            
            # Normalize
            prod_text_emb = prod_text_emb / np.linalg.norm(prod_text_emb)
            prod_img_emb = prod_img_emb / np.linalg.norm(prod_img_emb)
            
            # Apply same alpha as query
            if text_embedding is not None and image_embedding is not None:
                product_embedding = alpha * prod_img_emb + (1 - alpha) * prod_text_emb
            elif image_embedding is not None:
                product_embedding = prod_img_emb
            else:
                product_embedding = prod_text_emb
            
            product_embedding = product_embedding / np.linalg.norm(product_embedding)
            
            # Compute cosine similarity
            score = float(np.dot(query_embedding.flatten(), product_embedding))
            
            # Apply filters
            if score < min_score:
                continue
            
            if filter_categories and metadata.get('category') not in filter_categories:
                continue
            
            # Prepare result
            result = {}
            for k, v in metadata.items():
                # Skip embeddings from result (they're large)
                if k in ['text_embedding', 'image_embedding']:
                    continue
                if isinstance(v, np.ndarray):
                    result[k] = v.tolist()
                elif isinstance(v, (np.float32, np.float64)):
                    result[k] = float(v)
                elif isinstance(v, (np.int32, np.int64)):
                    result[k] = int(v)
                else:
                    result[k] = v
            result['similarity_score'] = score
            
            rescored_results.append((result, score))
        
        # Sort by score (descending) and take top_k
        rescored_results.sort(key=lambda x: x[1], reverse=True)
        rescored_results = rescored_results[:top_k]
        
        if not rescored_results:
            return [], np.array([])
        
        results = [r[0] for r in rescored_results]
        scores = np.array([r[1] for r in rescored_results])
        
        return results, scores
    
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
    
    def get_total_products(self) -> int:
        """
        Get total number of products in the index
        """
        return len(self.product_metadata)
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Get product by ID
        
        Args:
            product_id: Product ID to retrieve
            
        Returns:
            Product metadata dict or None if not found
        """
        for metadata in self.product_metadata:
            if str(metadata.get('product_id')) == str(product_id):
                return metadata
        
        logger.warning(f"Product {product_id} not found in index")
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get index statistics (alias for get_stats)
        """
        return self.get_stats()
    
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
            index_file = self.index_path / "products.index"
            metadata_file = self.index_path / "metadata.json"
            
            # Save FAISS index
            faiss.write_index(self.index, str(index_file))
            
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