'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

interface Order {
  order_id: string;
  user_id: string;
  items: Array<{
    product_id: string;
    title: string;
    price: number;
    quantity: number;
    image_url: string;
  }>;
  total_price: number;
  shipping_address: string;
  shipping_city: string;
  shipping_zip: string;
  status: string;
  created_at: string;
}

export default function OrderDetailsPage({ params }: { params: { order_id: string } }) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Unwrap params for Next.js 13+
  const [orderId, setOrderId] = useState<string | null>(null);

  useEffect(() => {
    // Handle async params in Next.js 13+
    const unwrapParams = async () => {
      const resolvedParams = await Promise.resolve(params);
      setOrderId(resolvedParams.order_id);
    };
    unwrapParams();
  }, [params]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
      return;
    }

    if (!isLoading && isAuthenticated && orderId) {
      fetchOrder();
    }
  }, [isLoading, isAuthenticated, orderId, router]);

  const fetchOrder = async () => {
    if (!orderId) return;

    try {
      setLoading(true);
      const token = localStorage.getItem('auth_token');

      console.log('Fetching order:', orderId);
      console.log('Token exists:', !!token);

      const response = await fetch(`${API_URL}/orders/${orderId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      console.log('Response status:', response.status);

      if (response.status === 401) {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
        setError('Session expired. Please log in again.');
        setTimeout(() => router.push('/login'), 1500);
        return;
      }

      if (!response.ok) {
        const errorData = await response.text();
        console.error('Error response:', errorData);
        throw new Error(`Order not found (${response.status})`);
      }

      const data = await response.json();
      console.log('Order data:', data);
      setOrder(data);
      setError(null);
    } catch (err: any) {
      console.error('Fetch order error:', err);
      setError(err.message || 'Failed to load order');
    } finally {
      setLoading(false);
    }
  };

  if (isLoading || loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <h1 className="text-2xl font-bold text-white">Loading...</h1>
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-neutral-900">
        <nav className="bg-slate-900/80 backdrop-blur-md border-b border-slate-800">
          <div className="container mx-auto px-4 py-4 max-w-7xl">
            <Link href="/" className="text-2xl font-bold text-white hover:text-blue-400">
              Fashion Finder
            </Link>
          </div>
        </nav>
        <div className="container mx-auto px-4 py-8 max-w-7xl">
          <div className="bg-red-500/20 border border-red-500 rounded-xl p-6 max-w-2xl mx-auto">
            <h2 className="text-xl font-bold text-red-300 mb-3">
              {error || 'Order not found'}
            </h2>
            <p className="text-red-200 mb-4">
              We couldn't find the order you're looking for. This might be because:
            </p>
            <ul className="list-disc list-inside text-red-200 mb-6 space-y-1">
              <li>The order ID is incorrect</li>
              <li>You don't have permission to view this order</li>
              <li>Your session has expired</li>
            </ul>
            <div className="flex gap-4">
              <Link
                href="/orders"
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
              >
                View All Orders
              </Link>
              <Link
                href="/recommend"
                className="px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition"
              >
                Continue Shopping
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const orderDate = new Date(order.created_at).toLocaleDateString();
  const statusColor = {
    pending: 'bg-yellow-500/20 text-yellow-300',
    processing: 'bg-blue-500/20 text-blue-300',
    shipped: 'bg-purple-500/20 text-purple-300',
    delivered: 'bg-green-500/20 text-green-300',
  }[order.status] || 'bg-gray-500/20 text-gray-300';

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-neutral-900">
      {/* Navigation */}
      <nav className="bg-slate-900/80 backdrop-blur-md border-b border-slate-800 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 max-w-7xl flex justify-between items-center">
          <Link href="/" className="text-2xl font-bold text-white hover:text-blue-400">
            Fashion Finder
          </Link>
          <Link
            href="/recommend"
            className="text-gray-300 hover:text-white transition"
          >
            Continue Shopping
          </Link>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Success Message */}
        <div className="mb-8 bg-green-500/20 border border-green-500 rounded-xl p-6">
          <div className="flex gap-4">
            <div className="text-3xl">✓</div>
            <div>
              <h1 className="text-2xl font-bold text-green-300 mb-2">
                Order Placed Successfully!
              </h1>
              <p className="text-green-200">
                Thank you for your purchase. Your order has been received and is being processed.
              </p>
            </div>
          </div>
        </div>

        {/* Order Details */}
        <div className="bg-slate-800/50 backdrop-blur-md rounded-xl border border-slate-700 p-8 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8 pb-8 border-b border-slate-700">
            <div>
              <p className="text-gray-400 text-sm mb-2">Order ID</p>
              <p className="text-2xl font-bold text-white">#{order.order_id}</p>
            </div>
            <div>
              <p className="text-gray-400 text-sm mb-2">Order Date</p>
              <p className="text-2xl font-bold text-white">{orderDate}</p>
            </div>
            <div>
              <p className="text-gray-400 text-sm mb-2">Status</p>
              <span className={`inline-block px-4 py-2 rounded-full font-semibold ${statusColor}`}>
                {order.status.charAt(0).toUpperCase() + order.status.slice(1)}
              </span>
            </div>
            <div>
              <p className="text-gray-400 text-sm mb-2">Total Amount</p>
              <p className="text-2xl font-bold text-blue-400">₹{order.total_price.toLocaleString('en-IN')}</p>
            </div>
          </div>

          {/* Shipping Address */}
          <div className="mb-8">
            <h2 className="text-lg font-bold text-white mb-4">Shipping Address</h2>
            <div className="bg-slate-900/50 rounded-lg p-4 text-gray-300">
              <p>{order.shipping_address}</p>
              <p>{order.shipping_city}, {order.shipping_zip}</p>
            </div>
          </div>
        </div>

        {/* Order Items */}
        <div className="bg-slate-800/50 backdrop-blur-md rounded-xl border border-slate-700 p-8 mb-8">
          <h2 className="text-2xl font-bold text-white mb-6">Order Items</h2>
          <div className="space-y-4">
            {order.items.map((item) => (
              <div
                key={item.product_id}
                className="flex gap-4 pb-4 border-b border-slate-700 last:border-0"
              >
                <img
                  src={item.image_url}
                  alt={item.title}
                  className="w-20 h-20 object-cover rounded-lg"
                />
                <div className="flex-1">
                  <h3 className="text-white font-semibold mb-2">{item.title}</h3>
                  <p className="text-gray-400 text-sm">
                    Quantity: {item.quantity}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-blue-400 font-semibold">
                    ₹{item.price.toLocaleString('en-IN')}
                  </p>
                  <p className="text-gray-400 text-sm">
                    Subtotal: ₹{(item.price * item.quantity).toLocaleString('en-IN')}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-4 justify-center mb-8">
          <Link
            href="/recommend"
            className="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition"
          >
            Continue Shopping
          </Link>
          <Link
            href="/orders"
            className="px-8 py-3 bg-slate-700 hover:bg-slate-600 text-white font-semibold rounded-lg transition"
          >
            View All Orders
          </Link>
        </div>
      </div>
    </div>
  );
}
