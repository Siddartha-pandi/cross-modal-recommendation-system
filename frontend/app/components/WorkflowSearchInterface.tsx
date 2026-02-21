'use client';

import React, { useState, useRef, useCallback } from 'react';
import { 
  Search, 
  Upload, 
  X, 
  Sparkles, 
  Settings, 
  Zap,
  Target,
  Info
} from 'lucide-react';

interface WorkflowSearchInterfaceProps {
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

const WorkflowSearchInterface: React.FC<WorkflowSearchInterfaceProps> = ({
  onSearch,
  isLoading,
}) => {
  // Search State - Combined mode only
  const [textQuery, setTextQuery] = useState('');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [previewImage, setPreviewImage] = useState<string | null>(null);
  
  // Advanced Parameters State
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [topK, setTopK] = useState(12);
  const [imageWeight, setImageWeight] = useState(0.7);
  const [textWeight, setTextWeight] = useState(0.3);
  const [fusionMethod, setFusionMethod] = useState<'weighted_avg' | 'concatenation' | 'element_wise'>('weighted_avg');
  
  // Filtering State
  const [categoryFilter, setCategoryFilter] = useState('');
  const [priceMin, setPriceMin] = useState<number | ''>('');
  const [priceMax, setPriceMax] = useState<number | ''>('');
  
  // Reranking State
  const [enableReranking, setEnableReranking] = useState(true);
  const [rerankingMethod, setRerankingMethod] = useState<'cross_attention' | 'cosine_rerank' | 'category_boost'>('cross_attention');
  const [diversityWeight, setDiversityWeight] = useState(0.1);
  
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
    
    const searchParams: SearchParameters = {
      text: textQuery.trim(),
      imageFile: uploadedFile,
      topK,
      imageWeight,
      textWeight,
      fusionMethod,
      categoryFilter: categoryFilter || undefined,
      priceMin: typeof priceMin === 'number' ? priceMin : undefined,
      priceMax: typeof priceMax === 'number' ? priceMax : undefined,
      enableReranking,
      rerankingMethod,
      diversityWeight
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
  };
  
  return (
    <div className="bg-white/90 backdrop-blur-xl rounded-2xl shadow-xl border border-white/20 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 via-blue-600 to-cyan-600 text-white p-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
            <Sparkles className="w-6 h-6 animate-pulse" />
          </div>
          <h2 className="text-2xl font-bold">AI Vision Search</h2>
        </div>
        <p className="text-white/90">
          Combined AI-powered search using both images and text descriptions
        </p>
      </div>
      
      <form onSubmit={handleSubmit} className="p-6">
        {/* Search Info */}
        <div className="mb-6">
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-xl p-4">
            <div className="flex items-center gap-2 text-blue-700 mb-2">
              <Zap className="w-5 h-5" />
              <span className="font-semibold">Cross-Modal Search Required</span>
            </div>
            <p className="text-blue-600 text-sm">
              Both an image and text description are required for the most accurate AI-powered product recommendations.
            </p>
          </div>
        </div>

        {/* Text Input */}
        <div className="mb-6">
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            Text Description <span className="text-red-500">*</span>
          </label>
          <div className="relative">
            <input
              type="text"
              value={textQuery}
              onChange={(e) => setTextQuery(e.target.value)}
              placeholder="Describe what you're looking for..."
              className="w-full px-4 py-3 pr-10 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
              disabled={isLoading}
              required
            />
            <Search className="absolute right-3 top-3.5 w-5 h-5 text-gray-400" />
          </div>
        </div>

        {/* Image Upload */}
        <div className="mb-6">
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            Image Upload <span className="text-red-500">*</span>
          </label>
          
          {previewImage ? (
            <div className="relative inline-block">
              <img
                src={previewImage}
                alt="Upload preview"
                className="w-48 h-48 object-cover rounded-xl border-2 border-gray-200 shadow-lg"
              />
              <button
                type="button"
                onClick={clearImage}
                className="absolute -top-2 -right-2 w-7 h-7 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 transition-colors shadow-lg"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div
              className={`border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer ${
                dragActive
                  ? 'border-purple-400 bg-purple-50 scale-105'
                  : 'border-gray-300 hover:border-purple-400 hover:bg-gray-50'
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
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
        
        {/* Advanced Settings */}
        <div className="mb-6">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center gap-2 text-purple-600 hover:text-purple-700 font-medium transition-colors"
          >
            <Settings className="w-4 h-4" />
            Advanced Settings
            <span className={`transform transition-transform ${showAdvanced ? 'rotate-180' : ''}`}>
              ▼
            </span>
          </button>
          
          {showAdvanced && (
            <div className="mt-4 p-4 bg-gray-50 rounded-xl border border-gray-200">
              {/* Results Count */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Number of Results: {topK}
                </label>
                <input
                  type="range"
                  min="1"
                  max="50"
                  value={topK}
                  onChange={(e) => setTopK(parseInt(e.target.value))}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                />
              </div>
              
              {/* Embedding Fusion */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Image Weight: {imageWeight.toFixed(2)}
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={imageWeight}
                    onChange={(e) => {
                      const val = parseFloat(e.target.value);
                      setImageWeight(val);
                      setTextWeight(1 - val);
                    }}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Text Weight: {textWeight.toFixed(2)}
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={textWeight}
                    onChange={(e) => {
                      const val = parseFloat(e.target.value);
                      setTextWeight(val);
                      setImageWeight(1 - val);
                    }}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  />
                </div>
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Fusion Method
                </label>
                <select
                  value={fusionMethod}
                  onChange={(e) => setFusionMethod(e.target.value as any)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  <option value="weighted_avg">Weighted Average</option>
                  <option value="concatenation">Concatenation</option>
                  <option value="element_wise">Element-wise Multiplication</option>
                </select>
              </div>
              
              {/* Filters */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Category Filter
                  </label>
                  <select
                    value={categoryFilter}
                    onChange={(e) => setCategoryFilter(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  >
                    <option value="">All Categories</option>
                    <option value="Electronics">Electronics</option>
                    <option value="Clothing">Clothing</option>
                    <option value="Home">Home & Garden</option>
                    <option value="Sports">Sports & Outdoors</option>
                    <option value="Books">Books</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Min Price ($)
                  </label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={priceMin}
                    onChange={(e) => setPriceMin(e.target.value === '' ? '' : parseFloat(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    placeholder="0.00"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Max Price ($)
                  </label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={priceMax}
                    onChange={(e) => setPriceMax(e.target.value === '' ? '' : parseFloat(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    placeholder="999.99"
                  />
                </div>
              </div>
              
              {/* Reranking Options */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <input
                      type="checkbox"
                      id="enableReranking"
                      checked={enableReranking}
                      onChange={(e) => setEnableReranking(e.target.checked)}
                      className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                    />
                    <label htmlFor="enableReranking" className="text-sm font-medium text-gray-700">
                      Enable Neural Reranking
                    </label>
                  </div>
                  {enableReranking && (
                    <select
                      value={rerankingMethod}
                      onChange={(e) => setRerankingMethod(e.target.value as any)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    >
                      <option value="cross_attention">Cross-Attention</option>
                      <option value="cosine_rerank">Cosine Rerank</option>
                      <option value="category_boost">Category Boost</option>
                    </select>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Diversity Weight: {diversityWeight.toFixed(2)}
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={diversityWeight}
                    onChange={(e) => setDiversityWeight(parseFloat(e.target.value))}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  />
                </div>
              </div>
            </div>
          )}
        </div>
        
        {/* Action Buttons */}
        <div className="flex gap-3">
          <button
            type="submit"
            disabled={isLoading || !textQuery.trim() || !uploadedFile}
            className="flex-1 bg-gradient-to-r from-purple-600 to-blue-600 text-white py-3 px-6 rounded-xl font-semibold hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-105 shadow-lg"
          >
            {isLoading ? (
              <div className="flex items-center justify-center gap-2">
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                Searching...
              </div>
            ) : (
              <div className="flex items-center justify-center gap-2">
                <Target className="w-5 h-5" />
                Search Products
              </div>
            )}
          </button>
          
          <button
            type="button"
            onClick={clearAll}
            className="px-6 py-3 border border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 transition-colors"
            disabled={isLoading}
          >
            Clear All
          </button>
        </div>
        
        {/* Help Text */}
        <div className="mt-6 p-4 bg-blue-50 rounded-xl border border-blue-200">
          <div className="flex items-start gap-2">
            <Info className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
            <div className="text-sm">
              <p className="text-blue-800 font-medium mb-1">
                How Cross-Modal Search Works:
              </p>
              <p className="text-blue-700">
                Our AI analyzes both your image and text description to understand what you're looking for, 
                then finds the most similar products using advanced neural networks and vector similarity search.
              </p>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
};

export default WorkflowSearchInterface;
