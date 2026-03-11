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

export default function OrdersPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
      return;
    }

    if (!isLoading && isAuthenticated) {
      fetchOrders();
    }
  }, [isLoading, isAuthenticated, router]);

  const fetchOrders = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('auth_token');

      console.log('Fetching orders list');
      console.log('Token exists:', !!token);

      const response = await fetch(`${API_URL}/orders/`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      console.log('Orders response status:', response.status);

      if (response.status === 401) {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
        router.push('/login');
        return;
      }

      if (!response.ok) {
        const errorData = await response.text();
        console.error('Error fetching orders:', errorData);
        throw new Error('Failed to fetch orders');
      }

      const data = await response.json();
      console.log('Orders data:', data);
      setOrders(Array.isArray(data) ? data : []);
      setError(null);
    } catch (err: any) {
      console.error('Fetch orders error:', err);
      setError(err.message || 'Failed to load orders');
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

  const statusColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'bg-yellow-500/20 text-yellow-300',
      processing: 'bg-blue-500/20 text-blue-300',
      shipped: 'bg-purple-500/20 text-purple-300',
      delivered: 'bg-green-500/20 text-green-300',
    };
    return colors[status] || 'bg-gray-500/20 text-gray-300';
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
              Shop
            </Link>
            <Link
              href="/cart"
              className="text-gray-300 hover:text-white transition"
            >
              Cart
            </Link>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <h1 className="text-4xl font-bold text-white mb-8">My Orders</h1>

        {error && (
          <div className="mb-6 bg-red-500/20 border border-red-500 text-red-300 px-4 py-4 rounded-lg">
            {error}
          </div>
        )}

        {orders.length === 0 ? (
          <div className="text-center py-12">
            <h2 className="text-2xl font-semibold text-white mb-4">No orders yet</h2>
            <p className="text-gray-400 mb-6">Start shopping to place your first order</p>
            <Link
              href="/simple"
              className="inline-block px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
            >
              Start Shopping
            </Link>
          </div>
        ) : (
          <div className="space-y-6">
            {orders.map((order) => (
              <Link
                key={order.order_id}
                href={`/orders/${order.order_id}`}
                className="block"
              >
                <div className="bg-slate-800/50 backdrop-blur-md rounded-xl border border-slate-700 p-6 hover:border-blue-500 transition">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                    <div>
                      <p className="text-gray-400 text-sm mb-1">Order ID</p>
                      <p className="text-white font-semibold">#{order.order_id}</p>
                    </div>
                    <div>
                      <p className="text-gray-400 text-sm mb-1">Date</p>
                      <p className="text-white font-semibold">
                        {new Date(order.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-400 text-sm mb-1">Total</p>
                      <p className="text-blue-400 font-semibold">
                        ₹{order.total_price.toLocaleString('en-IN')}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-400 text-sm mb-1">Status</p>
                      <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${statusColor(order.status)}`}>
                        {order.status.charAt(0).toUpperCase() + order.status.slice(1)}
                      </span>
                    </div>
                  </div>
                  <div className="pt-4 border-t border-slate-700">
                    <p className="text-gray-400 text-sm">
                      {order.items.length} item{order.items.length > 1 ? 's' : ''}
                    </p>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
