'use client';

import { useState } from 'react';
import { Button } from './ui/button';
import { 
  Heart, 
  Share2, 
  Star, 
  Truck, 
  Shield,
  RotateCcw,
  ExternalLink,
  Sparkles,
  Box,
  Camera,
  Info
} from 'lucide-react';

interface Product {
  product_id: string;
  title: string;
  description: string;
  image_url: string;
  price: number;
  source: string;
  buy_url: string;
  category?: string;
  brand?: string;
  rating?: number;
  score?: number;
  match_tags?: string[];
}

interface ProductDetailProps {
  product: Product;
  onClose: () => void;
  onTryOn3D: (product: Product) => void;
  onTryOnAR: (product: Product) => void;
}

export default function ProductDetail({ product, onClose, onTryOn3D, onTryOnAR }: ProductDetailProps) {
  const [isFavorite, setIsFavorite] = useState(false);
  const [quantity, setQuantity] = useState(1);

  const formatMatchTag = (tag: string) => {
    return tag.split('-').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  const getMatchTagColor = (tag: string) => {
    if (tag.includes('excellent')) return 'bg-green-100 text-green-800 border-green-300';
    if (tag.includes('great')) return 'bg-blue-100 text-blue-800 border-blue-300';
    if (tag.includes('good')) return 'bg-purple-100 text-purple-800 border-purple-300';
    if (tag.includes('color')) return 'bg-pink-100 text-pink-800 border-pink-300';
    if (tag.includes('style')) return 'bg-indigo-100 text-indigo-800 border-indigo-300';
    return 'bg-gray-100 text-gray-800 border-gray-300';
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-5xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-pink-600 text-white p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Sparkles className="w-6 h-6" />
            <h2 className="text-xl font-bold">Product Details</h2>
          </div>
          <button
            onClick={onClose}
            className="text-white hover:bg-white/20 rounded-full p-2 transition"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="overflow-y-auto max-h-[calc(90vh-80px)]">
          <div className="grid md:grid-cols-2 gap-6 p-6">
            {/* Left: Image */}
            <div className="space-y-4">
              <div className="relative aspect-square rounded-xl overflow-hidden bg-gray-100 shadow-lg">
                <img 
                  src={product.image_url} 
                  alt={product.title}
                  className="w-full h-full object-cover"
                />
                
                {/* AI Match Score Badge */}
                {product.score && (
                  <div className="absolute top-4 right-4 bg-white/95 backdrop-blur-sm rounded-full px-4 py-2 shadow-lg">
                    <div className="flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-purple-600" />
                      <span className="text-sm font-bold text-gray-900">
                        {Math.round(product.score * 100)}% Match
                      </span>
                    </div>
                  </div>
                )}

                {/* Source Badge */}
                <div className="absolute bottom-4 left-4 bg-black/80 backdrop-blur-sm text-white px-3 py-1 rounded-full text-xs font-medium">
                  {product.source}
                </div>
              </div>

              {/* Try-On Buttons */}
              <div className="grid grid-cols-2 gap-3">
                <Button
                  onClick={() => onTryOn3D(product)}
                  className="bg-purple-600 hover:bg-purple-700 flex items-center justify-center gap-2"
                >
                  <Box className="w-4 h-4" />
                  3D Try-On
                </Button>
                <Button
                  onClick={() => onTryOnAR(product)}
                  className="bg-blue-600 hover:bg-blue-700 flex items-center justify-center gap-2"
                >
                  <Camera className="w-4 h-4" />
                  AR Try-On
                </Button>
              </div>
            </div>

            {/* Right: Details */}
            <div className="space-y-6">
              {/* Title & Rating */}
              <div>
                <h1 className="text-2xl font-bold text-gray-900 mb-2">
                  {product.title}
                </h1>
                
                {product.rating && (
                  <div className="flex items-center gap-2 mb-3">
                    <div className="flex">
                      {[...Array(5)].map((_, i) => (
                        <Star
                          key={i}
                          className={`w-4 h-4 ${
                            i < Math.floor(product.rating!) 
                              ? 'fill-yellow-400 text-yellow-400' 
                              : 'text-gray-300'
                          }`}
                        />
                      ))}
                    </div>
                    <span className="text-sm text-gray-600">
                      {product.rating.toFixed(1)} / 5.0
                    </span>
                  </div>
                )}

                {/* Category & Brand */}
                <div className="flex gap-2 text-sm text-gray-600">
                  {product.brand && <span>By {product.brand}</span>}
                  {product.category && (
                    <>
                      <span>•</span>
                      <span>{product.category}</span>
                    </>
                  )}
                </div>
              </div>

              {/* Match Tags */}
              {product.match_tags && product.match_tags.length > 0 && (
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Info className="w-4 h-4 text-purple-600" />
                    <h3 className="font-semibold text-sm text-gray-900">Why This Match?</h3>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {product.match_tags.map((tag, idx) => (
                      <span
                        key={idx}
                        className={`text-xs px-3 py-1 rounded-full font-medium border ${getMatchTagColor(tag)}`}
                      >
                        {formatMatchTag(tag)}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Price */}
              <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl p-4 border border-purple-200">
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-bold text-purple-900">
                    ${product.price.toFixed(2)}
                  </span>
                  <span className="text-sm text-gray-600">USD</span>
                </div>
              </div>

              {/* Description */}
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Description</h3>
                <p className="text-gray-700 text-sm leading-relaxed">
                  {product.description}
                </p>
              </div>

              {/* Quantity Selector */}
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Quantity</h3>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setQuantity(Math.max(1, quantity - 1))}
                    className="w-10 h-10 rounded-lg border border-gray-300 hover:bg-gray-100 flex items-center justify-center font-bold"
                  >
                    -
                  </button>
                  <span className="w-12 text-center font-semibold">{quantity}</span>
                  <button
                    onClick={() => setQuantity(quantity + 1)}
                    className="w-10 h-10 rounded-lg border border-gray-300 hover:bg-gray-100 flex items-center justify-center font-bold"
                  >
                    +
                  </button>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="space-y-3">
                <a
                  href={product.buy_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-full"
                >
                  <Button className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold py-6 text-lg">
                    <ExternalLink className="w-5 h-5 mr-2" />
                    Buy Now on {product.source}
                  </Button>
                </a>

                <div className="grid grid-cols-2 gap-3">
                  <Button
                    variant="outline"
                    onClick={() => setIsFavorite(!isFavorite)}
                    className={isFavorite ? 'border-red-300 bg-red-50' : ''}
                  >
                    <Heart className={`w-4 h-4 mr-2 ${isFavorite ? 'fill-red-500 text-red-500' : ''}`} />
                    {isFavorite ? 'Saved' : 'Save'}
                  </Button>
                  <Button variant="outline">
                    <Share2 className="w-4 h-4 mr-2" />
                    Share
                  </Button>
                </div>
              </div>

              {/* Trust Badges */}
              <div className="grid grid-cols-3 gap-4 pt-4 border-t">
                <div className="text-center">
                  <Truck className="w-6 h-6 mx-auto mb-1 text-green-600" />
                  <p className="text-xs text-gray-600">Free Shipping</p>
                </div>
                <div className="text-center">
                  <Shield className="w-6 h-6 mx-auto mb-1 text-blue-600" />
                  <p className="text-xs text-gray-600">Secure Payment</p>
                </div>
                <div className="text-center">
                  <RotateCcw className="w-6 h-6 mx-auto mb-1 text-purple-600" />
                  <p className="text-xs text-gray-600">Easy Returns</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

