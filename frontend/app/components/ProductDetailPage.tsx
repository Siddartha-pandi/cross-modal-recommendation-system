'use client';

import React, { useState, useEffect } from 'react';
import { Heart, Share2, Star, Truck, Shield, RotateCcw, ChevronLeft, ChevronRight, Sparkles } from 'lucide-react';
import { apiClient, ProductResult } from '../lib/api';
import Link from 'next/link';

interface Product {
  id: string;
  title: string;
  price: number;
  originalPrice?: number;
  description: string;
  category: string;
  images: string[];
  tags: string[];
  rating: number;
  reviews: number;
}

export default function ProductDetailPage({ productId }: { productId?: string }) {
  const [selectedImage, setSelectedImage] = useState(0);
  const [similarProducts, setSimilarProducts] = useState<ProductResult[]>([]);
  const [isLoadingSimilar, setIsLoadingSimilar] = useState(false);
  const [product, setProduct] = useState<Product | null>(null);

  useEffect(() => {
    // Mock product data - in a real app, this would come from the backend
    setProduct({
      id: productId || 'dress_001',
      title: 'Elegant Red Evening Dress',
      price: 2999,
      originalPrice: 4999,
      description: 'Beautiful red evening dress perfect for special occasions. Made with premium fabric with elegant design and comfortable fit.',
      category: "Women's Clothing",
      images: ['/dress1.jpg', '/dress2.jpg', '/dress3.jpg'],
      tags: ['Evening Wear', 'Party Dress', 'Red', 'Elegant', 'Premium'],
      rating: 4.5,
      reviews: 128
    });
  }, [productId]);

  const handleFindSimilar = async () => {
    if (!product) return;
    
    setIsLoadingSimilar(true);
    try {
      // Search for similar products using the product title
      const results = await apiClient.getSimilarProducts(product.title, 8);
      setSimilarProducts(results);
    } catch (error) {
      console.error('Error finding similar products:', error);
      alert('Failed to find similar products. Make sure the backend is running.');
    } finally {
      setIsLoadingSimilar(false);
    }
  };

  if (!product) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <Link href="/search" className="flex items-center gap-2 text-gray-600 hover:text-indigo-600 transition">
            <ChevronLeft className="w-5 h-5" />
            Back to Search
          </Link>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="grid md:grid-cols-2 gap-8 mb-12">
          {/* Image Gallery */}
          <div>
            <div className="bg-white dark:bg-gray-800 rounded-2xl overflow-hidden mb-4">
              <div className="aspect-square bg-gray-100 dark:bg-gray-700 relative">
                <img
                  src={product.images[selectedImage] || '/placeholder.png'}
                  alt={product.title}
                  className="w-full h-full object-cover"
                />
                <button className="absolute left-4 top-1/2 -translate-y-1/2 bg-white/80 p-2 rounded-full hover:bg-white transition">
                  <ChevronLeft className="w-6 h-6" />
                </button>
                <button className="absolute right-4 top-1/2 -translate-y-1/2 bg-white/80 p-2 rounded-full hover:bg-white transition">
                  <ChevronRight className="w-6 h-6" />
                </button>
              </div>
            </div>
            <div className="grid grid-cols-4 gap-2">
              {product.images.map((img, idx) => (
                <button
                  key={idx}
                  onClick={() => setSelectedImage(idx)}
                  className={`aspect-square rounded-lg overflow-hidden border-2 ${
                    selectedImage === idx ? 'border-indigo-600' : 'border-transparent'
                  }`}
                >
                  <img src={img || '/placeholder.png'} alt="" className="w-full h-full object-cover" />
                </button>
              ))}
            </div>
          </div>

          {/* Product Info */}
          <div>
            <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-lg">
              <span className="text-sm text-indigo-600 font-semibold">{product.category}</span>
              <h1 className="text-3xl font-bold mt-2 mb-4">{product.title}</h1>
              
              {/* Rating */}
              <div className="flex items-center gap-2 mb-4">
                <div className="flex items-center">
                  {[...Array(5)].map((_, i) => (
                    <Star
                      key={i}
                      className={`w-5 h-5 ${
                        i < Math.floor(product.rating)
                          ? 'fill-yellow-400 text-yellow-400'
                          : 'text-gray-300'
                      }`}
                    />
                  ))}
                </div>
                <span className="text-sm text-gray-600">
                  {product.rating} ({product.reviews} reviews)
                </span>
              </div>

              {/* Price */}
              <div className="mb-6">
                <div className="flex items-baseline gap-3">
                  <span className="text-4xl font-bold text-indigo-600">₹{product.price}</span>
                  {product.originalPrice && (
                    <>
                      <span className="text-xl text-gray-400 line-through">₹{product.originalPrice}</span>
                      <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-semibold">
                        {Math.round((1 - product.price / product.originalPrice) * 100)}% OFF
                      </span>
                    </>
                  )}
                </div>
              </div>

              {/* Description */}
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                {product.description}
              </p>

              {/* AI-Extracted Tags */}
              <div className="mb-6">
                <div className="flex items-center gap-2 mb-2">
                  <Sparkles className="w-4 h-4 text-indigo-600" />
                  <span className="text-sm font-semibold">AI-Extracted Tags</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {product.tags.map((tag, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 bg-indigo-50 dark:bg-indigo-900/20 text-indigo-700 dark:text-indigo-300 rounded-full text-sm"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3 mb-6">
                <button className="flex-1 px-6 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:shadow-lg transition text-lg font-semibold">
                  Add to Cart
                </button>
                <button className="px-4 py-4 border-2 border-gray-300 rounded-xl hover:bg-gray-50 transition">
                  <Heart className="w-6 h-6" />
                </button>
                <button className="px-4 py-4 border-2 border-gray-300 rounded-xl hover:bg-gray-50 transition">
                  <Share2 className="w-6 h-6" />
                </button>
              </div>

              {/* Find Similar Button */}
              <button
                onClick={handleFindSimilar}
                disabled={isLoadingSimilar}
                className="w-full px-6 py-3 bg-purple-100 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300 rounded-xl hover:bg-purple-200 transition flex items-center justify-center gap-2 font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoadingSimilar ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-purple-700"></div>
                    <span>Finding Similar Items...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5" />
                    <span>Find Similar Items (CLIP-Based)</span>
                  </>
                )}
              </button>

              {/* Trust Badges */}
              <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t">
                <div className="text-center">
                  <Truck className="w-8 h-8 text-indigo-600 mx-auto mb-2" />
                  <p className="text-xs text-gray-600">Free Shipping</p>
                </div>
                <div className="text-center">
                  <Shield className="w-8 h-8 text-indigo-600 mx-auto mb-2" />
                  <p className="text-xs text-gray-600">Secure Payment</p>
                </div>
                <div className="text-center">
                  <RotateCcw className="w-8 h-8 text-indigo-600 mx-auto mb-2" />
                  <p className="text-xs text-gray-600">Easy Returns</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Similar Products Section */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-lg">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold">Similar Products (Cross-Modal Results)</h2>
            <span className="text-sm text-gray-600">Ranked by CLIP similarity</span>
          </div>
          
          {similarProducts.length > 0 ? (
            <div className="grid sm:grid-cols-2 md:grid-cols-4 gap-6">
              {similarProducts.map((item) => (
                <Link key={item.product_id} href={`/product/${item.product_id}`} className="group cursor-pointer">
                  <div className="aspect-square bg-gray-100 rounded-xl overflow-hidden mb-3">
                    <img
                      src={item.image_url || '/placeholder.png'}
                      alt={item.title}
                      className="w-full h-full object-cover group-hover:scale-110 transition"
                    />
                  </div>
                  <h3 className="font-semibold text-sm line-clamp-2 mb-1">{item.title}</h3>
                  <div className="flex items-center justify-between">
                    <span className="text-indigo-600 font-bold">₹{item.price}</span>
                    <span className="text-xs text-gray-500">
                      {(item.similarity_score * 100).toFixed(0)}% match
                    </span>
                  </div>
                  {item.category && (
                    <p className="text-xs text-gray-500 mt-1">{item.category}</p>
                  )}
                </Link>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-gray-400">
              <Sparkles className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p>Click "Find Similar Items" to see CLIP-based recommendations</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
