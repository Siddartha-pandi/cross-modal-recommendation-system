'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { useCart } from '@/contexts/CartContext';
import UserMenu from '@/components/UserMenu';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

interface Product {
  product_id: string;
  title: string;
  description: string;
  image_url: string;
  price: number;
  category: string;
  brand?: string;
  material?: string;
  color?: string;
  size?: string;
  rating?: number;
  tags?: string[];
}

export default function ProductDetailPage({ params }: { params: Promise<{ product_id: string }> }) {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const { addToCart, itemCount } = useCart();
  
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cartLoading, setCartLoading] = useState(false);
  const [addedToCart, setAddedToCart] = useState(false);
  const [productId, setProductId] = useState<string | null>(null);
  const [quantity, setQuantity] = useState(1);

  // Unwrap params
  useEffect(() => {
    params.then((resolvedParams) => {
      setProductId(resolvedParams.product_id);
    });
  }, [params]);

  // Fetch product details
  useEffect(() => {
    if (!productId) return;

    const fetchProduct = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch(`${API_URL}/products/${productId}`);
        
        if (!response.ok) {
          if (response.status === 404) {
            setError('Product not found');
          } else {
            setError('Failed to load product details');
          }
          return;
        }

        const data = await response.json();
        setProduct(data);
      } catch (err: any) {
        console.error('Error fetching product:', err);
        setError(err.message || 'Failed to load product');
      } finally {
        setLoading(false);
      }
    };

    fetchProduct();
  }, [productId]);

  // Handle authentication redirect
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [authLoading, isAuthenticated, router]);

  const handleAddToCart = async () => {
    if (!product) return;

    try {
      setCartLoading(true);
      setError(null);
      
      await addToCart({
        product_id: String(product.product_id),
        title: product.title,
        price: product.price,
        quantity: quantity,
        image_url: product.image_url,
      });
      
      setAddedToCart(true);
      setTimeout(() => setAddedToCart(false), 2000);
    } catch (err: any) {
      console.error('Failed to add to cart:', err);
      setError(err.message || 'Failed to add to cart');
    } finally {
      setCartLoading(false);
    }
  };

  const handleBuyNow = async () => {
    if (!product) return;

    try {
      setCartLoading(true);
      
      await addToCart({
        product_id: String(product.product_id),
        title: product.title,
        price: product.price,
        quantity: quantity,
        image_url: product.image_url,
      });
      
      router.push('/cart');
    } catch (err: any) {
      setError(err.message || 'Failed to process purchase');
      setCartLoading(false);
    }
  };

  // Loading state
  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-white mb-4">Loading...</h1>
        </div>
      </div>
    );
  }

  // Error state
  if (error && !product) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-neutral-900">
        {/* Navigation */}
        <nav className="bg-slate-900/80 backdrop-blur-md border-b border-slate-800 sticky top-0 z-50">
          <div className="container mx-auto px-4 py-4 max-w-7xl flex justify-between items-center">
            <Link href="/recommend" className="text-2xl font-bold text-white hover:text-blue-400">
              Fashion Finder
            </Link>
            <div className="flex items-center gap-4">
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

        <div className="container mx-auto px-4 py-16 max-w-4xl text-center">
          <div className="bg-red-500/20 border border-red-500 rounded-xl p-8">
            <h1 className="text-3xl font-bold text-red-300 mb-4">{error}</h1>
            <Link
              href="/recommend"
              className="inline-block mt-4 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition"
            >
              Back to Search
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (!product) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-neutral-900">
      {/* Navigation */}
      <nav className="bg-slate-900/80 backdrop-blur-md border-b border-slate-800 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 max-w-7xl flex justify-between items-center">
          <Link href="/recommend" className="text-2xl font-bold text-white hover:text-blue-400">
            Fashion Finder
          </Link>
          <div className="flex items-center gap-4">
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

      {/* Product Detail */}
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Breadcrumb */}
        <div className="mb-6">
          <Link href="/recommend" className="text-blue-400 hover:text-blue-300 transition">
            ← Back to Search
          </Link>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-red-500/20 border border-red-500 text-red-300 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        <div className="grid md:grid-cols-2 gap-8">
          {/* Image Section */}
          <div className="bg-slate-800/50 backdrop-blur-md rounded-2xl border border-slate-700 p-4 overflow-hidden">
            <img
              src={product.image_url}
              alt={product.title}
              className="w-full h-auto object-contain rounded-lg"
            />
          </div>

          {/* Product Info Section */}
          <div className="space-y-6">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2">{product.title}</h1>
              {product.brand && (
                <p className="text-blue-400 text-lg mb-4">by {product.brand}</p>
              )}
              {product.rating && (
                <div className="flex items-center gap-2 mb-4">
                  <div className="flex text-yellow-400">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <span key={i}>
                        {i < Math.floor(product.rating!) ? '★' : '☆'}
                      </span>
                    ))}
                  </div>
                  <span className="text-gray-400">({product.rating})</span>
                </div>
              )}
            </div>

            <div className="bg-slate-800/30 rounded-xl p-6 border border-slate-700">
              <div className="text-4xl font-bold text-blue-400 mb-4">
                ₹{product.price.toLocaleString()}
              </div>

              {/* Product Details */}
              <div className="space-y-3 mb-6">
                {product.category && (
                  <div className="flex justify-between">
                    <span className="text-gray-400">Category:</span>
                    <span className="text-white capitalize">{product.category}</span>
                  </div>
                )}
                {product.color && (
                  <div className="flex justify-between">
                    <span className="text-gray-400">Color:</span>
                    <span className="text-white capitalize">{product.color}</span>
                  </div>
                )}
                {product.material && (
                  <div className="flex justify-between">
                    <span className="text-gray-400">Material:</span>
                    <span className="text-white capitalize">{product.material}</span>
                  </div>
                )}
                {product.size && (
                  <div className="flex justify-between">
                    <span className="text-gray-400">Size:</span>
                    <span className="text-white">{product.size}</span>
                  </div>
                )}
              </div>

              {/* Quantity Selector */}
              <div className="mb-6">
                <label className="block text-gray-400 mb-2">Quantity:</label>
                <div className="flex items-center gap-4">
                  <button
                    onClick={() => setQuantity(Math.max(1, quantity - 1))}
                    className="w-10 h-10 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-bold transition"
                  >
                    -
                  </button>
                  <span className="text-2xl text-white font-semibold w-12 text-center">
                    {quantity}
                  </span>
                  <button
                    onClick={() => setQuantity(quantity + 1)}
                    className="w-10 h-10 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-bold transition"
                  >
                    +
                  </button>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="space-y-3">
                <button
                  onClick={handleAddToCart}
                  disabled={cartLoading}
                  className={`w-full py-4 px-6 rounded-lg font-semibold text-lg transition ${
                    addedToCart
                      ? 'bg-green-600 hover:bg-green-700 text-white'
                      : 'bg-blue-600 hover:bg-blue-700 text-white'
                  } disabled:opacity-50`}
                >
                  {cartLoading
                    ? 'Adding...'
                    : addedToCart
                    ? '✓ Added to Cart'
                    : '🛒 Add to Cart'}
                </button>
                <button
                  onClick={handleBuyNow}
                  disabled={cartLoading}
                  className="w-full py-4 px-6 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white rounded-lg font-semibold text-lg transition"
                >
                  Buy Now
                </button>
              </div>
            </div>

            {/* Description */}
            {product.description && (
              <div className="bg-slate-800/30 rounded-xl p-6 border border-slate-700">
                <h2 className="text-xl font-bold text-white mb-3">Description</h2>
                <p className="text-gray-300 leading-relaxed">{product.description}</p>
              </div>
            )}

            {/* Tags */}
            {product.tags && product.tags.length > 0 && (
              <div className="bg-slate-800/30 rounded-xl p-6 border border-slate-700">
                <h2 className="text-xl font-bold text-white mb-3">Tags</h2>
                <div className="flex flex-wrap gap-2">
                  {product.tags.map((tag, index) => (
                    <span
                      key={index}
                      className="bg-blue-500/20 text-blue-300 px-3 py-1 rounded-full text-sm"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
