'use client';

import { useState, useRef, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function UserMenu() {
  const { user, logout } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = () => {
    logout();
    setIsOpen(false);
    router.push('/');
  };

  if (!user) return null;

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 transition"
      >
        <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-semibold">
          {user.full_name.charAt(0).toUpperCase()}
        </div>
        <span className="hidden md:block text-white">{user.full_name}</span>
        <svg
          className={`w-4 h-4 text-white transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-48 rounded-lg shadow-lg bg-slate-800 border border-slate-700 py-1 z-50">
          <div className="px-4 py-2 border-b border-slate-700">
            <p className="text-sm text-white font-medium">{user.full_name}</p>
            <p className="text-xs text-gray-400">{user.email}</p>
          </div>
          
          <Link
            href="/recommend"
            className="block px-4 py-2 text-sm text-gray-300 hover:bg-slate-700"
            onClick={() => setIsOpen(false)}
          >
            Search Products
          </Link>

          <Link
            href="/cart"
            className="block px-4 py-2 text-sm text-gray-300 hover:bg-slate-700"
            onClick={() => setIsOpen(false)}
          >
            Shopping Cart
          </Link>

          <Link
            href="/orders"
            className="block px-4 py-2 text-sm text-gray-300 hover:bg-slate-700"
            onClick={() => setIsOpen(false)}
          >
            My Orders
          </Link>
          
          <button
            onClick={handleLogout}
            className="block w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-slate-700"
          >
            Logout
          </button>
        </div>
      )}
    </div>
  );
}
