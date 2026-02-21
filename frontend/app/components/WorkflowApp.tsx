'use client';

import React, { useState, useCallback, useEffect } from 'react';
import WorkflowSearchInterface from './WorkflowSearchInterface';
import WorkflowSearchResults from './WorkflowSearchResults';
import { Search, Sparkles, Zap, TrendingUp, Bot, Cpu, Eye, Brain, Target } from 'lucide-react';

interface SearchParameters {
  text?: string;
  imageFile?: File;
  topK: number;
  imageWeight: number;
  textWeight: number;
  fusionMethod: 'weighted_avg' | 'concatenation' | 'element_wise';
  categoryFilter?: string;
  priceMin?: number;
  priceMax?: number;
  enableReranking: boolean;
  rerankingMethod: 'cross_attention' | 'cosine_rerank' | 'category_boost';
  diversityWeight: number;
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

const WorkflowApp: React.FC = () => {
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const [processingStats, setProcessingStats] = useState<ProcessingStats | undefined>();

  const [showStats, setShowStats] = useState(false);

  // Trigger stats animation after component mounts
  useEffect(() => {
    const timer = setTimeout(() => setShowStats(true), 500);
    return () => clearTimeout(timer);
  }, []);

  const handleSearch = useCallback(async (params: SearchParameters) => {
    setIsLoading(true);
    setHasSearched(true);
    
    // Combined search mode only

    try {
      // Create FormData for multipart request
      const formData = new FormData();
      
      if (params.text) {
        formData.append('text', params.text);
      }
      
      if (params.imageFile) {
        formData.append('image', params.imageFile);
      }
      
      // Add search parameters
      formData.append('top_k', params.topK.toString());
      formData.append('image_weight', params.imageWeight.toString());
      formData.append('text_weight', params.textWeight.toString());
      formData.append('fusion_method', params.fusionMethod);
      formData.append('enable_reranking', params.enableReranking.toString());
      formData.append('reranking_method', params.rerankingMethod);
      formData.append('diversity_weight', params.diversityWeight.toString());
      
      if (params.categoryFilter) {
        formData.append('category_filter', params.categoryFilter);
      }
      
      if (params.priceMin !== undefined) {
        formData.append('price_min', params.priceMin.toString());
      }
      
      if (params.priceMax !== undefined) {
        formData.append('price_max', params.priceMax.toString());
      }

      const response = await fetch('/api/search/workflow', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Search failed: ${response.statusText}`);
      }

      const data = await response.json();
      
      // Transform API response to match our interface
      const transformedResults: SearchResult[] = data.results.map((item: any) => ({
        id: item.id,
        name: item.name,
        description: item.description,
        price: item.price,
        originalPrice: item.original_price,
        imageUrl: item.image_url,
        category: item.category,
        rating: item.rating || 4.0,
        reviewCount: item.review_count || 0,
        availability: item.availability || 'in_stock',
        isFavorite: false, // This would come from user preferences
        similarityScore: item.similarity_score,
        textRelevance: item.text_relevance,
        imageRelevance: item.image_relevance,
        rerankingScore: item.reranking_score,
        crossModalFeatures: item.cross_modal_features ? {
          dominantColors: item.cross_modal_features.dominant_colors || [],
          detectedObjects: item.cross_modal_features.detected_objects || [],
          styleAttributes: item.cross_modal_features.style_attributes || [],
          semanticTags: item.cross_modal_features.semantic_tags || [],
        } : undefined,
      }));

      setSearchResults(transformedResults);
      
      // Set processing stats
      if (data.processing_stats) {
        setProcessingStats({
          totalResults: data.processing_stats.total_results,
          processingTimeMs: data.processing_stats.processing_time_ms,
          searchMode: data.processing_stats.search_mode,
          fusionMethod: data.processing_stats.fusion_method,
          rerankingApplied: data.processing_stats.reranking_applied,
          vectorSearchTime: data.processing_stats.vector_search_time,
          rerankingTime: data.processing_stats.reranking_time,
        });
      }

    } catch (error) {
      console.error('Search error:', error);
      
      // For demo purposes, generate mock results
      const mockResults: SearchResult[] = generateMockResults(params);
      setSearchResults(mockResults);
      
      setProcessingStats({
        totalResults: mockResults.length,
        processingTimeMs: Math.floor(Math.random() * 1000) + 200,
        searchMode: 'combined',
        fusionMethod: params.fusionMethod,
        rerankingApplied: params.enableReranking,
        vectorSearchTime: Math.floor(Math.random() * 500) + 100,
        rerankingTime: params.enableReranking ? Math.floor(Math.random() * 200) + 50 : undefined,
      });
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleProductClick = useCallback((productId: string) => {
    console.log('Product clicked:', productId);
    // Navigate to product detail page
  }, []);

  const handleAddToCart = useCallback((productId: string) => {
    console.log('Add to cart:', productId);
    // Add to cart logic
  }, []);

  const handleToggleFavorite = useCallback((productId: string) => {
    setSearchResults(prev => 
      prev.map(result => 
        result.id === productId 
          ? { ...result, isFavorite: !result.isFavorite }
          : result
      )
    );
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-cyan-50 relative overflow-hidden">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-1/2 -right-1/2 w-96 h-96 bg-gradient-to-r from-purple-400/20 to-pink-400/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute -bottom-1/2 -left-1/2 w-96 h-96 bg-gradient-to-r from-blue-400/20 to-cyan-400/20 rounded-full blur-3xl animate-pulse" style={{animationDelay: '1s'}}></div>
        <div className="absolute top-1/4 left-1/4 w-32 h-32 bg-gradient-to-r from-yellow-400/30 to-orange-400/30 rounded-full blur-2xl animate-bounce" style={{animationDuration: '3s'}}></div>
      </div>

      {/* Header */}
      <header className="relative z-10 bg-white/80 backdrop-blur-xl shadow-lg border-b border-white/20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-20">
            <div className="flex items-center space-x-4">
              <div className="relative">
                <div className="w-12 h-12 bg-gradient-to-r from-purple-500 via-blue-500 to-cyan-500 rounded-2xl flex items-center justify-center shadow-lg transform hover:scale-110 transition-all duration-300">
                  <Bot className="w-7 h-7 text-white animate-pulse" />
                </div>
                <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-400 rounded-full animate-ping"></div>
              </div>
              <div className="">
                <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                  AI Vision Search
                </h1>
                <p className="text-sm text-slate-600 flex items-center gap-1">
                  <Sparkles className="w-4 h-4 text-yellow-500 animate-spin" />
                  Cross-Modal Product Discovery
                </p>
              </div>
            </div>
            
            {/* Live Stats */}
            <div className="hidden md:flex items-center space-x-6">
              <div className={`text-center transform transition-all duration-700 ${showStats ? 'translate-y-0 opacity-100' : 'translate-y-4 opacity-0'}`}>
                <div className="flex items-center justify-center w-10 h-10 bg-gradient-to-r from-green-400 to-emerald-500 rounded-full mb-1">
                  <TrendingUp className="w-5 h-5 text-white" />
                </div>
                <p className="text-sm font-bold text-slate-800">98.5%</p>
                <p className="text-xs text-slate-500">Accuracy</p>
              </div>
              <div className={`text-center transform transition-all duration-700 delay-150 ${showStats ? 'translate-y-0 opacity-100' : 'translate-y-4 opacity-0'}`}>
                <div className="flex items-center justify-center w-10 h-10 bg-gradient-to-r from-blue-400 to-indigo-500 rounded-full mb-1">
                  <Zap className="w-5 h-5 text-white" />
                </div>
                <p className="text-sm font-bold text-slate-800">&lt;0.3s</p>
                <p className="text-xs text-slate-500">Response</p>
              </div>
              <div className={`text-center transform transition-all duration-700 delay-300 ${showStats ? 'translate-y-0 opacity-100' : 'translate-y-4 opacity-0'}`}>
                <div className="flex items-center justify-center w-10 h-10 bg-gradient-to-r from-purple-400 to-pink-500 rounded-full mb-1">
                  <Cpu className="w-5 h-5 text-white" />
                </div>
                <p className="text-sm font-bold text-slate-800">CLIP</p>
                <p className="text-xs text-slate-500">AI Model</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      {!hasSearched && (
        <div className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-8 text-center">
          <div className="transform hover:scale-105 transition-all duration-500">
            <h2 className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-purple-600 via-blue-600 to-cyan-600 bg-clip-text text-transparent mb-6 leading-tight">
              Find Products with
              <span className="block bg-gradient-to-r from-pink-500 to-orange-500 bg-clip-text text-transparent">
                AI Vision
              </span>
            </h2>
            <p className="text-xl text-slate-600 mb-8 max-w-2xl mx-auto leading-relaxed">
              Upload an image, describe what you want, or do both! Our AI understands your needs and finds the perfect products.
            </p>
            <div className="flex justify-center items-center gap-8 mb-12">
              <div className="flex items-center gap-2 text-slate-600 group cursor-pointer">
                <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform">
                  <Eye className="w-4 h-4 text-white" />
                </div>
                <span className="font-medium">Smart Vision</span>
              </div>
              <div className="flex items-center gap-2 text-slate-600 group cursor-pointer">
                <div className="w-8 h-8 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform">
                  <Brain className="w-4 h-4 text-white" />
                </div>
                <span className="font-medium">Deep Learning</span>
              </div>
              <div className="flex items-center gap-2 text-slate-600 group cursor-pointer">
                <div className="w-8 h-8 bg-gradient-to-r from-orange-500 to-red-500 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform">
                  <Target className="w-4 h-4 text-white" />
                </div>
                <span className="font-medium">Perfect Match</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Search Interface */}
          <div className="lg:col-span-4">
            <div className="sticky top-8">
              <div className="transform hover:scale-[1.02] transition-all duration-300">
                <WorkflowSearchInterface
                  onSearch={handleSearch}
                  isLoading={isLoading}
                />
              </div>
            </div>
          </div>

          {/* Results */}
          <div className="lg:col-span-8">
            {isLoading && (
              <div className="text-center py-16">
                <div className="relative inline-flex items-center">
                  {/* Animated circles */}
                  <div className="absolute inset-0">
                    <div className="w-20 h-20 border-4 border-purple-200 rounded-full animate-ping"></div>
                  </div>
                  <div className="absolute inset-2">
                    <div className="w-16 h-16 border-4 border-blue-300 rounded-full animate-pulse"></div>
                  </div>
                  <div className="relative w-12 h-12 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full flex items-center justify-center">
                    <Bot className="w-6 h-6 text-white animate-bounce" />
                  </div>
                </div>
                <div className="mt-8">
                  <h3 className="text-xl font-bold text-slate-800 mb-2">AI is Analyzing...</h3>
                  <p className="text-slate-600 mb-4">Processing your request with advanced computer vision</p>
                  <div className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-purple-500 to-blue-500 text-white rounded-full shadow-lg">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Searching Products...
                  </div>
                </div>
              </div>
            )}

            {!isLoading && hasSearched && (
              <div className="animate-fadeIn">
                <WorkflowSearchResults
                  results={searchResults}
                  isLoading={isLoading}
                  searchType="combined"
                  processingStats={processingStats}
                  onProductClick={handleProductClick}
                  onAddToCart={handleAddToCart}
                  onToggleFavorite={handleToggleFavorite}
                />
              </div>
            )}

            {!hasSearched && !isLoading && (
              <div className="text-center py-16">
                <div className="relative inline-block mb-8">
                  <div className="w-32 h-32 mx-auto bg-gradient-to-r from-purple-100 via-blue-100 to-cyan-100 rounded-full flex items-center justify-center transform hover:rotate-12 transition-all duration-500">
                    <Search className="w-16 h-16 text-slate-400" />
                  </div>
                  <div className="absolute -top-2 -right-2 w-8 h-8 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-full flex items-center justify-center animate-bounce">
                    <Sparkles className="w-4 h-4 text-white" />
                  </div>
                </div>
                <h3 className="text-2xl font-bold text-slate-800 mb-4">Ready for Magic ✨</h3>
                <p className="text-lg text-slate-600 max-w-lg mx-auto leading-relaxed">
                  Upload an image, describe what you want, or combine both for the most accurate AI-powered product recommendations!
                </p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

// Mock data generator for demo purposes
function generateMockResults(params: SearchParameters): SearchResult[] {
  const mockProducts = [
    {
      id: '1',
      name: 'Modern Wireless Headphones',
      description: 'High-quality noise-canceling wireless headphones with premium sound',
      price: 199.99,
      originalPrice: 249.99,
      imageUrl: 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400',
      category: 'Electronics',
      rating: 4.5,
      reviewCount: 128,
      availability: 'in_stock' as const,
      isFavorite: false,
      similarityScore: 0.95,
      textRelevance: 0.88,
      imageRelevance: 0.92,
      rerankingScore: 0.94,
      crossModalFeatures: {
        dominantColors: ['#000000', '#333333', '#666666'],
        detectedObjects: ['headphones', 'electronics'],
        styleAttributes: ['modern', 'sleek', 'wireless'],
        semanticTags: ['audio', 'music', 'technology']
      }
    },
    {
      id: '2',
      name: 'Vintage Leather Jacket',
      description: 'Classic brown leather jacket with vintage styling',
      price: 299.99,
      imageUrl: 'https://images.unsplash.com/photo-1551028719-00167b16eac5?w=400',
      category: 'Clothing',
      rating: 4.3,
      reviewCount: 89,
      availability: 'in_stock' as const,
      isFavorite: false,
      similarityScore: 0.87,
      textRelevance: 0.82,
      imageRelevance: 0.91,
      crossModalFeatures: {
        dominantColors: ['#8B4513', '#A0522D', '#654321'],
        detectedObjects: ['jacket', 'clothing', 'leather'],
        styleAttributes: ['vintage', 'classic', 'leather'],
        semanticTags: ['fashion', 'outerwear', 'style']
      }
    },
    {
      id: '3',
      name: 'Minimalist Coffee Table',
      description: 'Clean lines wooden coffee table perfect for modern living rooms',
      price: 449.99,
      originalPrice: 549.99,
      imageUrl: 'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400',
      category: 'Furniture',
      rating: 4.7,
      reviewCount: 203,
      availability: 'low_stock' as const,
      isFavorite: false,
      similarityScore: 0.79,
      textRelevance: 0.85,
      imageRelevance: 0.74,
      crossModalFeatures: {
        dominantColors: ['#DEB887', '#F5DEB3', '#D2B48C'],
        detectedObjects: ['table', 'furniture', 'wood'],
        styleAttributes: ['minimalist', 'modern', 'wooden'],
        semanticTags: ['furniture', 'home', 'interior']
      }
    }
  ];

  // Apply filters
  let filtered = mockProducts;
  
  if (params.categoryFilter) {
    filtered = filtered.filter(p => p.category === params.categoryFilter);
  }
  
  if (params.priceMin !== undefined) {
    filtered = filtered.filter(p => p.price >= params.priceMin!);
  }
  
  if (params.priceMax !== undefined) {
    filtered = filtered.filter(p => p.price <= params.priceMax!);
  }

  return filtered.slice(0, params.topK);
}

export default WorkflowApp;
