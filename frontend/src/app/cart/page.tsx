'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { useCart } from '@/contexts/CartContext';
import { useRouter } from 'next/navigation';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

interface CheckoutFormData {
  shipping_address: string;
  shipping_city: string;
  shipping_zip: string;
}

export default function CartPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const { items, totalPrice, removeFromCart, updateQuantity, loading: cartLoading } = useCart();
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [formData, setFormData] = useState<CheckoutFormData>({
    shipping_address: '',
    shipping_city: '',
    shipping_zip: '',
  });
  const [showCheckout, setShowCheckout] = useState(false);

  // Redirect if not authenticated
  if (!isLoading && !isAuthenticated) {
    router.push('/login');
    return null;
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <h1 className="text-2xl font-bold text-white">Loading...</h1>
      </div>
    );
  }

  const handleQuantityChange = async (productId: string, newQuantity: number) => {
    if (newQuantity <= 0) {
      await removeFromCart(productId);
    } else {
      await updateQuantity(productId, newQuantity);
    }
  };

  const handleCheckout = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.shipping_address || !formData.shipping_city || !formData.shipping_zip) {
      setError('Please fill in all shipping information');
      return;
    }

    if (items.length === 0) {
      setError('Your cart is empty');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const token = localStorage.getItem('auth_token');

      console.log('Processing checkout...');

      const response = await fetch(`${API_URL}/orders/checkout`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      console.log('Checkout response status:', response.status);

      if (response.status === 401) {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
        setError('Session expired. Please log in again.');
        setTimeout(() => router.push('/login'), 1500);
        return;
      }

      if (!response.ok) {
        const data = await response.json();
        console.error('Checkout error:', data);
        throw new Error(data.detail || 'Checkout failed');
      }

      const order = await response.json();
      console.log('Order created:', order);
      console.log('Order ID:', order.order_id);
      setSuccess(true);
      setShowCheckout(false);

      // Redirect to order confirmation after 2 seconds
      setTimeout(() => {
        console.log('Redirecting to order:', `/orders/${order.order_id}`);
        router.push(`/orders/${order.order_id}`);
      }, 2000);
    } catch (err: any) {
      console.error('Checkout error:', err);
      setError(err.message || 'Checkout failed');
    } finally {
      setLoading(false);
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
          <div className="flex gap-6">
            <Link
              href="/simple"
              className="text-gray-300 hover:text-white transition"
            >
              Continue Shopping
            </Link>
            <span className="text-gray-300">Cart ({items.length})</span>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <h1 className="text-4xl font-bold text-white mb-8">Shopping Cart</h1>

        {success && (
          <div className="mb-6 bg-green-500/20 border border-green-500 text-green-300 px-4 py-4 rounded-lg">
            Order placed successfully! Redirecting to order confirmation...
          </div>
        )}

        {error && (
          <div className="mb-6 bg-red-500/20 border border-red-500 text-red-300 px-4 py-4 rounded-lg">
            {error}
          </div>
        )}

        {items.length === 0 ? (
          <div className="text-center py-12">
            <h2 className="text-2xl font-semibold text-white mb-4">Your cart is empty</h2>
            <Link
              href="/simple"
              className="inline-block px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
            >
              Start Shopping
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Cart Items */}
            <div className="lg:col-span-2 space-y-4">
              {items.map((item) => (
                <div
                  key={item.product_id}
                  className="bg-slate-800/50 backdrop-blur-md rounded-xl border border-slate-700 p-6 flex gap-6"
                >
                  <img
                    src={item.image_url}
                    alt={item.title}
                    className="w-24 h-24 object-cover rounded-lg"
                  />
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-white mb-2">
                      {item.title}
                    </h3>
                    <p className="text-blue-400 text-lg font-semibold mb-4">
                      ₹{item.price.toLocaleString('en-IN')}
                    </p>
                    <div className="flex items-center gap-4">
                      <div className="flex items-center border border-slate-600 rounded-lg">
                        <button
                          onClick={() =>
                            handleQuantityChange(item.product_id, item.quantity - 1)
                          }
                          className="px-3 py-2 text-white hover:bg-slate-700 transition"
                        >
                          −
                        </button>
                        <span className="px-4 py-2 text-white">{item.quantity}</span>
                        <button
                          onClick={() =>
                            handleQuantityChange(item.product_id, item.quantity + 1)
                          }
                          className="px-3 py-2 text-white hover:bg-slate-700 transition"
                        >
                          +
                        </button>
                      </div>
                      <button
                        onClick={() => removeFromCart(item.product_id)}
                        className="text-red-400 hover:text-red-300 transition ml-auto"
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-gray-300 text-sm mb-2">Subtotal</p>
                    <p className="text-xl font-bold text-white">
                      ₹{(item.price * item.quantity).toLocaleString('en-IN')}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            {/* Order Summary */}
            <div className="lg:col-span-1">
              <div className="bg-slate-800/50 backdrop-blur-md rounded-xl border border-slate-700 p-6 sticky top-24">
                <h2 className="text-xl font-bold text-white mb-4">Order Summary</h2>

                <div className="space-y-3 mb-6 border-b border-slate-700 pb-6">
                  <div className="flex justify-between text-gray-300">
                    <span>Subtotal</span>
                    <span>₹{totalPrice.toLocaleString('en-IN')}</span>
                  </div>
                  <div className="flex justify-between text-gray-300">
                    <span>Shipping</span>
                    <span>Free</span>
                  </div>
                  <div className="flex justify-between text-gray-300">
                    <span>Tax</span>
                    <span>Calculated at checkout</span>
                  </div>
                </div>

                <div className="mb-6">
                  <div className="flex justify-between items-center">
                    <span className="text-lg font-semibold text-white">Total</span>
                    <span className="text-2xl font-bold text-blue-400">
                      ₹{totalPrice.toLocaleString('en-IN')}
                    </span>
                  </div>
                </div>

                {!showCheckout ? (
                  <button
                    onClick={() => setShowCheckout(true)}
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg transition"
                  >
                    Proceed to Checkout
                  </button>
                ) : (
                  <form onSubmit={handleCheckout} className="space-y-4">
                    <div>
                      <label className="block text-sm text-gray-300 mb-2">
                        Street Address
                      </label>
                      <input
                        type="text"
                        required
                        value={formData.shipping_address}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            shipping_address: e.target.value,
                          })
                        }
                        className="w-full px-3 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="123 Main St"
                      />
                    </div>

                    <div>
                      <label className="block text-sm text-gray-300 mb-2">
                        City
                      </label>
                      <input
                        type="text"
                        required
                        value={formData.shipping_city}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            shipping_city: e.target.value,
                          })
                        }
                        className="w-full px-3 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="New York"
                      />
                    </div>

                    <div>
                      <label className="block text-sm text-gray-300 mb-2">
                        ZIP Code
                      </label>
                      <input
                        type="text"
                        required
                        value={formData.shipping_zip}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            shipping_zip: e.target.value,
                          })
                        }
                        className="w-full px-3 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="10001"
                      />
                    </div>

                    <button
                      type="submit"
                      disabled={loading || cartLoading}
                      className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white font-semibold py-3 rounded-lg transition"
                    >
                      {loading ? 'Processing...' : 'Place Order'}
                    </button>

                    <button
                      type="button"
                      onClick={() => setShowCheckout(false)}
                      className="w-full bg-slate-700 hover:bg-slate-600 text-white font-semibold py-2 rounded-lg transition"
                    >
                      Cancel
                    </button>
                  </form>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
