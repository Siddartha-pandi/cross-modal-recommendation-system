'use client';

import React from 'react';
import { Search, Upload, Sparkles, TrendingUp, Zap, Shield, Heart } from 'lucide-react';
import Link from 'next/link';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-indigo-900">
      {/* Header */}
      <header className="border-b bg-white/80 dark:bg-gray-900/80 backdrop-blur-md sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-8 h-8 text-indigo-600" />
              <span className="text-xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                Cross-Modal Fashion Recommendation
              </span>
            </div>
            <nav className="hidden md:flex items-center space-x-8">
              <Link href="/" className="text-gray-700 dark:text-gray-300 hover:text-indigo-600 transition">
                Home
              </Link>
              <Link href="/search" className="text-gray-700 dark:text-gray-300 hover:text-indigo-600 transition">
                Explore
              </Link>
              <Link href="/upload" className="text-gray-700 dark:text-gray-300 hover:text-indigo-600 transition">
                Upload
              </Link>
              <Link href="/dashboard" className="text-gray-700 dark:text-gray-300 hover:text-indigo-600 transition">
                Dashboard
              </Link>
            </nav>
            <div className="flex items-center space-x-4">
              <button className="px-4 py-2 text-indigo-600 hover:text-indigo-700 transition">
                Login
              </button>
              <button className="px-6 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg hover:shadow-lg transition">
                Register
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-5xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
            Hybrid Cross-Modal Fashion Discovery
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 mb-8">
            Search with text, images, or both. Our AI-powered CLIP model understands your style.
          </p>
          
          {/* Hybrid Search Bar */}
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-6 mb-12">
            <div className="flex flex-col md:flex-row gap-4 mb-4">
              <div className="flex-1">
                <input
                  type="text"
                  placeholder="Describe what you're looking for (e.g., red floral party dress)"
                  className="w-full px-6 py-4 rounded-xl border-2 border-gray-200 dark:border-gray-700 focus:border-indigo-500 focus:outline-none text-lg"
                />
              </div>
              <button className="px-6 py-4 bg-indigo-100 dark:bg-indigo-900 text-indigo-600 dark:text-indigo-300 rounded-xl hover:bg-indigo-200 transition flex items-center justify-center gap-2">
                <Upload className="w-5 h-5" />
                <span>Upload Image</span>
              </button>
            </div>
            <Link href="/search">
              <button className="w-full px-8 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:shadow-lg transition text-lg font-semibold flex items-center justify-center gap-2">
                <Search className="w-5 h-5" />
                Search Now
              </button>
            </Link>
          </div>

          {/* Features */}
          <div className="grid md:grid-cols-3 gap-6 mt-16">
            <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-lg">
              <Zap className="w-12 h-12 text-indigo-600 mx-auto mb-4" />
              <h3 className="text-xl font-bold mb-2">Instant Search</h3>
              <p className="text-gray-600 dark:text-gray-400">
                Lightning-fast CLIP-based similarity matching
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-lg">
              <Sparkles className="w-12 h-12 text-purple-600 mx-auto mb-4" />
              <h3 className="text-xl font-bold mb-2">Hybrid Fusion</h3>
              <p className="text-gray-600 dark:text-gray-400">
                Combine text + image with adjustable weights
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-lg">
              <TrendingUp className="w-12 h-12 text-pink-600 mx-auto mb-4" />
              <h3 className="text-xl font-bold mb-2">Smart Rankings</h3>
              <p className="text-gray-600 dark:text-gray-400">
                AI-powered relevance scoring and reranking
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Featured Recommendations */}
      <section className="container mx-auto px-4 py-16">
        <h2 className="text-3xl font-bold text-center mb-12">Featured Collections</h2>
        <div className="grid md:grid-cols-3 gap-8">
          <div className="group cursor-pointer">
            <div className="aspect-square bg-gradient-to-br from-rose-200 to-pink-300 rounded-2xl mb-4 overflow-hidden">
              <div className="w-full h-full flex items-center justify-center group-hover:scale-110 transition">
                <Heart className="w-16 h-16 text-white" />
              </div>
            </div>
            <h3 className="text-xl font-bold">Trending Now</h3>
            <p className="text-gray-600">Most popular items this week</p>
          </div>
          <div className="group cursor-pointer">
            <div className="aspect-square bg-gradient-to-br from-indigo-200 to-purple-300 rounded-2xl mb-4 overflow-hidden">
              <div className="w-full h-full flex items-center justify-center group-hover:scale-110 transition">
                <Shield className="w-16 h-16 text-white" />
              </div>
            </div>
            <h3 className="text-xl font-bold">Occasion-Based</h3>
            <p className="text-gray-600">Perfect for every event</p>
          </div>
          <div className="group cursor-pointer">
            <div className="aspect-square bg-gradient-to-br from-emerald-200 to-teal-300 rounded-2xl mb-4 overflow-hidden">
              <div className="w-full h-full flex items-center justify-center group-hover:scale-110 transition">
                <Sparkles className="w-16 h-16 text-white" />
              </div>
            </div>
            <h3 className="text-xl font-bold">Seasonal Picks</h3>
            <p className="text-gray-600">Curated for this season</p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-100 dark:bg-gray-900 mt-20 py-12">
        <div className="container mx-auto px-4 text-center text-gray-600 dark:text-gray-400">
          <p>© 2026 Cross-Modal Fashion Recommendation System</p>
          <p className="mt-2 text-sm">Powered by CLIP + FAISS | Hybrid AI Search</p>
        </div>
      </footer>
    </div>
  );
}
