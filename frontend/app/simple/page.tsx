'use client';

import { useState } from 'react';
import { Search, Upload, X, Loader2 } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

interface Product {
  product_id: string;
  title: string;
  description: string;
  image_url: string;
  price: number;
  category: string;
  similarity_score: number;
}

interface SearchResponse {
  results: Product[];
  query_time: number;
  total_results: number;
  alpha_used: number;
  search_type: string;
}

export default function HybridSearchPage() {
  const [textQuery, setTextQuery] = useState('');
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [alpha, setAlpha] = useState(0.5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<SearchResponse | null>(null);

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        setError('Image size must be less than 5MB');
        return;
      }
      setImageFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const removeImage = () => {
    setImageFile(null);
    setImagePreview(null);
  };

  const handleSearch = async () => {
    if (!textQuery && !imageFile) {
      setError('Please provide either text or image');
      return;
    }

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      let imageBase64 = null;
      if (imageFile) {
        const reader = new FileReader();
        imageBase64 = await new Promise<string>((resolve, reject) => {
          reader.onload = () => {
            const base64 = (reader.result as string).split(',')[1];
            resolve(base64);
          };
          reader.onerror = reject;
          reader.readAsDataURL(imageFile);
        });
      }

      const res = await fetch(`${API_URL}/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: textQuery || null,
          image: imageBase64,
          alpha: alpha,
          top_k: 10,
        }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Search failed');
      }

      const data: SearchResponse = await res.json();
      setResponse(data);
    } catch (err: any) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const getSearchTypeLabel = (type: string) => {
    switch (type) {
      case 'text':
        return 'Text Search';
      case 'image':
        return 'Image Search';
      case 'hybrid':
        return 'Hybrid Search';
      default:
        return type;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Cross-Modal Fashion Search
          </h1>
          <p className="text-gray-600 text-lg">
            Search with text, images, or both using AI-powered similarity
          </p>
        </div>

        {/* Search Interface */}
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-8">
          {/* Text Input */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Text Query
            </label>
            <div className="relative">
              <input
                type="text"
                value={textQuery}
                onChange={(e) => setTextQuery(e.target.value)}
                placeholder="e.g., red summer dress, leather shoes, blue jeans..."
                className="w-full px-4 py-3 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
              <Search className="absolute right-3 top-3.5 text-gray-400" size={20} />
            </div>
          </div>

          {/* Image Upload */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Image Query
            </label>
            {!imagePreview ? (
              <label className="flex flex-col items-center justify-center w-full h-40 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-blue-500 hover:bg-blue-50 transition">
                <Upload className="text-gray-400 mb-2" size={32} />
                <span className="text-gray-600">Click to upload or drag image here</span>
                <span className="text-gray-400 text-sm mt-1">PNG, JPG, WEBP (max 5MB)</span>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleImageUpload}
                  className="hidden"
                />
              </label>
            ) : (
              <div className="relative inline-block">
                <img
                  src={imagePreview}
                  alt="Preview"
                  className="h-40 rounded-lg border-2 border-gray-200"
                />
                <button
                  onClick={removeImage}
                  className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 hover:bg-red-600 transition"
                >
                  <X size={16} />
                </button>
              </div>
            )}
          </div>

          {/* Alpha Slider */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Alpha (α) - Fusion Weight
            </label>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600 w-24">Text Only</span>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={alpha}
                onChange={(e) => setAlpha(parseFloat(e.target.value))}
                className="flex-1 h-2 rounded-lg appearance-none cursor-pointer slider"
              />
              <span className="text-sm text-gray-600 w-24 text-right">Image Only</span>
            </div>
            <div className="mt-2 text-center">
              <span className="text-lg font-semibold text-blue-600">α = {alpha.toFixed(2)}</span>
              <p className="text-xs text-gray-500 mt-1">
                V<sub>fusion</sub> = {alpha.toFixed(2)} × V<sub>image</sub> + {(1 - alpha).toFixed(2)} × V<sub>text</sub>
              </p>
            </div>
          </div>

          {/* Search Button */}
          <button
            onClick={handleSearch}
            disabled={loading || (!textQuery && !imageFile)}
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-400 disabled:cursor-not-allowed transition flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="animate-spin" size={20} />
                Searching...
              </>
            ) : (
              <>
                <Search size={20} />
                Search Products
              </>
            )}
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-8">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Results */}
        {response && (
          <div className="mb-8">
            {/* Results Header */}
            <div className="bg-white rounded-lg shadow p-4 mb-6">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h2 className="text-2xl font-bold text-gray-800">
                    {response.total_results} Results
                  </h2>
                  <p className="text-gray-600 text-sm mt-1">
                    {getSearchTypeLabel(response.search_type)} • 
                    Query time: {response.query_time.toFixed(3)}s • 
                    α = {response.alpha_used.toFixed(2)}
                  </p>
                </div>
              </div>
            </div>

            {/* Results Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {response.results.map((product) => (
                <div
                  key={product.product_id}
                  className="bg-white rounded-xl shadow-md overflow-hidden hover:shadow-xl transition-shadow duration-300 group"
                >
                  {/* Product Image */}
                  <div className="relative h-64 bg-gray-100 overflow-hidden">
                    <img
                      src={`http://localhost:8000${product.image_url}`}
                      alt={product.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      onError={(e) => {
                        e.currentTarget.src = 'https://via.placeholder.com/300x300?text=No+Image';
                      }}
                    />
                    {/* Similarity Score Badge */}
                    <div className="absolute top-2 right-2 bg-blue-600 text-white px-3 py-1 rounded-full text-sm font-semibold shadow-lg">
                      {(product.similarity_score * 100).toFixed(1)}%
                    </div>
                  </div>

                  {/* Product Info */}
                  <div className="p-4">
                    <h3 className="font-semibold text-gray-800 mb-2 line-clamp-2 min-h-[3rem]">
                      {product.title}
                    </h3>
                    
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-2xl font-bold text-blue-600">
                        ${product.price.toFixed(2)}
                      </span>
                      {product.category && (
                        <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded capitalize">
                          {product.category}
                        </span>
                      )}
                    </div>

                    {product.description && (
                      <p className="text-gray-600 text-sm line-clamp-2 mb-3">
                        {product.description}
                      </p>
                    )}

                    {/* Similarity Bar */}
                    <div className="mb-2">
                      <div className="flex justify-between text-xs text-gray-600 mb-1">
                        <span>Similarity</span>
                        <span>{(product.similarity_score * 100).toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-500"
                          style={{ width: `${product.similarity_score * 100}%` }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {!response && !loading && (
          <div className="text-center py-16 text-gray-400">
            <Search size={64} className="mx-auto mb-4 opacity-50" />
            <p className="text-lg">Enter a search query to find products</p>
            <p className="text-sm mt-2">Try searching by text, uploading an image, or both!</p>
          </div>
        )}
      </div>

      <style jsx>{`
        .slider::-webkit-slider-thumb {
          appearance: none;
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: linear-gradient(135deg, #3b82f6, #a855f7);
          cursor: pointer;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }

        .slider::-moz-range-thumb {
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: linear-gradient(135deg, #3b82f6, #a855f7);
          cursor: pointer;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }

        .slider {
          background: linear-gradient(to right, #10b981 0%, #3b82f6 50%, #a855f7 100%);
        }
      `}</style>
    </div>
  );
}
