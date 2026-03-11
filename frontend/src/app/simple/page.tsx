'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { useCart } from '@/contexts/CartContext';
import UserMenu from '@/components/UserMenu';
import { useRouter } from 'next/navigation';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api/v1';

interface Product {
  product_id: string;
  title: string;
  description: string;
  image_url: string;
  price: number;
  category: string;
  similarity_score: number;
  visual_score?: number;
  text_score?: number;
  final_score?: number;
  matched_attributes?: string[];
}

interface SearchResponse {
  results: Product[];
  query_time: number;
  total_results: number;
  alpha_used: number;
  search_type: string;
  query_analysis?: {
    detected_category?: string;
    detected_colors?: string[];
    detected_patterns?: string[];
    intent?: string;
  };
}

export default function HybridSearchPage() {
  const { user, isAuthenticated, isLoading } = useAuth();
  const { addToCart, itemCount } = useCart();
  const router = useRouter();
  const [textQuery, setTextQuery] = useState('');
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const alpha = 0.6;
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [cartLoading, setCartLoading] = useState<string | null>(null);
  const [addedItems, setAddedItems] = useState<Set<string>>(new Set());
  const [hoveredImage, setHoveredImage] = useState<string | null>(null);

  // Handle authentication redirect in useEffect
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isLoading, isAuthenticated, router]);

  // Show loading screen while auth is being checked
  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-white mb-4">Loading...</h1>
        </div>
      </div>
    );
  }

  // Show loading screen while redirecting
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-white mb-4">Redirecting...</h1>
          <p className="text-gray-400">Please log in to access this page</p>
        </div>
      </div>
    );
  }

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setImageFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSearch = async () => {
    if (!textQuery && !imageFile) {
      setError('Please provide text or image');
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

      console.log('Sending search request to:', `${API_URL}/search`);
      console.log('Payload:', {
        text: textQuery || null,
        image: imageBase64 ? `${imageBase64.substring(0, 50)}...` : null,
        alpha,
        top_k: 3,
      });

      const res = await fetch(`${API_URL}/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: textQuery || null,
          image: imageBase64,
          alpha,
          top_k: 3,
        }),
      });

      console.log('Response status:', res.status);

      if (!res.ok) {
        const errorText = await res.text();
        console.error('Error response:', errorText);
        throw new Error(`Search failed: ${res.status} ${res.statusText}. ${errorText}`);
      }

      const data = await res.json();
      console.log('Search successful, got results:', data.total_results);
      setResponse(data);
    } catch (err: any) {
      console.error('Search error:', err);
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = async (product: Product) => {
    try {
      setCartLoading(product.product_id);
      setError(null); // Clear previous errors
      await addToCart({
        product_id: String(product.product_id),
        title: product.title,
        price: product.price,
        quantity: 1,
        image_url: product.image_url,
      });
      setAddedItems(new Set([...addedItems, product.product_id]));
      setTimeout(() => {
        setAddedItems((prev) => {
          const newSet = new Set(prev);
          newSet.delete(product.product_id);
          return newSet;
        });
      }, 2000);
    } catch (err: any) {
      console.error('handleAddToCart error:', err);
      const errorMsg = err.message || 'Failed to add to cart';
      setError(`Failed to add "${product.title}" to cart: ${errorMsg}`);
    } finally {
      setCartLoading(null);
    }
  };

  const handleBuyNow = async (product: Product) => {
    try {
      setCartLoading(product.product_id);
      await addToCart({
        product_id: String(product.product_id),
        title: product.title,
        price: product.price,
        quantity: 1,
        image_url: product.image_url,
      });
      router.push('/cart');
    } catch (err: any) {
      setError(err.message || 'Failed to process purchase');
      setCartLoading(null);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-neutral-900">
      {/* Navigation */}
      <nav className="bg-slate-900/80 backdrop-blur-md border-b border-slate-800 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 max-w-7xl flex justify-between items-center">
          <Link href="/" className="text-2xl font-bold text-white hover:text-blue-400">
            Fashion Finder
          </Link>
          <div className="flex items-center gap-4">
            {/* <Link
              href="/recommend"
              className="text-sm font-semibold text-violet-400 border border-violet-500/40 px-3 py-1 rounded-full bg-violet-500/10 hover:bg-violet-500/20 transition"
            >
              ✨ Live Recommend
            </Link> */}
            <Link
              href="/cart"
              className="relative text-white hover:text-blue-400 transition flex items-center gap-2"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              {itemCount > 0 && (
                <span className="absolute -top-2 -right-2 bg-red-600 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                  {itemCount}
                </span>
              )}
            </Link>
            <UserMenu />
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-5xl font-bold text-white mb-4">Fashion Discovery</h1>
          <p className="text-gray-400 text-lg">
            Search with text, images, or both
          </p>
          {user && (
            <p className="text-gray-300 mt-4">Welcome, {user.full_name}!</p>
          )}
        </div>

        {/* Search Form */}
        <div className="bg-slate-800/50 backdrop-blur-md rounded-2xl border border-slate-700 p-8 mb-8">
          <div className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {/* Text Input */}
              <div className="space-y-3">
                <label className="block text-[10px] font-bold tracking-widest text-slate-400 uppercase">
                  Text Query
                </label>
                <input
                  type="text"
                  value={textQuery}
                  onChange={(e) => setTextQuery(e.target.value)}
                  placeholder="Describe what you're looking for..."
                  className="w-full px-4 py-4 bg-slate-900 border border-slate-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 h-[58px]"
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                />
              </div>

              {/* Image Upload */}
              <div className="space-y-3">
                <label className="block text-[10px] font-bold tracking-widest text-slate-400 uppercase">
                  Image Query
                </label>
                <div
                  className={`relative group min-h-[160px] transition-all duration-200 ${!imagePreview ? 'cursor-pointer' : ''}`}
                  onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); }}
                  onDrop={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    const file = e.dataTransfer.files?.[0];
                    if (file) handleImageUpload({ target: { files: [file] } } as any);
                  }}
                >
                  <input
                    id="image-upload"
                    type="file"
                    accept="image/*"
                    onChange={handleImageUpload}
                    className="hidden"
                  />

                  {!imagePreview ? (
                    <label
                      htmlFor="image-upload"
                      className="flex flex-col items-center justify-center gap-4 w-full h-[160px] bg-slate-900/50 border-2 border-dashed border-slate-700 rounded-xl hover:border-slate-500 hover:bg-slate-800/80 transition-all cursor-pointer group-hover:bg-slate-800/80"
                    >
                      <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center text-slate-500 group-hover:text-blue-400 group-hover:bg-slate-700 transition-all">
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                      </div>
                      <span className="text-sm text-slate-400 font-medium text-center px-4">Click to upload or drag & drop</span>
                    </label>
                  ) : (
                    <div className="relative w-full h-[160px] bg-slate-900 rounded-xl overflow-hidden border-2 border-slate-700 flex flex-col p-4">
                      <div className="flex items-center gap-4 mb-3">
                        <div className="w-12 h-12 flex-shrink-0 bg-slate-800 rounded-lg overflow-hidden border border-slate-700">
                          <img src={imagePreview} alt="Preview" className="w-full h-full object-cover" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <span className="block text-sm text-slate-200 font-semibold truncate">
                            {imageFile?.name || 'Selected image'}
                          </span>
                          <span className="text-xs text-slate-500 uppercase font-bold tracking-tight">Image Selected</span>
                        </div>
                        <button
                          onClick={(e) => { e.preventDefault(); e.stopPropagation(); setImageFile(null); setImagePreview(null); }}
                          className="bg-red-500/10 hover:bg-red-500/20 text-red-400 p-2 rounded-lg transition-colors flex items-center justify-center"
                          title="Remove image"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                      <div className="flex-1 rounded-lg overflow-hidden bg-black/20 border border-white/5 flex items-center justify-center">
                        <img src={imagePreview} alt="Full Preview" className="h-full object-contain" />
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>



            {/* Search Button */}
            <button
              onClick={handleSearch}
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-semibold py-3 px-6 rounded-lg transition"
            >
              {loading ? 'Searching...' : 'Search'}
            </button>

            {/* Error Message */}
            {error && (
              <div className="bg-red-500/20 border border-red-500 text-red-300 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}
          </div>
        </div>

        {/* Results */}
        {response && (() => {
          const SIMILARITY_THRESHOLD = 0.65;
          const accurateResults = response.results.filter(
            (p) => p.similarity_score >= SIMILARITY_THRESHOLD
          );

          if (accurateResults.length === 0) {
            return (
              <div className="flex flex-col items-center justify-center py-20 px-4">
                <div className="bg-slate-800/50 backdrop-blur-md border border-slate-700 rounded-2xl p-12 text-center max-w-md w-full">
                  {/* Icon */}
                  <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-slate-700/60 flex items-center justify-center">
                    <svg className="w-10 h-10 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                        d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
                    </svg>
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-3">No Products Found</h3>
                  <p className="text-gray-400 text-sm leading-relaxed mb-6">
                    We couldn&apos;t find any products that closely match your search.
                    Try using different keywords or a clearer image.
                  </p>
                  <div className="flex flex-col gap-2 text-xs text-slate-500">
                    <span>💡 Use a high-quality, well-lit image</span>
                    <span>💡 Try more descriptive text keywords</span>
                    <span>💡 Search with only text or only image</span>
                  </div>
                </div>
              </div>
            );
          }

          return (
            <div className="space-y-8">
              <div className="flex flex-col md:flex-row gap-6">
                <h2 className="text-3xl font-bold text-white">
                  Results ({accurateResults.length})
                </h2>

                {/* {response.query_analysis && (
                  <div className="flex-1 bg-blue-500/10 border border-blue-500/20 rounded-xl px-4 py-2 flex flex-wrap gap-4 items-center">
                    <span className="text-blue-400 text-sm font-bold uppercase tracking-wider">Analysis:</span>
                    {response.query_analysis.detected_category && (
                      <div className="flex items-center gap-1">
                        <span className="text-gray-500 text-xs">Category:</span>
                        <span className="bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded text-xs font-semibold">
                          {response.query_analysis.detected_category}
                        </span>
                      </div>
                    )}
                    {response.query_analysis.detected_colors?.length ? (
                      <div className="flex items-center gap-1">
                        <span className="text-gray-500 text-xs">Colors:</span>
                        <span className="bg-purple-500/20 text-purple-300 px-2 py-0.5 rounded text-xs font-semibold">
                          {response.query_analysis.detected_colors.join(', ')}
                        </span>
                      </div>
                    ) : null}
                    {response.query_analysis.detected_patterns?.length ? (
                      <div className="flex items-center gap-1">
                        <span className="text-gray-500 text-xs">Pattern:</span>
                        <span className="bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded text-xs font-semibold">
                          {response.query_analysis.detected_patterns.join(', ')}
                        </span>
                      </div>
                    ) : null}
                  </div>
                )} */}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {accurateResults.map((product) => (
                  <div
                    key={product.product_id}
                    className="bg-slate-800/50 backdrop-blur-md rounded-xl border border-slate-700 overflow-hidden hover:border-blue-500 transition flex flex-col"
                  >
                    <Link href={`/product/${product.product_id}`}>
                      <div
                        className="relative cursor-zoom-in"
                        onMouseEnter={() => setHoveredImage(product.product_id)}
                        onMouseLeave={() => setHoveredImage(null)}
                      >
                        <img
                          src={product.image_url}
                          alt={product.title}
                          className="w-full h-48 object-cover transition-transform hover:scale-105"
                        />
                        {hoveredImage === product.product_id && (
                          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm pointer-events-none">
                            <img
                              src={product.image_url}
                              alt={product.title}
                              className="max-w-[90vw] max-h-[90vh] object-contain rounded-lg shadow-2xl border-4 border-blue-500"
                            />
                          </div>
                        )}
                      </div>
                    </Link>
                    <div className="p-4 flex-1 flex flex-col">
                      <Link href={`/product/${product.product_id}`}>
                        <h3 className="text-lg font-semibold text-white mb-2 hover:text-blue-400 transition cursor-pointer">
                          {product.title}
                        </h3>
                      </Link>
                      <p className="text-gray-400 text-sm mb-3 flex-1">{product.description}</p>
                      <div className="flex justify-between items-center mb-4">
                        <span className="text-blue-400 font-semibold">
                          ₹{product.price.toLocaleString('en-IN')}
                        </span>
                        <div className="flex flex-col items-end">
                          <span className="text-xs text-gray-500 mb-1">Match Score</span>
                          <span className="bg-blue-500/20 text-blue-300 px-3 py-1 rounded-full text-sm font-bold border border-blue-500/30">
                            {(product.similarity_score * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>

                      {/* Attribute Chips */}
                      {product.matched_attributes && (
                        <div className="flex flex-wrap gap-1 mb-4">
                          {product.matched_attributes.slice(0, 3).map((attr, idx) => (
                            <span key={idx} className="text-[10px] bg-slate-700/50 text-gray-300 px-2 py-0.5 rounded">
                              {attr}
                            </span>
                          ))}
                        </div>
                      )}
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleAddToCart(product)}
                          disabled={cartLoading === product.product_id}
                          className={`flex-1 py-2 px-3 rounded-lg font-semibold transition text-sm ${addedItems.has(product.product_id)
                            ? 'bg-green-600 hover:bg-green-700 text-white'
                            : 'bg-blue-600 hover:bg-blue-700 text-white'
                            } disabled:opacity-50`}
                        >
                          {cartLoading === product.product_id
                            ? 'Adding...'
                            : addedItems.has(product.product_id)
                              ? '✓ Added'
                              : '🛒 Add to Cart'}
                        </button>
                        <button
                          onClick={() => handleBuyNow(product)}
                          disabled={cartLoading === product.product_id}
                          className="flex-1 py-2 px-3 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white rounded-lg font-semibold transition text-sm"
                        >
                          {cartLoading === product.product_id ? 'Loading...' : 'Buy Now'}
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })()}
      </div>
    </div>
  );
}
