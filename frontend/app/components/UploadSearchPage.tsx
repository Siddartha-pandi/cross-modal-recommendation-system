'use client';

import React, { useState, useRef } from 'react';
import { Upload, X, Sparkles, CheckCircle, Loader, Tag, Eye } from 'lucide-react';
import { apiClient, ProductResult } from '../lib/api';
import Link from 'next/link';

interface ExtractedTag {
  tag: string;
  confidence: number;
}

export default function UploadSearchPage() {
  const [, setUploadedImage] = useState<File | null>(null);
  const [previewImage, setPreviewImage] = useState<string | null>(null);
  const [, setIsProcessing] = useState(false);
  const [embeddingStatus, setEmbeddingStatus] = useState<'idle' | 'processing' | 'complete'>('idle');
  const [extractedTags, setExtractedTags] = useState<ExtractedTag[]>([]);
  const [searchResults, setSearchResults] = useState<ProductResult[]>([]);
  const [queryTime, setQueryTime] = useState<number>(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImageUpload = (file: File) => {
    setUploadedImage(file);
    const reader = new FileReader();
    reader.onload = (e) => {
      setPreviewImage(e.target?.result as string);
      processImage(file);
    };
    reader.readAsDataURL(file);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleImageUpload(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      handleImageUpload(file);
    }
  };

  const processImage = async (file: File) => {
    setIsProcessing(true);
    setEmbeddingStatus('processing');
    
    try {
      // Call the real API
      const response = await apiClient.uploadAndSearch(file, {
        top_k: 20,
        enable_reranking: true
      });
      
      setEmbeddingStatus('complete');
      setSearchResults(response.results);
      setQueryTime(response.query_time);
      
      // Mock extracted tags (backend doesn't return this yet)
      if (response.results.length > 0) {
        const topCategories = response.results
          .slice(0, 5)
          .map((r, i) => ({ 
            tag: r.category || 'Fashion Item', 
            confidence: 0.95 - (i * 0.05) 
          }));
        setExtractedTags(topCategories);
      }
      
    } catch (error) {
      console.error('Processing error:', error);
      alert('Failed to process image. Make sure the backend is running on port 8000.');
      setEmbeddingStatus('idle');
    } finally {
      setIsProcessing(false);
    }
  };

  const clearImage = () => {
    setUploadedImage(null);
    setPreviewImage(null);
    setEmbeddingStatus('idle');
    setExtractedTags([]);
    setSearchResults([]);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-2">
            <Upload className="w-6 h-6 text-indigo-600" />
            <h1 className="text-lg font-bold">Cross-Modal Fashion Recommendation - Visual Search</h1>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          {/* Upload Section */}
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-8 mb-8">
            <div className="text-center mb-6">
              <Sparkles className="w-12 h-12 text-indigo-600 mx-auto mb-3" />
              <h2 className="text-2xl font-bold mb-2">Upload Image to Find Similar Fashion</h2>
              <p className="text-gray-600 dark:text-gray-400">
                Our CLIP model will analyze your image and find visually similar products
              </p>
            </div>

            {!previewImage ? (
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className="border-3 border-dashed border-indigo-300 dark:border-indigo-700 rounded-2xl p-12 text-center cursor-pointer hover:border-indigo-500 hover:bg-indigo-50 dark:hover:bg-indigo-900/10 transition"
              >
                <Upload className="w-16 h-16 text-indigo-400 mx-auto mb-4" />
                <p className="text-lg font-semibold mb-2">Drop your image here or click to browse</p>
                <p className="text-sm text-gray-500">Supports JPG, PNG, WEBP (Max 10MB)</p>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleFileChange}
                  className="hidden"
                />
              </div>
            ) : (
              <div className="space-y-6">
                {/* Preview */}
                <div className="relative">
                  <img
                    src={previewImage}
                    alt="Uploaded"
                    className="max-h-96 mx-auto rounded-xl shadow-lg"
                  />
                  <button
                    onClick={clearImage}
                    className="absolute top-4 right-4 bg-red-500 text-white p-2 rounded-full hover:bg-red-600 shadow-lg transition"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                {/* Processing Status */}
                <div className="bg-indigo-50 dark:bg-indigo-900/20 rounded-xl p-6">
                  <div className="flex items-center justify-between mb-4">
                    <span className="font-semibold">Visual Embedding Status</span>
                    {embeddingStatus === 'processing' && (
                      <Loader className="w-5 h-5 text-indigo-600 animate-spin" />
                    )}
                    {embeddingStatus === 'complete' && (
                      <CheckCircle className="w-5 h-5 text-green-600" />
                    )}
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span>CLIP Image Encoding</span>
                      <span className={embeddingStatus === 'complete' ? 'text-green-600' : 'text-gray-500'}>
                        {embeddingStatus === 'complete' ? '✓ Complete' : 'Processing...'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span>Feature Extraction</span>
                      <span className={embeddingStatus === 'complete' ? 'text-green-600' : 'text-gray-500'}>
                        {embeddingStatus === 'complete' ? '✓ Complete' : 'Processing...'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span>Similarity Search (FAISS)</span>
                      <span className={embeddingStatus === 'complete' ? 'text-green-600' : 'text-gray-500'}>
                        {embeddingStatus === 'complete' ? '✓ Complete' : 'Waiting...'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Extracted Tags */}
                {extractedTags.length > 0 && (
                  <div className="bg-purple-50 dark:bg-purple-900/20 rounded-xl p-6">
                    <div className="flex items-center gap-2 mb-4">
                      <Tag className="w-5 h-5 text-purple-600" />
                      <span className="font-semibold">AI-Extracted Tags</span>
                    </div>
                    <div className="flex flex-wrap gap-3">
                      {extractedTags.map((tag, idx) => (
                        <div
                          key={idx}
                          className="px-4 py-2 bg-white dark:bg-gray-800 rounded-lg shadow-sm"
                        >
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{tag.tag}</span>
                            <span className="text-xs text-gray-500">
                              {(tag.confidence * 100).toFixed(0)}%
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Search Results */}
          {searchResults.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-8">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-2xl font-bold">Similar Products Found</h3>
                <span className="text-sm text-gray-600">
                  {searchResults.length} results ({queryTime.toFixed(2)}s)
                </span>
              </div>
              
              <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-6">
                {searchResults.map((product) => (
                  <div key={product.product_id} className="group cursor-pointer">
                    <div className="aspect-square bg-gray-100 dark:bg-gray-700 rounded-xl overflow-hidden mb-3 relative">
                      <img
                        src={product.image_url || '/placeholder.png'}
                        alt={product.title}
                        className="w-full h-full object-cover group-hover:scale-110 transition"
                      />
                      <div className="absolute top-3 right-3 bg-green-500 text-white px-3 py-1 rounded-full text-xs font-semibold">
                        {(product.similarity_score * 100).toFixed(0)}% Match
                      </div>
                    </div>
                    <h4 className="font-semibold line-clamp-2 mb-2">{product.title}</h4>
                    {product.category && (
                      <p className="text-sm text-gray-600 mb-2">{product.category}</p>
                    )}
                    <div className="flex items-center justify-between">
                      <span className="text-xl font-bold text-indigo-600">₹{product.price}</span>
                      <Link href={`/product/${product.product_id}`}>
                        <button className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition text-sm flex items-center gap-1">
                          <Eye className="w-4 h-4" />
                          View
                        </button>
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
