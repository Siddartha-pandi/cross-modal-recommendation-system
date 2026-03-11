'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api/v1';

export interface CartItem {
  product_id: string;
  title: string;
  price: number;
  quantity: number;
  image_url: string;
}

interface CartContextType {
  items: CartItem[];
  totalPrice: number;
  itemCount: number;
  addToCart: (item: CartItem) => Promise<void>;
  removeFromCart: (productId: string) => Promise<void>;
  updateQuantity: (productId: string, quantity: number) => Promise<void>;
  clearCart: () => Promise<void>;
  getCart: () => Promise<void>;
  loading: boolean;
  error: string | null;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

export function CartProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<CartItem[]>([]);
  const [totalPrice, setTotalPrice] = useState(0);
  const [itemCount, setItemCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getCart = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('auth_token');
      if (!token) return;

      const response = await fetch(`${API_URL}/cart/`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.status === 401) {
        // Token expired or invalid - clear and redirect
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
        return;
      }

      if (!response.ok) throw new Error('Failed to fetch cart');

      const data = await response.json();
      setItems(data.items || []);
      setTotalPrice(data.total_price || 0);
      setItemCount(data.item_count || 0);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const addToCart = async (item: CartItem) => {
    try {
      setLoading(true);
      const token = localStorage.getItem('auth_token');
      if (!token) {
        const err = new Error('Please log in to add items to cart');
        setError(err.message);
        throw err;
      }

      console.log('Adding to cart:', item);
      console.log('API URL:', `${API_URL}/cart/add`);
      console.log('Token exists:', !!token);

      const response = await fetch(`${API_URL}/cart/add`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(item),
      });

      console.log('Cart add response status:', response.status);

      if (response.status === 401) {
        // Token expired or invalid
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
        const err = new Error('Session expired. Please log in again.');
        setError(err.message);
        // Reload page to trigger redirect to login
        setTimeout(() => window.location.href = '/login', 1500);
        throw err;
      }

      if (!response.ok) {
        const errorData = await response.text();
        console.error('Cart add error:', errorData);
        throw new Error(`Failed to add to cart: ${response.status} - ${errorData}`);
      }

      const data = await response.json();
      console.log('Cart updated:', data);
      setItems(data.items || []);
      setTotalPrice(data.total_price || 0);
      setItemCount(data.item_count || 0);
      setError(null);
    } catch (err: any) {
      console.error('addToCart error:', err);
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const removeFromCart = async (productId: string) => {
    try {
      setLoading(true);
      const token = localStorage.getItem('auth_token');
      if (!token) throw new Error('Not authenticated');

      const response = await fetch(`${API_URL}/cart/remove/${productId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) throw new Error('Failed to remove from cart');

      const data = await response.json();
      setItems(data.items || []);
      setTotalPrice(data.total_price || 0);
      setItemCount(data.item_count || 0);
      setError(null);
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const updateQuantity = async (productId: string, quantity: number) => {
    try {
      setLoading(true);
      const token = localStorage.getItem('auth_token');
      if (!token) throw new Error('Not authenticated');

      const response = await fetch(
        `${API_URL}/cart/update/${productId}/${quantity}`,
        {
          method: 'PUT',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) throw new Error('Failed to update quantity');

      const data = await response.json();
      setItems(data.items || []);
      setTotalPrice(data.total_price || 0);
      setItemCount(data.item_count || 0);
      setError(null);
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const clearCart = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('auth_token');
      if (!token) throw new Error('Not authenticated');

      const response = await fetch(`${API_URL}/cart/clear`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) throw new Error('Failed to clear cart');

      setItems([]);
      setTotalPrice(0);
      setItemCount(0);
      setError(null);
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Load cart when component mounts
    const token = localStorage.getItem('auth_token');
    if (token) {
      getCart();
    }
  }, []);

  return (
    <CartContext.Provider
      value={{
        items,
        totalPrice,
        itemCount,
        addToCart,
        removeFromCart,
        updateQuantity,
        clearCart,
        getCart,
        loading,
        error,
      }}
    >
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const context = useContext(CartContext);
  if (context === undefined) {
    throw new Error('useCart must be used within CartProvider');
  }
  return context;
}
