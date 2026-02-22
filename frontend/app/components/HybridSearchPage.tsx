'use client';

import React, { useState, useRef } from 'react';
import { Search, Upload, X, Sparkles, Info, Sliders, TrendingUp } from 'lucide-react';
import { apiClient, ProductResult } from '../lib/api';
import Link from 'next/link';

export default function HybridSearchPage() {
  const [textQuery, setTextQuery] = useState('');
  const [uploadedImage, setUploadedImage] = useState<File | null>(null);
  const [previewImage, setPreviewImage] = useState<string | null>(null);
  const [fusionWeight, setFusionWeight] = useState(0.5); // Alpha: 0 = only image, 1 = only text
  const [results, setResults] = useState<ProductResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [priceRange, setPriceRange] = useState([0, 10000]);
  const [sortBy, setSortBy] = useState('relevance');
  const [queryTime, setQueryTime] = useState<number>(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const categories = [
    "Women's Clothing", "Men's Clothing", "Kids' Clothing",
    "Shoes & Footwear", "Bags & Handbags", "Jewelry & Watches",
    "Activewear & Sportswear", "Outerwear & Jackets"
  ];

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadedImage(file);
      const reader = new FileReader();
      reader.onload = (e) => setPreviewImage(e.target?.result as string);
      reader.readAsDataURL(file);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      setUploadedImage(file);
      const reader = new FileReader();
      reader.onload = (e) => setPreviewImage(e.target?.result as string);
      reader.readAsDataURL(file);
    }
  };

  const clearImage = () => {
    setUploadedImage(null);
    setPreviewImage(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleSearch = async () => {
    if (!textQuery && !uploadedImage) {
      alert('Please provide text, image, or both for hybrid search');
      return;
    }

    setIsLoading(true);
    try {
      const formData = new FormData();
      
      if (textQuery) formData.append('text', textQuery);
      if (uploadedImage) formData.append('image', uploadedImage);  // Changed from 'image_file' to 'image'
      
      // Add fusion weight
      formData.append('text_weight', fusionWeight.toString());
      formData.append('image_weight', (1 - fusionWeight).toString());
      formData.append('fusion_method', 'weighted_avg');
      formData.append('top_k', '20');
      formData.append('enable_reranking', 'true');
      
      if (selectedCategory) formData.append('category_filter', selectedCategory);
      if (priceRange[0] > 0) formData.append('price_min', priceRange[0].toString());
      if (priceRange[1] < 10000) formData.append('price_max', priceRange[1].toString());

      const response = await apiClient.hybridSearch(formData);
      setResults(response.results);
      setQueryTime(response.query_time);
    } catch (error) {
      console.error('Search error:', error);
      alert('Search failed. Make sure the backend is running on port 8000.');
    } finally {
      setIsLoading(false);
    }
  };

  const determineMatchType = (): 'text' | 'image' | 'hybrid' => {
    if (textQuery && uploadedImage) return 'hybrid';
    if (textQuery) return 'text';
    return 'image';
  };

  const getMatchTypeBadge = () => {
    const type = determineMatchType();
    const badges = {
      text: { color: 'bg-purple-100 text-purple-700', label: '🟣 Text Match' },
      image: { color: 'bg-blue-100 text-blue-700', label: '🔵 Image Match' },
      hybrid: { color: 'bg-green-100 text-green-700', label: '🟢 Hybrid Match' }
    };
    const badge = badges[type];
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${badge.color}`}>
        {badge.label}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-6 h-6 text-indigo-600" />
              <span className="text-lg font-bold">Cross-Modal Fashion Recommendation</span>
            </div>
            <h1 className="text-md font-semibold">Hybrid Search</h1>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {/* Hybrid Search Bar */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6 mb-8">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="w-5 h-5 text-indigo-600" />
            <h2 className="text-xl font-bold">Hybrid Cross-Modal Search</h2>
            <Info className="w-4 h-4 text-gray-400 cursor-help" />
          </div>

          {/* Text Input */}
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">Text Query</label>
            <input
              type="text"
              value={textQuery}
              onChange={(e) => setTextQuery(e.target.value)}
              placeholder="Describe what you're looking for (e.g., red floral party dress)"
              className="w-full px-4 py-3 rounded-xl border-2 border-gray-200 dark:border-gray-700 focus:border-indigo-500 focus:outline-none"
            />
          </div>

          {/* Image Upload */}
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">Image Upload (Optional)</label>
            <div
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              className="border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-xl p-6 text-center cursor-pointer hover:border-indigo-500 transition"
              onClick={() => fileInputRef.current?.click()}
            >
              {previewImage ? (
                <div className="relative inline-block">
                  <img src={previewImage} alt="Preview" className="max-h-40 rounded-lg" />
                  <button
                    onClick={(e) => { e.stopPropagation(); clearImage(); }}
                    className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 hover:bg-red-600"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <div>
                  <Upload className="w-12 h-12 text-gray-400 mx-auto mb-2" />
                  <p className="text-gray-600 dark:text-gray-400">Drag & drop or click to upload</p>
                </div>
              )}
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleImageUpload}
                className="hidden"
              />
            </div>
          </div>

          {/* Fusion Weight Control */}
          <div className="mb-6 p-4 bg-indigo-50 dark:bg-indigo-900/20 rounded-xl">
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium flex items-center gap-2">
                <Sliders className="w-4 h-4" />
                Fusion Weight Control
              </label>
              <span className="text-xs text-gray-600 dark:text-gray-400">
                Image: {((1 - fusionWeight) * 100).toFixed(0)}% | Text: {(fusionWeight * 100).toFixed(0)}%
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={fusionWeight}
              onChange={(e) => setFusionWeight(parseFloat(e.target.value))}
              className="w-full h-2 rounded-lg appearance-none cursor-pointer"
              style={{
                background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${(1 - fusionWeight) * 100}%, #a855f7 ${(1 - fusionWeight) * 100}%, #a855f7 100%)`
              }}
            />
            <div className="flex justify-between text-xs mt-1">
              <span className="text-blue-600 font-medium">Only Image</span>
              <span className="text-indigo-600 font-medium">Balanced</span>
              <span className="text-purple-600 font-medium">Only Text</span>
            </div>
          </div>

          {/* Search Button */}
          <button
            onClick={handleSearch}
            disabled={isLoading || (!textQuery && !uploadedImage)}
            className="w-full px-6 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:shadow-lg transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 text-lg font-semibold"
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                <span>Searching...</span>
              </>
            ) : (
              <>
                <Search className="w-5 h-5" />
                <span>Search Now</span>
              </>
            )}
          </button>
        </div>

        {/* Layout: Filters + Results */}
        <div className="grid md:grid-cols-4 gap-6">
          {/* Filters Sidebar */}
          <div className="md:col-span-1">
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6 sticky top-24">
              <h3 className="font-bold text-lg mb-4">Filters</h3>
              
              {/* Category */}
              <div className="mb-6">
                <label className="block text-sm font-medium mb-2">Category</label>
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">All Categories</option>
                  {categories.map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>

              {/* Price Range */}
              <div className="mb-6">
                <label className="block text-sm font-medium mb-2">
                  Price Range: ₹{priceRange[0]} - ₹{priceRange[1]}
                </label>
                <input
                  type="range"
                  min="0"
                  max="10000"
                  value={priceRange[1]}
                  onChange={(e) => setPriceRange([0, parseInt(e.target.value)])}
                  className="w-full"
                />
              </div>

              {/* Sort By */}
              <div className="mb-6">
                <label className="block text-sm font-medium mb-2">Sort By</label>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="relevance">Relevance</option>
                  <option value="price_low">Price: Low to High</option>
                  <option value="price_high">Price: High to Low</option>
                  <option value="popularity">Popularity</option>
                </select>
              </div>
            </div>
          </div>

          {/* Results Grid */}
          <div className="md:col-span-3">
            {results.length > 0 ? (
              <>
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-lg font-semibold">{results.length} Results Found</h3>
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <TrendingUp className="w-4 h-4" />
                    Ranked by hybrid similarity ({queryTime.toFixed(2)}s)
                  </div>
                </div>
                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
                  {results.map((product) => (
                    <div key={product.product_id} className="bg-white dark:bg-gray-800 rounded-xl shadow hover:shadow-xl transition overflow-hidden group">
                      <div className="aspect-square bg-gray-100 dark:bg-gray-700 overflow-hidden">
                        <img
                          src={product.image_url || '/placeholder.png'}
                          alt={product.title}
                          className="w-full h-full object-cover group-hover:scale-110 transition"
                        />
                      </div>
                      <div className="p-4">
                        <div className="flex items-start justify-between mb-2">
                          <h4 className="font-semibold text-sm line-clamp-2 flex-1">{product.title}</h4>
                          {getMatchTypeBadge()}
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-lg font-bold text-indigo-600">₹{product.price}</span>
                          {product.similarity_score && (
                            <span className="text-xs text-gray-500">
                              {(product.similarity_score * 100).toFixed(1)}% match
                            </span>
                          )}
                        </div>
                        {product.category && (
                          <div className="mt-2">
                            <span className="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
                              {product.category}
                            </span>
                          </div>
                        )}
                        <div className="mt-3 flex gap-2">
                          <Link href={`/product/${product.product_id}`} className="flex-1">
                            <button className="w-full px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition text-sm">
                              View Details
                            </button>
                          </Link>
                          <button className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition">
                            ❤️
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-12 text-center">
                <Search className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-xl font-semibold mb-2">No Results Yet</h3>
                <p className="text-gray-600 dark:text-gray-400">
                  Start searching with text, image, or both to see hybrid recommendations
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
