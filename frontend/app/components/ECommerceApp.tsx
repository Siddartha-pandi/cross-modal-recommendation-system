'use client';

import React, { useState, useCallback, useEffect } from 'react';
import AISearchModal from './AISearchModal';
import { 
  ShoppingCart, 
  Heart, 
  User, 
  Menu, 
  Search, 
  Bell,
  MapPin,
  ChevronDown,
  Star,
  Truck,
  Shield,
  RotateCcw,
  Gift,
  Camera,
  Image,
  Sparkles
} from 'lucide-react';

// Types
interface CartItem {
  id: string;
  name: string;
  price: number;
  quantity: number;
  imageUrl: string;
  size?: string;
  color?: string;
}

interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
}

interface Product {
  id: string;
  name: string;
  description: string;
  price: number;
  originalPrice?: number;
  discount?: number;
  imageUrl: string;
  images?: string[];
  category: string;
  brand: string;
  rating: number;
  reviewCount: number;
  availability: 'in_stock' | 'low_stock' | 'out_of_stock';
  features: string[];
  specifications: Record<string, string>;
  shipping: {
    free: boolean;
    days: number;
  };
}

// Import SearchResult interface for conversion
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

// Utility function to convert SearchResult to Product
const convertSearchResultToProduct = (searchResult: SearchResult): Product => {
  return {
    id: searchResult.id,
    name: searchResult.name,
    description: searchResult.description,
    price: searchResult.price,
    originalPrice: searchResult.originalPrice,
    imageUrl: searchResult.imageUrl,
    category: searchResult.category,
    rating: searchResult.rating,
    reviewCount: searchResult.reviewCount,
    availability: searchResult.availability,
    // Default values for required Product fields not in SearchResult
    brand: 'Unknown Brand',
    features: searchResult.crossModalFeatures?.styleAttributes || ['AI Recommended'],
    specifications: {
      'AI Match Score': `${Math.round((searchResult.similarityScore || 0) * 100)}%`,
      'Category': searchResult.category,
      'Detected Features': searchResult.crossModalFeatures?.detectedObjects?.join(', ') || 'Various'
    },
    shipping: { free: true, days: 2 }
  };
};

// Mock Data
const CATEGORIES = [
  'Electronics', 'Fashion', 'Home & Kitchen', 'Books', 'Sports', 'Beauty', 'Automotive', 'Toys'
];

const FEATURED_PRODUCTS: Product[] = [
  {
    id: '1',
    name: 'iPhone 15 Pro Max',
    description: 'Latest iPhone with A17 Pro chip and titanium design',
    price: 1199,
    originalPrice: 1299,
    discount: 8,
    imageUrl: 'https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=400',
    category: 'Electronics',
    brand: 'Apple',
    rating: 4.8,
    reviewCount: 2341,
    availability: 'in_stock',
    features: ['A17 Pro Chip', '5G Ready', 'Pro Camera System', 'Titanium Build'],
    specifications: {
      'Display': '6.7-inch Super Retina XDR',
      'Storage': '256GB',
      'Camera': '48MP Main + 12MP Ultra Wide',
      'Battery': 'Up to 29 hours video playback'
    },
    shipping: { free: true, days: 1 }
  },
  {
    id: '2',
    name: 'Nike Air Max 270',
    description: 'Comfortable lifestyle sneakers with Max Air technology',
    price: 150,
    originalPrice: 180,
    discount: 17,
    imageUrl: 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400',
    category: 'Fashion',
    brand: 'Nike',
    rating: 4.6,
    reviewCount: 892,
    availability: 'in_stock',
    features: ['Max Air Unit', 'Breathable Mesh', 'Rubber Outsole', 'Comfortable Fit'],
    specifications: {
      'Material': 'Synthetic and Mesh',
      'Sole': 'Rubber',
      'Closure': 'Lace-up',
      'Heel Height': '32mm'
    },
    shipping: { free: true, days: 2 }
  },
  {
    id: '3',
    name: 'Samsung 55" QLED 4K TV',
    description: 'Quantum Dot technology with HDR10+ support',
    price: 799,
    originalPrice: 999,
    discount: 20,
    imageUrl: 'https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?w=400',
    category: 'Electronics',
    brand: 'Samsung',
    rating: 4.7,
    reviewCount: 1456,
    availability: 'in_stock',
    features: ['4K UHD', 'HDR10+', 'Smart TV', 'Voice Control'],
    specifications: {
      'Screen Size': '55 inches',
      'Resolution': '3840 x 2160',
      'Refresh Rate': '120Hz',
      'Smart Platform': 'Tizen OS'
    },
    shipping: { free: true, days: 3 }
  }
];

