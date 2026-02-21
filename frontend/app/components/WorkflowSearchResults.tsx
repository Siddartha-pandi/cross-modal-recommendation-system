'use client';

import React from 'react';
import { 
  Star, 
  Heart, 
  ShoppingCart, 
  Eye,
  ExternalLink,
  Zap,
  Target,
  TrendingUp,
  Image as ImageIcon,
  Type
} from 'lucide-react';

interface WorkflowSearchResultsProps {
  results: SearchResult[];
  isLoading: boolean;
  searchType: 'text' | 'image' | 'combined';
  processingStats?: ProcessingStats;
  onProductClick: (productId: string) => void;
  onAddToCart: (productId: string) => void;
  onToggleFavorite: (productId: string) => void;
}

interface SearchResult {
  id: string;
  name: string;
  description: string;
  price: number;
  originalPrice?: number;
  imageUrl: string;
  category: string;
  rating: number;
  reviewCount: number;
  availability: 'in_stock' | 'low_stock' | 'out_of_stock';
  isFavorite: boolean;
  
  // Cross-modal specific fields
  similarityScore: number;
  textRelevance?: number;
  imageRelevance?: number;
  rerankingScore?: number;
  crossModalFeatures?: {
    dominantColors: string[];
    detectedObjects: string[];
    styleAttributes: string[];
    semanticTags: string[];
  };
}

interface ProcessingStats {
  totalResults: number;
  processingTimeMs: number;
  searchMode: string;
  fusionMethod?: string;
  rerankingApplied: boolean;
  vectorSearchTime: number;
  rerankingTime?: number;
}

