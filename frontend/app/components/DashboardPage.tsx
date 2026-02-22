'use client';

import React, { useState } from 'react';
import { Heart, Clock, Settings, TrendingUp, Sparkles, LogOut, Eye, Trash2 } from 'lucide-react';

interface SavedItem {
  id: string;
  title: string;
  price: number;
  image_url: string;
  saved_date: string;
}

interface SearchHistory {
  id: string;
  query: string;
  query_type: 'text' | 'image' | 'hybrid';
  timestamp: string;
  results_count: number;
}

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<'saved' | 'history' | 'preferences'>('saved');

  const savedItems: SavedItem[] = [
    {
      id: '1',
      title: 'Elegant Red Evening Dress',
      price: 2999,
      image_url: '/dress1.jpg',
      saved_date: '2026-02-20'
    },
    {
      id: '2',
      title: 'Black Leather Boots',
      price: 4599,
      image_url: '/boots1.jpg',
      saved_date: '2026-02-19'
    },
    {
      id: '3',
      title: 'Designer Handbag',
      price: 8999,
      image_url: '/bag1.jpg',
      saved_date: '2026-02-18'
    }
  ];

  const searchHistory: SearchHistory[] = [
    {
      id: '1',
      query: 'red floral party dress',
      query_type: 'text',
      timestamp: '2026-02-21 10:30',
      results_count: 24
    },
    {
      id: '2',
      query: 'Image: dress_001.jpg',
      query_type: 'image',
      timestamp: '2026-02-20 15:45',
      results_count: 18
    },
    {
      id: '3',
      query: 'elegant evening wear + Image',
      query_type: 'hybrid',
      timestamp: '2026-02-20 14:20',
      results_count: 32
    }
  ];

  const getQueryTypeBadge = (type: string) => {
    const badges = {
      text: { color: 'bg-purple-100 text-purple-700', label: '🟣 Text' },
      image: { color: 'bg-blue-100 text-blue-700', label: '🔵 Image' },
      hybrid: { color: 'bg-green-100 text-green-700', label: '🟢 Hybrid' }
    };
    const badge = badges[type as keyof typeof badges];
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${badge.color}`}>
        {badge.label}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="w-6 h-6 text-indigo-600" />
              <h1 className="text-lg font-bold">Cross-Modal Fashion Recommendation</h1>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className="w-10 h-10 bg-indigo-600 rounded-full flex items-center justify-center text-white font-bold">
                  JD
                </div>
                <div className="hidden md:block">
                  <p className="font-semibold text-sm">John Doe</p>
                  <p className="text-xs text-gray-500">john@example.com</p>
                </div>
              </div>
              <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition">
                <LogOut className="w-5 h-5 text-gray-600" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          {/* Welcome Banner */}
          <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl p-8 text-white mb-8">
            <h2 className="text-3xl font-bold mb-2">Welcome Back, John! 👋</h2>
            <p className="text-indigo-100">Your personalized fashion dashboard powered by AI</p>
          </div>

          {/* Tabs */}
          <div className="flex gap-2 mb-6 bg-white dark:bg-gray-800 p-2 rounded-xl shadow">
            <button
              onClick={() => setActiveTab('saved')}
              className={`flex-1 px-6 py-3 rounded-lg font-semibold transition flex items-center justify-center gap-2 ${
                activeTab === 'saved'
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <Heart className="w-5 h-5" />
              Saved Items
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`flex-1 px-6 py-3 rounded-lg font-semibold transition flex items-center justify-center gap-2 ${
                activeTab === 'history'
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <Clock className="w-5 h-5" />
              Search History
            </button>
            <button
              onClick={() => setActiveTab('preferences')}
              className={`flex-1 px-6 py-3 rounded-lg font-semibold transition flex items-center justify-center gap-2 ${
                activeTab === 'preferences'
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <Settings className="w-5 h-5" />
              Preferences
            </button>
          </div>

          {/* Content */}
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
            {/* Saved Items Tab */}
            {activeTab === 'saved' && (
              <div>
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-2xl font-bold">Your Saved Items</h3>
                  <span className="text-sm text-gray-600">{savedItems.length} items</span>
                </div>
                <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-6">
                  {savedItems.map((item) => (
                    <div key={item.id} className="group relative">
                      <div className="aspect-square bg-gray-100 dark:bg-gray-700 rounded-xl overflow-hidden mb-3">
                        <img
                          src={item.image_url || '/placeholder.png'}
                          alt={item.title}
                          className="w-full h-full object-cover group-hover:scale-110 transition"
                        />
                      </div>
                      <h4 className="font-semibold line-clamp-2 mb-2">{item.title}</h4>
                      <div className="flex items-center justify-between">
                        <span className="text-lg font-bold text-indigo-600">₹{item.price}</span>
                        <div className="flex gap-2">
                          <button className="p-2 bg-indigo-100 text-indigo-600 rounded-lg hover:bg-indigo-200 transition">
                            <Eye className="w-4 h-4" />
                          </button>
                          <button className="p-2 bg-red-100 text-red-600 rounded-lg hover:bg-red-200 transition">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                      <p className="text-xs text-gray-500 mt-2">Saved on {item.saved_date}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Search History Tab */}
            {activeTab === 'history' && (
              <div>
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-2xl font-bold">Search History</h3>
                  <button className="text-sm text-red-600 hover:text-red-700 font-semibold">
                    Clear All
                  </button>
                </div>
                <div className="space-y-4">
                  {searchHistory.map((search) => (
                    <div
                      key={search.id}
                      className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-xl hover:shadow-md transition"
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          {getQueryTypeBadge(search.query_type)}
                          <span className="font-semibold">{search.query}</span>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-gray-600">
                          <span className="flex items-center gap-1">
                            <Clock className="w-4 h-4" />
                            {search.timestamp}
                          </span>
                          <span className="flex items-center gap-1">
                            <TrendingUp className="w-4 h-4" />
                            {search.results_count} results
                          </span>
                        </div>
                      </div>
                      <button className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition text-sm">
                        Search Again
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Preferences Tab */}
            {activeTab === 'preferences' && (
              <div>
                <h3 className="text-2xl font-bold mb-6">Search Preferences</h3>
                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-semibold mb-2">
                      Default Search Mode
                    </label>
                    <select className="w-full px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-indigo-500 focus:outline-none">
                      <option value="hybrid">Hybrid (Text + Image)</option>
                      <option value="text">Text Only</option>
                      <option value="image">Image Only</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold mb-2">
                      Default Fusion Weight (Text vs Image)
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      defaultValue="0.5"
                      className="w-full h-2 rounded-lg appearance-none cursor-pointer"
                    />
                    <div className="flex justify-between text-xs mt-1">
                      <span>Only Image</span>
                      <span>Balanced</span>
                      <span>Only Text</span>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold mb-2">
                      Preferred Categories
                    </label>
                    <div className="grid grid-cols-2 gap-3">
                      {["Women's Clothing", "Men's Clothing", "Shoes", "Accessories", "Bags", "Jewelry"].map((cat) => (
                        <label key={cat} className="flex items-center gap-2 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg cursor-pointer hover:bg-gray-100">
                          <input type="checkbox" className="w-4 h-4 text-indigo-600" />
                          <span className="text-sm">{cat}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold mb-2">
                      Price Range (₹)
                    </label>
                    <div className="grid grid-cols-2 gap-4">
                      <input
                        type="number"
                        placeholder="Min"
                        className="px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-indigo-500 focus:outline-none"
                      />
                      <input
                        type="number"
                        placeholder="Max"
                        className="px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-indigo-500 focus:outline-none"
                      />
                    </div>
                  </div>

                  <button className="w-full px-6 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:shadow-lg transition text-lg font-semibold">
                    Save Preferences
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Personalized Recommendations */}
          <div className="bg-gradient-to-br from-purple-50 to-indigo-50 dark:from-purple-900/20 dark:to-indigo-900/20 rounded-2xl p-8 mt-8">
            <div className="flex items-center gap-2 mb-6">
              <Sparkles className="w-6 h-6 text-purple-600" />
              <h3 className="text-2xl font-bold">Personalized Recommendations</h3>
            </div>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Based on your search history and preferences, we've curated these items for you
            </p>
            <div className="grid sm:grid-cols-2 md:grid-cols-4 gap-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="aspect-square bg-gradient-to-br from-indigo-200 to-purple-200 rounded-xl"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
