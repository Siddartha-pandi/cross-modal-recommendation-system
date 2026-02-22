'use client';

import React, { useState, useRef, useCallback } from 'react';
import { 
  Search, 
  X, 
  Zap,
  Info,
  Camera
} from 'lucide-react';
import { AI_SEARCH_CONFIG, PRODUCT_CATEGORIES } from '../constants/config';

interface SimpleSearchInterfaceProps {
  onSearch: (params: SearchParameters) => void;
  isLoading: boolean;
}

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

const SimpleSearchInterface: React.FC<SimpleSearchInterfaceProps> = ({
  onSearch,
  isLoading,
}) => {
  // Simple state - only what users can control
  const [textQuery, setTextQuery] = useState('');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [previewImage, setPreviewImage] = useState<string | null>(null);
  const [categoryFilter, setCategoryFilter] = useState('');
  const [priceMax, setPriceMax] = useState<number | ''>('');
  
  // UI State
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const handleFileSelect = useCallback((file: File) => {
    if (file && file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        if (e.target?.result) {
          setPreviewImage(e.target.result as string);
        }
      };
      reader.readAsDataURL(file);
      setUploadedFile(file);
    }
  }, []);
  
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);
  
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  }, [handleFileSelect]);
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!textQuery.trim() || !uploadedFile) {
      return;
    }
    
    // Use fixed AI configuration with user's inputs
    const searchParams: SearchParameters = {
      text: textQuery.trim(),
      imageFile: uploadedFile,
      categoryFilter: categoryFilter || undefined,
      priceMax: typeof priceMax === 'number' ? priceMax : undefined,
      priceMin: undefined, // Not exposed in simple interface
      
      // Fixed AI parameters for consistent experience
      ...AI_SEARCH_CONFIG
    };
    
    onSearch(searchParams);
  };
  
  const clearImage = () => {
    setUploadedFile(null);
    setPreviewImage(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };
  
  const clearAll = () => {
    setTextQuery('');
    clearImage();
    setCategoryFilter('');
    setPriceMax('');
  };
  
  return (
    <div className="bg-white/95 backdrop-blur-xl rounded-2xl shadow-xl border border-white/30 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 via-blue-600 to-cyan-600 text-white p-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
            <Camera className="w-6 h-6 animate-pulse" />
          </div>
          <h2 className="text-xl font-bold">AI Product Search</h2>
        </div>
        <p className="text-white/90 text-sm">
          Find products using both images and descriptions
        </p>
      </div>
      
      <form onSubmit={handleSubmit} className="p-6">
        {/* Search Info */}
        <div className="mb-6">
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-xl p-4">
            <div className="flex items-center gap-2 text-blue-700 mb-2">
              <Zap className="w-5 h-5" />
              <span className="font-semibold">Smart Search</span>
            </div>
            <p className="text-blue-600 text-sm">
              Upload an image and describe what you're looking for to get AI-powered recommendations.
            </p>
          </div>
        </div>

        {/* Enhanced Text Input */}
        <div className="mb-6">
          <label className="block text-sm font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent mb-3">
            🔍 What are you looking for? <span className="text-red-500 animate-pulse">*</span>
          </label>
          <div className="relative group">
            <div className="absolute inset-0 bg-gradient-to-r from-purple-500/20 via-blue-500/20 to-cyan-500/20 rounded-xl blur opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
            <div className="relative">
              <input
                type="text"
                value={textQuery}
                onChange={(e) => setTextQuery(e.target.value)}
                placeholder="Describe the product you want to find... (e.g., 'blue cotton t-shirt')"
                className="w-full pl-12 pr-12 py-4 border-2 border-gray-200 hover:border-purple-300 focus:border-purple-500 rounded-xl bg-white/90 backdrop-blur-sm focus:ring-4 focus:ring-purple-500/20 transition-all duration-300 text-gray-800 placeholder-gray-500 font-medium"
                disabled={isLoading}
                required
              />
              <Search className="absolute left-4 top-4 w-5 h-5 text-purple-500 group-hover:text-blue-500 transition-colors duration-300" />
              <div className="absolute right-4 top-4 flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-xs text-gray-500">AI Ready</span>
              </div>
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-2 ml-1">💡 Be specific about colors, styles, and materials for better results</p>
        </div>

        {/* Enhanced Image Upload */}
        <div className="mb-6">
          <label className="block text-sm font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent mb-3">
            📸 Upload Image <span className="text-red-500 animate-pulse">*</span>
          </label>
          
          {previewImage ? (
            <div className="relative inline-block group">
              <div className="absolute inset-0 bg-gradient-to-br from-green-200 to-emerald-200 rounded-xl blur opacity-30 group-hover:opacity-50 transition-opacity duration-300"></div>
              <img
                src={previewImage}
                alt="Upload preview"
                className="relative w-48 h-48 object-cover rounded-xl border-4 border-white shadow-xl animate-fadeIn"
              />
              <button
                type="button"
                onClick={clearImage}
                className="absolute -top-3 -right-3 w-8 h-8 bg-gradient-to-r from-red-500 to-red-600 text-white rounded-full flex items-center justify-center hover:scale-110 transition-all duration-200 shadow-lg hover:shadow-xl"
              >
                <X className="w-4 h-4" />
              </button>
              <div className="absolute bottom-2 left-2 bg-green-500 text-white px-2 py-1 rounded-full text-xs font-semibold flex items-center space-x-1">
                <div className="w-1.5 h-1.5 bg-white rounded-full animate-pulse"></div>
                <span>Ready</span>
              </div>
            </div>
          ) : (
            <div
              className={`relative border-2 border-dashed rounded-xl p-10 text-center transition-all duration-300 cursor-pointer overflow-hidden group ${
                dragActive
                  ? 'border-blue-500 bg-gradient-to-br from-blue-50 to-cyan-50 shadow-lg scale-105'
                  : 'border-gray-300 hover:border-blue-400 hover:bg-gradient-to-br hover:from-blue-50/50 hover:to-purple-50/50 hover:shadow-md'
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              {/* Animated background elements */}
              <div className="absolute inset-0 opacity-10">
                <div className="absolute top-4 left-4 w-6 h-6 bg-blue-400 rounded-full animate-float"></div>
                <div className="absolute bottom-6 right-6 w-4 h-4 bg-purple-400 rounded-full animate-float delay-1000"></div>
                <div className="absolute top-1/2 right-1/4 w-3 h-3 bg-cyan-400 rounded-full animate-float delay-2000"></div>
              </div>
              
              <div className="relative z-10">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full mb-4 group-hover:scale-110 transition-transform duration-300 shadow-lg">
                  <Camera className="w-8 h-8 text-white animate-bounce-slow" />
                </div>
                <div className="space-y-3">
                  <p className="text-lg font-semibold text-gray-700 group-hover:text-blue-600 transition-colors">
                    Drop your image here
                  </p>
                  <p className="text-sm text-gray-600">
                    <span className="font-medium bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">Click to upload</span> or drag and drop
                  </p>
                  <div className="flex items-center justify-center space-x-3 text-xs">
                    <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full font-medium">PNG</span>
                    <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-full font-medium">JPG</span>
                    <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded-full font-medium">GIF</span>
                    <span className="text-gray-400">up to 10MB</span>
                  </div>
                </div>
              </div>
              <p className="text-gray-600 mb-2 font-medium">
                Drag and drop an image, or click to browse
              </p>
              <p className="text-sm text-gray-500">
                Supports JPG, PNG, GIF up to 10MB
              </p>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
                className="hidden"
              />
            </div>
          )}
        </div>
        
        {/* Simple Filters */}
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">Filters (Optional)</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Category
              </label>
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              >
                <option value="">All Categories</option>
                {PRODUCT_CATEGORIES.map(category => (
                  <option key={category} value={category}>{category}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Max Price ($)
              </label>
              <input
                type="number"
                min="0"
                step="0.01"
                value={priceMax}
                onChange={(e) => setPriceMax(e.target.value === '' ? '' : parseFloat(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="Any price"
              />
            </div>
          </div>
        </div>
        
        {/* Enhanced Action Buttons */}
        <div className="flex gap-3">
          <button
            type="submit"
            disabled={isLoading || !textQuery.trim() || !uploadedFile}
            className="relative flex-1 bg-gradient-to-r from-purple-600 via-blue-600 to-cyan-600 text-white py-4 px-6 rounded-xl font-bold text-lg hover:from-purple-700 hover:via-blue-700 hover:to-cyan-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-xl overflow-hidden group"
          >
            {/* Animated background for enabled state */}
            {!isLoading && textQuery.trim() && uploadedFile && (
              <div className="absolute inset-0 bg-gradient-to-r from-purple-600 via-blue-600 to-cyan-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            )}
            
            {/* Shimmer effect */}
            {!isLoading && textQuery.trim() && uploadedFile && (
              <div className="absolute inset-0 -skew-x-12 bg-gradient-to-r from-transparent via-white/20 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"></div>
            )}
            
            <div className="relative z-10 flex items-center justify-center gap-3">
              {isLoading ? (
                <>
                  <div className="relative">
                    <div className="w-6 h-6 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                    <div className="absolute inset-0 w-6 h-6 border border-white/50 rounded-full animate-ping"></div>
                  </div>
                  <span className="animate-pulse">🔮 AI is analyzing...</span>
                </>
              ) : (
                <>
                  <div className="flex items-center space-x-2">
                    <Zap className="w-5 h-5 group-hover:animate-bounce" />
                    <span className="text-sm">⚡</span>
                  </div>
                  <span>Search with CLIP AI</span>
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                    <span className="text-sm">🚀</span>
                  </div>
                </>
              )}
            </div>
          </button>
          
          <button
            type="button"
            onClick={clearAll}
            className="px-6 py-3 border border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 transition-colors"
            disabled={isLoading}
          >
            Clear
          </button>
        </div>
        
        {/* AI Info */}
        <div className="mt-6 p-4 bg-blue-50 rounded-xl border border-blue-200">
          <div className="flex items-start gap-2">
            <Info className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
            <div className="text-sm">
              <p className="text-blue-800 font-medium mb-1">
                Powered by Advanced AI:
              </p>
              <p className="text-blue-700">
                Our system uses CLIP neural networks to understand both images and text, 
                finding the most relevant products with high accuracy.
              </p>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
};

export default SimpleSearchInterface;