const ECommerceApp: React.FC = () => {
  // State Management
  const [user, setUser] = useState<User | null>(null);
  const [cartItems, setCartItems] = useState<CartItem[]>([]);
  const [wishlist, setWishlist] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [showMobileMenu, setShowMobileMenu] = useState(false);
  const [showCart, setShowCart] = useState(false);
  const [showAISearch, setShowAISearch] = useState(false);

  // Mock login
  useEffect(() => {
    setUser({
      id: '1',
      name: 'John Doe',
      email: 'john@example.com'
    });
  }, []);

  // Cart Functions
  const addToCart = useCallback((product: Product, quantity = 1) => {
    setCartItems(prev => {
      const existing = prev.find(item => item.id === product.id);
      if (existing) {
        return prev.map(item =>
          item.id === product.id
            ? { ...item, quantity: item.quantity + quantity }
            : item
        );
      } else {
        return [...prev, {
          id: product.id,
          name: product.name,
          price: product.price,
          quantity,
          imageUrl: product.imageUrl
        }];
      }
    });
  }, []);

  const removeFromCart = useCallback((productId: string) => {
    setCartItems(prev => prev.filter(item => item.id !== productId));
  }, []);

  const updateQuantity = useCallback((productId: string, quantity: number) => {
    if (quantity <= 0) {
      removeFromCart(productId);
      return;
    }
    setCartItems(prev =>
      prev.map(item =>
        item.id === productId ? { ...item, quantity } : item
      )
    );
  }, [removeFromCart]);

  // Wishlist Functions
  const toggleWishlist = useCallback((productId: string) => {
    setWishlist(prev =>
      prev.includes(productId)
        ? prev.filter(id => id !== productId)
        : [...prev, productId]
    );
  }, []);

  const cartTotal = cartItems.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  const cartItemCount = cartItems.reduce((sum, item) => sum + item.quantity, 0);



  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white/95 backdrop-blur-xl shadow-lg sticky top-0 z-50 border-b border-white/20">
        {/* Enhanced Top Bar */}
        <div className="bg-gradient-to-r from-blue-600 via-purple-600 to-cyan-600 text-white py-2 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-600/90 via-purple-600/90 to-cyan-600/90 animate-pulse"></div>
          <div className="relative max-w-7xl mx-auto px-4 flex justify-between items-center text-sm">
            <div className="flex items-center gap-6">
              <span className="flex items-center gap-2 hover:scale-105 transition-transform duration-200">
                <Truck className="w-4 h-4 animate-bounce-slow" />
                <span className="font-medium">Free Delivery on orders above $50</span>
              </span>
              <span className="flex items-center gap-2 hover:scale-105 transition-transform duration-200">
                <Shield className="w-4 h-4" />
                <span className="font-medium">100% Secure Payments</span>
              </span>
            </div>
            <div className="flex items-center gap-6">
              <span className="flex items-center gap-2">
                <MapPin className="w-4 h-4" />
                <span>Deliver to 12345</span>
              </span>
              <button className="hover:underline font-medium hover:scale-105 transition-all duration-200">Become a Seller ✨</button>
            </div>
          </div>
        </div>

        {/* Main Header */}
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            {/* Enhanced Logo */}
            <div className="flex items-center gap-3 group cursor-pointer">
              <div className="relative w-12 h-12 bg-gradient-to-br from-blue-600 via-purple-600 to-cyan-600 rounded-xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-all duration-300 group-hover:shadow-xl">
                <Sparkles className="w-7 h-7 text-white animate-spin-slow" />
                <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent rounded-xl"></div>
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-cyan-600 bg-clip-text text-transparent group-hover:from-purple-600 group-hover:to-blue-600 transition-all duration-300">
                  SmartShop
                </h1>
                <p className="text-xs text-gray-500 font-medium">🤖 AI-Powered Shopping</p>
              </div>
            </div>

            {/* Search Bar */}
            <div className="flex-1 max-w-2xl mx-8">
              <div className="relative flex">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search for products, brands and more..."
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-l-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={() => setShowAISearch(true)}
                  className="px-4 py-3 bg-purple-600 text-white hover:bg-purple-700 transition-colors"
                  title="AI Visual Search"
                >
                  <Camera className="w-5 h-5" />
                </button>
                <button className="px-6 py-3 bg-blue-600 text-white rounded-r-lg hover:bg-blue-700 transition-colors">
                  <Search className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* User Actions */}
            <div className="flex items-center gap-4">
              <button className="flex items-center gap-1 text-gray-700 hover:text-blue-600">
                <User className="w-5 h-5" />
                <span className="hidden md:block">
                  {user ? user.name : 'Sign In'}
                </span>
                <ChevronDown className="w-4 h-4" />
              </button>

              <button className="relative text-gray-700 hover:text-red-600">
                <Heart className="w-6 h-6" />
                {wishlist.length > 0 && (
                  <span className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                    {wishlist.length}
                  </span>
                )}
              </button>

              <button
                onClick={() => setShowCart(true)}
                className="relative text-gray-700 hover:text-blue-600"
              >
                <ShoppingCart className="w-6 h-6" />
                {cartItemCount > 0 && (
                  <span className="absolute -top-2 -right-2 w-5 h-5 bg-blue-500 text-white text-xs rounded-full flex items-center justify-center">
                    {cartItemCount}
                  </span>
                )}
              </button>

              <button className="text-gray-700 hover:text-blue-600">
                <Bell className="w-6 h-6" />
              </button>
            </div>
          </div>

          {/* Navigation Categories */}
          <nav className="mt-4 border-t pt-4">
            <div className="flex items-center gap-8">
              <button
                onClick={() => setShowMobileMenu(!showMobileMenu)}
                className="flex items-center gap-2 text-gray-700 hover:text-blue-600 md:hidden"
              >
                <Menu className="w-5 h-5" />
                Categories
              </button>
              <div className="hidden md:flex items-center gap-6">
                {CATEGORIES.map(category => (
                  <button
                    key={category}
                    onClick={() => setSelectedCategory(category)}
                    className={`text-sm font-medium transition-colors ${
                      selectedCategory === category
                        ? 'text-blue-600 border-b-2 border-blue-600 pb-1'
                        : 'text-gray-700 hover:text-blue-600'
                    }`}
                  >
                    {category}
                  </button>
                ))}
              </div>
            </div>
          </nav>
        </div>
      </header>

      {/* AI Search Modal */}
      <AISearchModal
        isOpen={showAISearch}
        onClose={() => setShowAISearch(false)}
        onProductSelect={(product) => {
          addToCart(convertSearchResultToProduct(product));
          setShowCart(true);
        }}
      />

      {/* Shopping Cart Sidebar */}
      {showCart && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50">
          <div className="absolute right-0 top-0 h-full w-96 bg-white shadow-2xl">
            <div className="p-6 border-b border-gray-200 flex justify-between items-center">
              <h2 className="text-xl font-bold">Shopping Cart</h2>
              <button
                onClick={() => setShowCart(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <div className="flex-1 overflow-auto p-6">
              {cartItems.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <ShoppingCart className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <p>Your cart is empty</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {cartItems.map(item => (
                    <div key={item.id} className="flex items-center gap-4 bg-gray-50 p-4 rounded-lg">
                      <img src={item.imageUrl} alt={item.name} className="w-16 h-16 object-cover rounded" />
                      <div className="flex-1">
                        <h4 className="font-medium text-sm">{item.name}</h4>
                        <p className="text-blue-600 font-bold">${item.price}</p>
                        <div className="flex items-center gap-2 mt-2">
                          <button
                            onClick={() => updateQuantity(item.id, item.quantity - 1)}
                            className="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center text-sm"
                          >
                            -
                          </button>
                          <span className="text-sm">{item.quantity}</span>
                          <button
                            onClick={() => updateQuantity(item.id, item.quantity + 1)}
                            className="w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center text-sm"
                          >
                            +
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            {cartItems.length > 0 && (
              <div className="border-t border-gray-200 p-6">
                <div className="flex justify-between items-center mb-4">
                  <span className="text-lg font-bold">Total: ${cartTotal.toFixed(2)}</span>
                </div>
                <button className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors">
                  Proceed to Checkout
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Enhanced Hero Banner */}
      <section className="relative bg-gradient-to-br from-purple-600 via-blue-600 to-cyan-600 text-white py-20 overflow-hidden">
        {/* Animated background elements */}
        <div className="absolute inset-0">
          <div className="absolute top-10 left-10 w-20 h-20 bg-white/10 rounded-full animate-float"></div>
          <div className="absolute top-32 right-20 w-16 h-16 bg-yellow-300/20 rounded-full animate-float" style={{ animationDelay: '1s' }}></div>
          <div className="absolute bottom-20 left-32 w-12 h-12 bg-pink-300/20 rounded-full animate-bounce-slow"></div>
          <div className="absolute top-20 right-1/3 w-8 h-8 bg-green-300/20 rounded-full animate-float" style={{ animationDelay: '2s' }}></div>
        </div>
        
        <div className="max-w-7xl mx-auto px-4 relative z-10">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="animate-fadeInUp">
              <div className="mb-6">
                <span className="bg-white/20 text-white text-sm px-4 py-2 rounded-full font-medium backdrop-blur-sm">
                  🚀 AI-Powered Shopping Revolution
                </span>
              </div>
              <h2 className="text-5xl lg:text-6xl font-bold mb-6 leading-tight">
                Smart Shopping
                <span className="block bg-gradient-to-r from-yellow-300 to-pink-300 bg-clip-text text-transparent">
                  with AI Magic
                </span>
              </h2>
              <p className="text-xl text-purple-100 mb-8 leading-relaxed">
                🔍 Find exactly what you're looking for with our revolutionary AI-powered visual search. 
                Upload images, describe products, or let our AI recommend the perfect items for you.
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <button
                  onClick={() => setShowAISearch(true)}
                  className="group bg-white text-purple-600 px-8 py-4 rounded-2xl font-bold text-lg hover:bg-gray-100 transition-all duration-300 flex items-center justify-center gap-3 shadow-2xl hover:shadow-white/20 transform hover:scale-105"
                >
                  <Camera className="w-6 h-6 group-hover:rotate-12 transition-transform duration-300" />
                  Try AI Search Now
                  <Sparkles className="w-5 h-5 animate-spin-slow" />
                </button>
                <button className="border-2 border-white text-white px-8 py-4 rounded-2xl font-bold text-lg hover:bg-white hover:text-purple-600 transition-all duration-300 backdrop-blur-sm hover:shadow-xl transform hover:scale-105">
                  🛍️ Shop Collection
                </button>
              </div>
            </div>
            
            <div className="text-center animate-fadeInUp" style={{ animationDelay: '0.3s' }}>
              <div className="relative">
                <div className="bg-white/10 backdrop-blur-xl rounded-3xl p-12 shadow-2xl border border-white/20 hover:bg-white/15 transition-all duration-500 transform hover:rotate-1">
                  <div className="relative">
                    <Image className="w-32 h-32 mx-auto mb-6 text-white/80 animate-float" />
                    <div className="absolute -top-2 -right-2 w-8 h-8 bg-yellow-400 rounded-full flex items-center justify-center animate-bounce-slow">
                      <Sparkles className="w-4 h-4 text-yellow-800" />
                    </div>
                  </div>
                  <h3 className="text-2xl font-bold mb-4">AI Visual Search</h3>
                  <p className="text-white/90 text-lg leading-relaxed">
                    📱 Upload any image and let our advanced AI find similar products instantly from our vast catalog
                  </p>
                  
                  {/* Feature pills */}
                  <div className="flex flex-wrap justify-center gap-2 mt-6">
                    {['🎯 Precise Match', '⚡ Instant Results', '🤖 Smart AI'].map((feature, idx) => (
                      <span key={idx} className="bg-white/20 text-white text-xs px-3 py-1 rounded-full backdrop-blur-sm">
                        {feature}
                      </span>
                    ))}
                  </div>
                </div>
                
                {/* Floating elements around the card */}
                <div className="absolute -top-4 -left-4 w-8 h-8 bg-gradient-to-r from-pink-400 to-red-400 rounded-full animate-bounce-slow"></div>
                <div className="absolute -bottom-4 -right-4 w-6 h-6 bg-gradient-to-r from-green-400 to-blue-400 rounded-full animate-float"></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Enhanced Features */}
      <section className="py-16 bg-gradient-to-r from-gray-50 via-white to-gray-50">
        <div className="max-w-7xl mx-auto px-4">
          <div className="text-center mb-12">
            <h3 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-blue-600 bg-clip-text text-transparent mb-4">
              Why Choose SmartShop?
            </h3>
            <p className="text-gray-600 text-lg">Experience the future of online shopping with our premium features</p>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {[
              { icon: Truck, title: 'Free Delivery', desc: 'On orders above $50', color: 'from-green-400 to-emerald-500', emoji: '🚚' },
              { icon: RotateCcw, title: 'Easy Returns', desc: '30-day return policy', color: 'from-blue-400 to-cyan-500', emoji: '🔄' },
              { icon: Shield, title: 'Secure Payment', desc: '100% secure checkout', color: 'from-purple-400 to-pink-500', emoji: '🔒' },
              { icon: Gift, title: 'Gift Wrapping', desc: 'Available for all orders', color: 'from-orange-400 to-red-500', emoji: '🎁' }
            ].map(({ icon: Icon, title, desc, color, emoji }, index) => (
              <div 
                key={title} 
                className="group text-center p-6 bg-white rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-500 hover:-translate-y-2 border border-gray-100 animate-fadeInUp"
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <div className={`w-16 h-16 mx-auto mb-4 bg-gradient-to-r ${color} rounded-2xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300`}>
                  <Icon className="w-8 h-8 text-white" />
                </div>
                <h3 className="font-bold text-gray-900 text-lg mb-2 group-hover:text-blue-600 transition-colors duration-300">
                  {emoji} {title}
                </h3>
                <p className="text-sm text-gray-600 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Featured Products */}
      <section className="py-12">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-between mb-10">
            <div className="space-y-2">
              <h2 className="text-4xl font-bold bg-gradient-to-r from-gray-900 via-blue-800 to-purple-800 bg-clip-text text-transparent">
                ✨ Featured Products
              </h2>
              <p className="text-gray-600">Discover our AI-curated selection of trending items</p>
            </div>
            <button className="group bg-gradient-to-r from-blue-500 to-purple-500 text-white px-6 py-3 rounded-xl font-semibold hover:from-blue-600 hover:to-purple-600 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-105">
              View All
              <span className="ml-2 group-hover:translate-x-1 transition-transform duration-300">→</span>
            </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {FEATURED_PRODUCTS.map((product, index) => (
              <div 
                key={product.id} 
                className="group bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden hover:shadow-2xl transition-all duration-500 hover:-translate-y-3 animate-fadeInUp hover:border-purple-200"
                style={{ animationDelay: `${index * 0.15}s` }}
              >
                <div className="relative overflow-hidden">
                  <img
                    src={product.imageUrl}
                    alt={product.name}
                    className="w-full h-56 object-cover group-hover:scale-110 transition-transform duration-700"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/30 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                  
                  {product.discount && (
                    <div className="absolute top-3 left-3 bg-gradient-to-r from-red-500 via-pink-500 to-red-600 text-white px-3 py-1.5 rounded-full text-sm font-bold shadow-lg animate-bounce-slow">
                      🔥 {product.discount}% OFF
                    </div>
                  )}
                  
                  <button
                    onClick={() => toggleWishlist(product.id)}
                    className={`absolute top-3 right-3 w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-300 backdrop-blur-sm shadow-lg hover:scale-110 ${
                      wishlist.includes(product.id)
                        ? 'bg-red-500/90 text-white shadow-red-500/30'
                        : 'bg-white/90 text-gray-600 hover:text-red-500 hover:bg-white hover:shadow-xl'
                    }`}
                  >
                    <Heart className={`w-5 h-5 transition-all duration-300 ${wishlist.includes(product.id) ? 'fill-current animate-pulse' : ''}`} />
                  </button>
                  
                  {/* Hover overlay with quick actions */}
                  <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-all duration-300 flex items-center justify-center">
                    <div className="flex gap-3 transform translate-y-4 group-hover:translate-y-0 transition-transform duration-300">
                      <button className="bg-white/90 text-gray-900 px-4 py-2 rounded-xl font-medium hover:bg-white transition-colors shadow-lg backdrop-blur-sm">
                        Quick View
                      </button>
                      <button className="bg-gradient-to-r from-blue-500 to-purple-500 text-white px-4 py-2 rounded-xl font-medium hover:from-blue-600 hover:to-purple-600 transition-all shadow-lg">
                        Add to Cart
                      </button>
                    </div>
                  </div>
                </div>
                
                <div className="p-6">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs bg-gradient-to-r from-gray-100 to-gray-200 text-gray-700 px-3 py-1.5 rounded-full font-medium">
                      {product.brand}
                    </span>
                    <div className="flex items-center gap-1 bg-yellow-50 px-2 py-1 rounded-full">
                      <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                      <span className="text-sm font-medium text-gray-700">
                        {product.rating}
                      </span>
                      <span className="text-xs text-gray-500">
                        ({product.reviewCount})
                      </span>
                    </div>
                  </div>
                  
                  <h3 className="font-bold text-gray-900 mb-2 line-clamp-2 text-lg group-hover:text-purple-600 transition-colors duration-300">
                    {product.name}
                  </h3>
                  
                  <p className="text-sm text-gray-600 mb-4 line-clamp-2 leading-relaxed">
                    {product.description}
                  </p>
                  
                  <div className="flex items-center gap-3 mb-4">
                    <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                      ${product.price}
                    </span>
                    {product.originalPrice && (
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-400 line-through">
                          ${product.originalPrice}
                        </span>
                        <span className="text-xs bg-red-100 text-red-600 px-2 py-1 rounded-full font-semibold">
                          Save ${product.originalPrice - product.price}
                        </span>
                      </div>
                    )}
                  </div>
                  
                  <div className="flex items-center gap-2 mb-5">
                    {product.shipping.free && (
                      <span className="text-xs bg-gradient-to-r from-green-100 to-emerald-100 text-green-700 px-3 py-1.5 rounded-full font-medium border border-green-200">
                        🚚 Free Delivery
                      </span>
                    )}
                    <span className="text-xs text-gray-500 bg-gray-50 px-2 py-1 rounded-full">
                      ⚡ {product.shipping.days} day delivery
                    </span>
                  </div>
                  
                  <button
                    onClick={() => addToCart(product)}
                    className="w-full bg-gradient-to-r from-blue-600 via-purple-600 to-blue-600 text-white py-3 rounded-xl font-semibold hover:from-blue-700 hover:via-purple-700 hover:to-blue-700 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-[1.02] active:scale-[0.98]"
                  >
                    Add to Cart 🛒
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Newsletter */}
      <section className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-4">Stay Updated</h2>
          <p className="text-gray-300 mb-6">Get the latest deals and product updates</p>
          <div className="flex max-w-md mx-auto gap-2">
            <input
              type="email"
              placeholder="Enter your email"
              className="flex-1 px-4 py-3 rounded-lg text-gray-900"
            />
            <button className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors">
              Subscribe
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-800 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 grid grid-cols-1 md:grid-cols-4 gap-8">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold">SmartShop</span>
            </div>
            <p className="text-gray-300 text-sm">
              AI-powered e-commerce platform for smart shopping experiences.
            </p>
          </div>
          
          <div>
            <h3 className="font-semibold mb-4">Quick Links</h3>
            <ul className="space-y-2 text-sm text-gray-300">
              <li><a href="#" className="hover:text-white">About Us</a></li>
              <li><a href="#" className="hover:text-white">Contact</a></li>
              <li><a href="#" className="hover:text-white">Careers</a></li>
              <li><a href="#" className="hover:text-white">Blog</a></li>
            </ul>
          </div>
          
          <div>
            <h3 className="font-semibold mb-4">Customer Service</h3>
            <ul className="space-y-2 text-sm text-gray-300">
              <li><a href="#" className="hover:text-white">Help Center</a></li>
              <li><a href="#" className="hover:text-white">Returns</a></li>
              <li><a href="#" className="hover:text-white">Shipping Info</a></li>
              <li><a href="#" className="hover:text-white">Track Order</a></li>
            </ul>
          </div>
          
          <div>
            <h3 className="font-semibold mb-4">Legal</h3>
            <ul className="space-y-2 text-sm text-gray-300">
              <li><a href="#" className="hover:text-white">Privacy Policy</a></li>
              <li><a href="#" className="hover:text-white">Terms of Service</a></li>
              <li><a href="#" className="hover:text-white">Cookie Policy</a></li>
            </ul>
          </div>
        </div>
        
        <div className="max-w-7xl mx-auto px-4 mt-8 pt-8 border-t border-gray-700 text-center text-sm text-gray-400">
          <p>&copy; 2025 SmartShop. All rights reserved. Powered by AI technology.</p>
        </div>
      </footer>
    </div>
  );
};

export default ECommerceApp;