const WorkflowSearchResults: React.FC<WorkflowSearchResultsProps> = ({
  results,
  isLoading,
  searchType,
  processingStats,
  onProductClick,
  onAddToCart,
  onToggleFavorite,
}) => {
  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-8">
        <div className="flex flex-col items-center justify-center space-y-4">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <div className="text-center">
            <h3 className="text-lg font-semibold text-gray-800 mb-2">Processing Your Search</h3>
            <p className="text-gray-600">Using AI to find the most relevant products...</p>
            <div className="flex items-center justify-center gap-4 mt-4 text-sm text-gray-500">
              <div className="flex items-center gap-1">
                <Zap className="w-4 h-4 text-blue-500" />
                <span>CLIP Encoding</span>
              </div>
              <div className="flex items-center gap-1">
                <Target className="w-4 h-4 text-green-500" />
                <span>Vector Search</span>
              </div>
              <div className="flex items-center gap-1">
                <TrendingUp className="w-4 h-4 text-purple-500" />
                <span>Reranking</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!results || results.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-8">
        <div className="text-center">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Eye className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-800 mb-2">No Results Found</h3>
          <p className="text-gray-600">
            Try adjusting your search terms or filters, or upload a different image.
          </p>
        </div>
      </div>
    );
  }

  const getAvailabilityColor = (availability: string) => {
    switch (availability) {
      case 'in_stock':
        return 'text-green-600 bg-green-50';
      case 'low_stock':
        return 'text-yellow-600 bg-yellow-50';
      case 'out_of_stock':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getAvailabilityText = (availability: string) => {
    switch (availability) {
      case 'in_stock':
        return 'In Stock';
      case 'low_stock':
        return 'Low Stock';
      case 'out_of_stock':
        return 'Out of Stock';
      default:
        return 'Unknown';
    }
  };

  const getSearchModeIcon = (mode: string) => {
    switch (mode) {
      case 'text':
        return <Type className="w-4 h-4" />;
      case 'image':
        return <ImageIcon className="w-4 h-4" />;
      case 'combined':
        return <Zap className="w-4 h-4" />;
      default:
        return <Eye className="w-4 h-4" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Processing Stats */}
      {processingStats && (
        <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                {getSearchModeIcon(searchType)}
              </div>
              <div>
                <h3 className="font-semibold text-gray-800">Search Results</h3>
                <p className="text-sm text-gray-600">
                  Found {processingStats.totalResults} products in {processingStats.processingTimeMs}ms
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4 text-sm text-gray-500">
              <div className="flex items-center gap-1">
                <Target className="w-4 h-4" />
                <span>Vector: {processingStats.vectorSearchTime}ms</span>
              </div>
              {processingStats.rerankingApplied && processingStats.rerankingTime && (
                <div className="flex items-center gap-1">
                  <TrendingUp className="w-4 h-4" />
                  <span>Rerank: {processingStats.rerankingTime}ms</span>
                </div>
              )}
              {processingStats.fusionMethod && (
                <div className="flex items-center gap-1">
                  <Zap className="w-4 h-4" />
                  <span>{processingStats.fusionMethod}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Results Grid */}
      <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {results.map((product) => (
            <div
              key={product.id}
              className="group relative bg-white border border-gray-200 rounded-lg overflow-hidden hover:shadow-lg transition-all duration-300 hover:border-gray-300"
            >
              {/* Product Image */}
              <div className="relative aspect-square overflow-hidden bg-gray-50">
                <img
                  src={product.imageUrl}
                  alt={product.name}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                />
                
                {/* Overlay Controls */}
                <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all duration-300 flex items-center justify-center">
                  <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-all duration-300">
                    <button
                      onClick={() => onProductClick(product.id)}
                      className="p-2 bg-white rounded-full shadow-lg hover:bg-gray-50 transition-colors"
                      title="View Details"
                    >
                      <Eye className="w-4 h-4 text-gray-700" />
                    </button>
                    <button
                      onClick={() => onToggleFavorite(product.id)}
                      className="p-2 bg-white rounded-full shadow-lg hover:bg-gray-50 transition-colors"
                      title={product.isFavorite ? "Remove from Favorites" : "Add to Favorites"}
                    >
                      <Heart className={`w-4 h-4 ${product.isFavorite ? 'text-red-500 fill-current' : 'text-gray-700'}`} />
                    </button>
                    <button
                      onClick={() => window.open(product.imageUrl, '_blank')}
                      className="p-2 bg-white rounded-full shadow-lg hover:bg-gray-50 transition-colors"
                      title="Open Image"
                    >
                      <ExternalLink className="w-4 h-4 text-gray-700" />
                    </button>
                  </div>
                </div>

                {/* Similarity Score Badge */}
                <div className="absolute top-2 left-2">
                  <div className="px-2 py-1 bg-black bg-opacity-75 text-white text-xs rounded-full">
                    {Math.round(product.similarityScore * 100)}% match
                  </div>
                </div>

                {/* Availability Badge */}
                <div className="absolute top-2 right-2">
                  <div className={`px-2 py-1 text-xs rounded-full ${getAvailabilityColor(product.availability)}`}>
                    {getAvailabilityText(product.availability)}
                  </div>
                </div>

                {/* Discount Badge */}
                {product.originalPrice && product.originalPrice > product.price && (
                  <div className="absolute bottom-2 left-2">
                    <div className="px-2 py-1 bg-red-500 text-white text-xs rounded-full">
                      {Math.round((1 - product.price / product.originalPrice) * 100)}% OFF
                    </div>
                  </div>
                )}
              </div>

              {/* Product Info */}
              <div className="p-4 space-y-3">
                {/* Title and Category */}
                <div>
                  <h3 className="font-medium text-gray-800 text-sm line-clamp-2 mb-1">
                    {product.name}
                  </h3>
                  <p className="text-xs text-gray-500">{product.category}</p>
                </div>

                {/* Rating */}
                <div className="flex items-center gap-1">
                  <div className="flex items-center">
                    {[...Array(5)].map((_, i) => (
                      <Star
                        key={i}
                        className={`w-3 h-3 ${
                          i < Math.floor(product.rating)
                            ? 'text-yellow-400 fill-current'
                            : 'text-gray-300'
                        }`}
                      />
                    ))}
                  </div>
                  <span className="text-xs text-gray-600">
                    {product.rating} ({product.reviewCount})
                  </span>
                </div>

                {/* Cross-modal Relevance Scores */}
                {(product.textRelevance !== undefined || product.imageRelevance !== undefined) && (
                  <div className="flex gap-2 text-xs">
                    {product.textRelevance !== undefined && (
                      <div className="flex items-center gap-1">
                        <Type className="w-3 h-3 text-blue-500" />
                        <span className="text-gray-600">{Math.round(product.textRelevance * 100)}%</span>
                      </div>
                    )}
                    {product.imageRelevance !== undefined && (
                      <div className="flex items-center gap-1">
                        <ImageIcon className="w-3 h-3 text-green-500" />
                        <span className="text-gray-600">{Math.round(product.imageRelevance * 100)}%</span>
                      </div>
                    )}
                    {product.rerankingScore !== undefined && (
                      <div className="flex items-center gap-1">
                        <TrendingUp className="w-3 h-3 text-purple-500" />
                        <span className="text-gray-600">{Math.round(product.rerankingScore * 100)}%</span>
                      </div>
                    )}
                  </div>
                )}

                {/* Cross-modal Features */}
                {product.crossModalFeatures && (
                  <div className="space-y-2">
                    {product.crossModalFeatures.dominantColors && product.crossModalFeatures.dominantColors.length > 0 && (
                      <div className="flex items-center gap-1">
                        <span className="text-xs text-gray-500">Colors:</span>
                        <div className="flex gap-1">
                          {product.crossModalFeatures.dominantColors.slice(0, 3).map((color, i) => (
                            <div
                              key={i}
                              className="w-3 h-3 rounded-full border border-gray-300"
                              style={{ backgroundColor: color }}
                              title={color}
                            />
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {product.crossModalFeatures.semanticTags && product.crossModalFeatures.semanticTags.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {product.crossModalFeatures.semanticTags.slice(0, 3).map((tag, i) => (
                          <span
                            key={i}
                            className="px-1 py-0.5 bg-gray-100 text-gray-600 text-xs rounded"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Price and Action */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-lg font-bold text-gray-800">
                      ${product.price.toFixed(2)}
                    </span>
                    {product.originalPrice && product.originalPrice > product.price && (
                      <span className="text-sm text-gray-500 line-through">
                        ${product.originalPrice.toFixed(2)}
                      </span>
                    )}
                  </div>
                  
                  <button
                    onClick={() => onAddToCart(product.id)}
                    disabled={product.availability === 'out_of_stock'}
                    className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                  >
                    <ShoppingCart className="w-3 h-3" />
                    Add
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default WorkflowSearchResults;
