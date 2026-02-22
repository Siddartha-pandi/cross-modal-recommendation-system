'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Button } from './ui/button';
import { Search, Upload, X, Sparkles, Loader2, Image as ImageIcon, TrendingUp, Star, ShoppingCart, Zap } from 'lucide-react';
import ProductDetail from './ProductDetail';
import TryOn3DViewer from './TryOn3DViewer';
import ARTryOn from './ARTryOn';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

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
  // Advanced features
  sentiment?: {
    aesthetic_score: number;
    emotion_category: string;
    color_harmony: number;
    brightness_score: number;
    warmth_score: number;
  };
  occasion?: {
    occasion_score: number;
    matched_occasion?: string;
    matched_mood?: string;
    boost_applied: number;
  };
}

interface SearchMeta {
  num_candidates: number;
  num_valid?: number;
  num_returned: number;
  query_time: number;
  fetch_time?: number;
  download_time?: number;
  encoding_time?: number;
  ranking_time?: number;
  weights?: {
    image: number;
    text: number;
  };
}

export default function EnhancedSearchInterface() {
  const [textQuery, setTextQuery] = useState('');
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const imageWeight = 0.6;
  const [results, setResults] = useState<Product[]>([]);
  const [meta, setMeta] = useState<SearchMeta | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [view, setView] = useState<'search' | 'detail' | '3d' | 'ar'>('search');
  const [selectedSources, setSelectedSources] = useState<string[]>([]);

  // Advanced features state
  const [occasion, setOccasion] = useState<string>('');
  const [mood, setMood] = useState<string>('');
  const [season, setSeason] = useState<string>('');
  const [timeOfDay, setTimeOfDay] = useState<string>('');
  const [enableSentiment, setEnableSentiment] = useState(false);
  const [enableOccasion, setEnableOccasion] = useState(false);

  const sources = ['amazon', 'flipkart', 'myntra', 'ikea', 'meesho'];
  
  // Occasion options (14 occasions from backend)
  const occasions = [
    'wedding', 'party', 'business', 'casual', 'beach', 'gym', 
    'outdoor', 'travel', 'home', 'office', 'date', 'festival', 'sports', 'formal'
  ];
  
  // Mood options (10 moods from backend)
  const moods = [
    'elegant', 'confident', 'relaxed', 'vibrant', 'professional', 
    'playful', 'minimalist', 'bold', 'sophisticated', 'comfortable'
  ];
  
  // Season options
  const seasons = ['spring', 'summer', 'fall', 'winter'];
  
  // Time of day options
  const timesOfDay = ['morning', 'afternoon', 'evening', 'night'];

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file) {
      setImageFile(file);
      const reader = new FileReader();
      reader.onload = () => {
        setImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.webp']
    },
    multiple: false
  });

  const removeImage = () => {
    setImageFile(null);
    setImagePreview(null);
  };

  const handleSearch = async () => {
    if (!textQuery && !imageFile) {
      setError('Please provide either text or image');
      return;
    }

    setLoading(true);
    setError(null);
    setResults([]);
    setMeta(null);

    try {
      let imageBase64 = null;
      if (imageFile) {
        const reader = new FileReader();
        imageBase64 = await new Promise<string>((resolve, reject) => {
          reader.onload = () => {
            const base64 = (reader.result as string).split(',')[1];
            resolve(base64);
          };
          reader.onerror = reject;
          reader.readAsDataURL(imageFile);
        });
      }

      const requestBody = {
        text: textQuery || null,
        image: imageBase64,
        priority: {
          image: imageWeight,
          text: 1 - imageWeight
        },
        top_k: 20,
        sources: selectedSources.length > 0 ? selectedSources : null,
        // Advanced features
        occasion: enableOccasion && occasion ? occasion : null,
        mood: enableOccasion && mood ? mood : null,
        season: enableOccasion && season ? season : null,
        time_of_day: enableOccasion && timeOfDay ? timeOfDay : null,
        enable_sentiment_scoring: enableSentiment,
        enable_occasion_ranking: enableOccasion
      };

      const response = await fetch(`${API_BASE_URL}/search/enhanced`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`Search failed: ${response.statusText}`);
      }

      const data = await response.json();
      setResults(data.results || []);
      setMeta(data.meta || null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleSource = (source: string) => {
    setSelectedSources(prev =>
      prev.includes(source)
        ? prev.filter(s => s !== source)
        : [...prev, source]
    );
  };

  if (view === 'detail' && selectedProduct) {
    return (
      <ProductDetail
        product={selectedProduct}
        onClose={() => {
          setView('search');
          setSelectedProduct(null);
        }}
        onTryOn3D={(product) => {
          setSelectedProduct(product);
          setView('3d');
        }}
        onTryOnAR={(product) => {
          setSelectedProduct(product);
          setView('ar');
        }}
      />
    );
  }

  if (view === '3d' && selectedProduct) {
    return (
      <div className="fixed inset-0 bg-white z-50">
        <div className="h-full flex flex-col">
          <div className="p-4 bg-white border-b flex items-center justify-between">
            <h2 className="text-xl font-bold">3D Try-On</h2>
            <Button variant="outline" onClick={() => setView('detail')}>
              Back to Details
            </Button>
          </div>
          <div className="flex-1">
            <TryOn3DViewer product={{...selectedProduct, id: selectedProduct.product_id}} />
          </div>
        </div>
      </div>
    );
  }

  if (view === 'ar' && selectedProduct) {
    return (
      <div className="fixed inset-0 bg-white z-50">
        <div className="h-full flex flex-col">
          <div className="p-4 bg-white border-b flex items-center justify-between">
            <h2 className="text-xl font-bold">AR Try-On</h2>
            <Button variant="outline" onClick={() => setView('detail')}>
              Back to Details
            </Button>
          </div>
          <div className="flex-1">
            <ARTryOn product={{...selectedProduct, id: selectedProduct.product_id}} />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-gray-50 to-blue-50">
      {/* Navigation Bar */}
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-40 backdrop-blur-md bg-white/95 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-20">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800 rounded-lg flex items-center justify-center shadow-md">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-gray-900 tracking-tight leading-tight">
                  Cross-Modal Product Recommendation System
                </h1>
                <p className="text-xs text-gray-500 font-medium">AI-Powered Multimodal Search Engine</p>
              </div>
            </div>
            <div className="flex items-center gap-6">
              <div className="hidden lg:flex items-center gap-2 px-4 py-2 bg-blue-50 rounded-lg border border-blue-100">
                <Zap className="w-4 h-4 text-blue-600" />
                <span className="text-sm font-semibold text-gray-700">CLIP Neural Network</span>
              </div>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {/* Search Section */}
        <div className="bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden mb-10">
          <div className="bg-gradient-to-r from-blue-600 to-indigo-700 px-8 py-6">
            <h2 className="text-2xl font-bold text-white mb-2">Intelligent Product Discovery</h2>
            <p className="text-blue-100">Search using natural language, images, or combine both for optimal results</p>
          </div>
          <div className="p-8">{/* Search Inputs Row */}
            <div className="grid md:grid-cols-2 gap-6 mb-6">
              {/* Text Search */}
              <div>
                <label className="flex items-center gap-2 text-sm font-semibold text-gray-800 mb-3">
                  <Search className="w-4 h-4 text-blue-600" />
                  Text-Based Query
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={textQuery}
                    onChange={(e) => setTextQuery(e.target.value)}
                    placeholder="e.g., red leather handbag, vintage watch, modern office chair..."
                    className="w-full px-4 py-3.5 pl-11 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all text-gray-900 placeholder:text-gray-400 font-medium"
                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  />
                  <Search className="absolute left-3.5 top-3.5 w-5 h-5 text-gray-400" />
                </div>
              </div>

              {/* Image Upload */}
              <div>
                <label className="flex items-center gap-2 text-sm font-semibold text-gray-800 mb-3">
                  <ImageIcon className="w-4 h-4 text-blue-600" />
                  Image-Based Query
                </label>
                {!imagePreview ? (
                  <div
                    {...getRootProps()}
                    className={`border-3 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all ${
                      isDragActive
                        ? 'border-blue-600 bg-blue-50 scale-[1.01] shadow-sm'
                        : 'border-gray-300 hover:border-blue-500 hover:bg-gray-50'
                    }`}
                  >
                    <input {...getInputProps()} />
                    <Upload className={`w-10 h-10 mx-auto mb-3 ${isDragActive ? 'text-blue-600' : 'text-gray-400'}`} />
                    <p className="text-sm text-gray-700 font-semibold mb-1">
                      {isDragActive ? 'Release to upload' : 'Drag & drop or click to browse'}
                    </p>
                    <p className="text-xs text-gray-500">Supports: PNG, JPG, JPEG, WebP (Max 10MB)</p>
                  </div>
                ) : (
                  <div className="relative group">
                    <img
                      src={imagePreview}
                      alt="Upload"
                      className="w-full h-36 object-cover rounded-lg border-2 border-gray-300 shadow-sm"
                    />
                    <button
                      onClick={removeImage}
                      className="absolute top-3 right-3 bg-red-600 hover:bg-red-700 text-white p-2.5 rounded-lg transition-all shadow-lg"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* AI-Powered Advanced Features */}
            <div className="mb-6 bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl p-6 border-2 border-indigo-200">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-lg flex items-center justify-center">
                    <Sparkles className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-gray-900">AI-Powered Context Filters</h3>
                    <p className="text-xs text-gray-600">Enhance results with occasion, mood, and sentiment analysis</p>
                  </div>
                </div>
              </div>

              {/* Feature Toggles */}
              <div className="grid md:grid-cols-2 gap-4 mb-5">
                <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-indigo-100 shadow-sm">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${enableSentiment ? 'bg-green-100' : 'bg-gray-100'}`}>
                      <TrendingUp className={`w-5 h-5 ${enableSentiment ? 'text-green-600' : 'text-gray-400'}`} />
                    </div>
                    <div>
                      <p className="text-sm font-bold text-gray-900">Visual Sentiment Analysis</p>
                      <p className="text-xs text-gray-500">Analyze product aesthetics and emotions</p>
                    </div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={enableSentiment}
                      onChange={(e) => setEnableSentiment(e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-14 h-7 bg-gray-300 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[4px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-indigo-100 shadow-sm">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${enableOccasion ? 'bg-purple-100' : 'bg-gray-100'}`}>
                      <Star className={`w-5 h-5 ${enableOccasion ? 'text-purple-600' : 'text-gray-400'}`} />
                    </div>
                    <div>
                      <p className="text-sm font-bold text-gray-900">Occasion & Mood Ranking</p>
                      <p className="text-xs text-gray-500">Match products to specific contexts</p>
                    </div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={enableOccasion}
                      onChange={(e) => setEnableOccasion(e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-14 h-7 bg-gray-300 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[4px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-purple-600"></div>
                  </label>
                </div>
              </div>

              {/* Context Options - Only show when Occasion/Mood is enabled */}
              {enableOccasion && (
                <div className="grid md:grid-cols-2 gap-4 pt-4 border-t border-indigo-200">
                  {/* Occasion Selector */}
                  <div>
                    <label className="block text-sm font-bold text-gray-800 mb-2">
                      Occasion
                    </label>
                    <select
                      value={occasion}
                      onChange={(e) => setOccasion(e.target.value)}
                      className="w-full px-4 py-2.5 border-2 border-indigo-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 bg-white text-gray-900 font-medium"
                    >
                      <option value="">Any Occasion</option>
                      {occasions.map(occ => (
                        <option key={occ} value={occ}>
                          {occ.charAt(0).toUpperCase() + occ.slice(1)}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Mood Selector */}
                  <div>
                    <label className="block text-sm font-bold text-gray-800 mb-2">
                      Mood
                    </label>
                    <select
                      value={mood}
                      onChange={(e) => setMood(e.target.value)}
                      className="w-full px-4 py-2.5 border-2 border-indigo-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 bg-white text-gray-900 font-medium"
                    >
                      <option value="">Any Mood</option>
                      {moods.map(m => (
                        <option key={m} value={m}>
                          {m.charAt(0).toUpperCase() + m.slice(1)}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Season Selector */}
                  <div>
                    <label className="block text-sm font-bold text-gray-800 mb-2">
                      Season
                    </label>
                    <select
                      value={season}
                      onChange={(e) => setSeason(e.target.value)}
                      className="w-full px-4 py-2.5 border-2 border-indigo-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 bg-white text-gray-900 font-medium"
                    >
                      <option value="">Any Season</option>
                      {seasons.map(s => (
                        <option key={s} value={s}>
                          {s.charAt(0).toUpperCase() + s.slice(1)}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Time of Day Selector */}
                  <div>
                    <label className="block text-sm font-bold text-gray-800 mb-2">
                      Time of Day
                    </label>
                    <select
                      value={timeOfDay}
                      onChange={(e) => setTimeOfDay(e.target.value)}
                      className="w-full px-4 py-2.5 border-2 border-indigo-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 bg-white text-gray-900 font-medium"
                    >
                      <option value="">Any Time</option>
                      {timesOfDay.map(t => (
                        <option key={t} value={t}>
                          {t.charAt(0).toUpperCase() + t.slice(1)}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              )}
            </div>

            {/* Source Filters */}
            <div className="mb-6">
              <label className="flex items-center gap-2 text-sm font-bold text-gray-800 mb-3">
                <ShoppingCart className="w-4 h-4 text-blue-600" />
                E-Commerce Data Sources
              </label>
              <div className="flex flex-wrap gap-2.5">
                {sources.map((source) => {
                  const isActive = selectedSources.includes(source) || selectedSources.length === 0;
                  return (
                    <button
                      key={source}
                      onClick={() => toggleSource(source)}
                      className={`px-5 py-2.5 rounded-lg text-sm font-semibold transition-all shadow-sm ${
                        isActive
                          ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md hover:shadow-lg transform hover:-translate-y-0.5'
                          : 'bg-white text-gray-700 hover:bg-gray-50 border-2 border-gray-300'
                      }`}
                    >
                      {source.charAt(0).toUpperCase() + source.slice(1)}
                    </button>
                  );
                })}
              </div>
              <p className="text-xs text-gray-600 mt-3 font-medium">
                {selectedSources.length === 0 
                  ? 'All sources active • Real-time data aggregation' 
                  : `${selectedSources.length} of ${sources.length} sources selected`}
              </p>
            </div>

            {/* Advanced Features Section */}
            <div className="mb-6 border-t-2 border-gray-200 pt-6">
              <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg p-6 border-2 border-purple-200">
                <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-purple-600" />
                  AI-Powered Advanced Features
                </h3>
                
                {/* Feature Toggles */}
                <div className="grid md:grid-cols-2 gap-4 mb-4">
                  <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-purple-200">
                    <div>
                      <label className="text-sm font-bold text-gray-800 block">Visual Sentiment Analysis</label>
                      <p className="text-xs text-gray-600 mt-1">Score products by aesthetic appeal & emotion</p>
                    </div>
                    <button
                      onClick={() => setEnableSentiment(!enableSentiment)}
                      className={`relative w-14 h-7 rounded-full transition-colors ${
                        enableSentiment ? 'bg-purple-600' : 'bg-gray-300'
                      }`}
                    >
                      <div
                        className={`absolute top-1 w-5 h-5 bg-white rounded-full transition-transform ${
                          enableSentiment ? 'translate-x-8' : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </div>
                  
                  <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-purple-200">
                    <div>
                      <label className="text-sm font-bold text-gray-800 block">Occasion & Mood Ranking</label>
                      <p className="text-xs text-gray-600 mt-1">Personalize results for specific contexts</p>
                    </div>
                    <button
                      onClick={() => setEnableOccasion(!enableOccasion)}
                      className={`relative w-14 h-7 rounded-full transition-colors ${
                        enableOccasion ? 'bg-purple-600' : 'bg-gray-300'
                      }`}
                    >
                      <div
                        className={`absolute top-1 w-5 h-5 bg-white rounded-full transition-transform ${
                          enableOccasion ? 'translate-x-8' : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </div>
                </div>

                {/* Occasion/Mood Controls - Only show when enabled */}
                {enableOccasion && (
                  <div className="bg-white rounded-lg p-5 border border-purple-200">
                    <div className="grid md:grid-cols-2 gap-4 mb-4">
                      {/* Occasion Selector */}
                      <div>
                        <label className="text-sm font-semibold text-gray-800 mb-2 block">
                          Occasion
                        </label>
                        <select
                          value={occasion}
                          onChange={(e) => setOccasion(e.target.value)}
                          className="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all text-gray-900 font-medium"
                        >
                          <option value="">Any Occasion</option>
                          {occasions.map((occ) => (
                            <option key={occ} value={occ}>
                              {occ.charAt(0).toUpperCase() + occ.slice(1)}
                            </option>
                          ))}
                        </select>
                      </div>

                      {/* Mood Selector */}
                      <div>
                        <label className="text-sm font-semibold text-gray-800 mb-2 block">
                          Mood
                        </label>
                        <select
                          value={mood}
                          onChange={(e) => setMood(e.target.value)}
                          className="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all text-gray-900 font-medium"
                        >
                          <option value="">Any Mood</option>
                          {moods.map((m) => (
                            <option key={m} value={m}>
                              {m.charAt(0).toUpperCase() + m.slice(1)}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>

                    <div className="grid md:grid-cols-2 gap-4">
                      {/* Season Selector */}
                      <div>
                        <label className="text-sm font-semibold text-gray-800 mb-2 block">
                          Season
                        </label>
                        <select
                          value={season}
                          onChange={(e) => setSeason(e.target.value)}
                          className="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all text-gray-900 font-medium"
                        >
                          <option value="">Any Season</option>
                          {seasons.map((s) => (
                            <option key={s} value={s}>
                              {s.charAt(0).toUpperCase() + s.slice(1)}
                            </option>
                          ))}
                        </select>
                      </div>

                      {/* Time of Day Selector */}
                      <div>
                        <label className="text-sm font-semibold text-gray-800 mb-2 block">
                          Time of Day
                        </label>
                        <select
                          value={timeOfDay}
                          onChange={(e) => setTimeOfDay(e.target.value)}
                          className="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all text-gray-900 font-medium"
                        >
                          <option value="">Any Time</option>
                          {timesOfDay.map((t) => (
                            <option key={t} value={t}>
                              {t.charAt(0).toUpperCase() + t.slice(1)}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Action Button */}
            <Button
              onClick={handleSearch}
              disabled={loading || (!textQuery && !imageFile)}
              className="w-full bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700 hover:from-blue-700 hover:via-blue-800 hover:to-indigo-800 text-white font-bold py-5 rounded-lg shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed text-lg"
            >
              {loading ? (
                <div className="flex items-center justify-center gap-3">
                  <Loader2 className="w-6 h-6 animate-spin" />
                  <span>Processing Neural Network Analysis...</span>
                </div>
              ) : (
                <div className="flex items-center justify-center gap-3">
                  <Search className="w-6 h-6" />
                  <span>Execute Cross-Modal Search</span>
                </div>
              )}
            </Button>

            {/* Status Messages */}
            {error && (
              <div className="mt-5 p-5 bg-red-50 border-l-4 border-red-600 rounded-lg shadow-sm">
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-red-600 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <X className="w-4 h-4 text-white" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-red-900 mb-1">Error</p>
                    <p className="text-sm text-red-800">{error}</p>
                  </div>
                </div>
              </div>
            )}

            {meta && (
              <div className="mt-5 p-5 bg-gradient-to-br from-green-50 to-emerald-50 border-l-4 border-green-600 rounded-lg shadow-sm">
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-green-600 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <TrendingUp className="w-4 h-4 text-white" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-bold text-green-900 mb-2">Search Complete</p>
                    <div className="grid grid-cols-3 gap-4 text-xs">
                      <div>
                        <p className="text-green-700 font-semibold">Products Found</p>
                        <p className="text-2xl font-bold text-green-900">{meta.num_returned}</p>
                      </div>
                      <div>
                        <p className="text-green-700 font-semibold">Total Analyzed</p>
                        <p className="text-2xl font-bold text-green-900">{meta.num_candidates}</p>
                      </div>
                      <div>
                        <p className="text-green-700 font-semibold">Processing Time</p>
                        <p className="text-2xl font-bold text-green-900">{meta.query_time.toFixed(2)}s</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Results Grid */}
        {results.length > 0 && (
          <div>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-3xl font-bold text-gray-900 mb-1">
                    {results.length} Products Discovered
                  </h2>
                  <p className="text-gray-600 font-medium">Ranked by cross-modal similarity score • Click for details</p>
                </div>
                <div className="hidden md:flex items-center gap-2 px-4 py-2 bg-blue-50 rounded-lg border border-blue-100">
                  <Star className="w-5 h-5 text-blue-600" />
                  <span className="text-sm font-semibold text-gray-700">AI-Sorted Results</span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {results.map((product) => (
                <div
                  key={product.product_id}
                  onClick={() => {
                    setSelectedProduct(product);
                    setView('detail');
                  }}
                  className="group bg-white rounded-xl shadow-md border-2 border-gray-200 overflow-hidden cursor-pointer transition-all hover:shadow-xl hover:-translate-y-1 hover:border-blue-400"
                >
                  {/* Product Image */}
                  <div className="relative aspect-square bg-gray-100 overflow-hidden">
                    <img
                      src={product.image_url}
                      alt={product.title}
                      className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                    />
                    
                    {/* Match Score Badge */}
                    {product.score && (
                      <div className="absolute top-3 right-3 bg-gradient-to-br from-blue-600 to-indigo-700 text-white text-xs font-bold px-3 py-1.5 rounded-full shadow-lg border-2 border-white">
                        {Math.round(product.score * 100)}% Match
                      </div>
                    )}
                    
                    {/* Sentiment Badge - Show when sentiment analysis is enabled */}
                    {enableSentiment && product.sentiment && (
                      <div className="absolute top-3 left-3 bg-gradient-to-br from-purple-600 to-pink-600 text-white text-xs font-bold px-3 py-1.5 rounded-full shadow-lg border-2 border-white flex items-center gap-1">
                        <Sparkles className="w-3 h-3" />
                        {Math.round(product.sentiment.aesthetic_score * 100)}% {product.sentiment.emotion_category}
                      </div>
                    )}
                    
                    {/* Occasion Badge - Show when occasion ranking is enabled */}
                    {enableOccasion && product.occasion && product.occasion.boost_applied > 1.0 && (
                      <div className="absolute top-14 left-3 bg-gradient-to-br from-amber-500 to-orange-600 text-white text-xs font-bold px-3 py-1.5 rounded-full shadow-lg border-2 border-white">
                        {product.occasion.matched_occasion && `${product.occasion.matched_occasion.charAt(0).toUpperCase() + product.occasion.matched_occasion.slice(1)}`}
                        {product.occasion.boost_applied > 1.0 && ` +${Math.round((product.occasion.boost_applied - 1) * 100)}%`}
                      </div>
                    )}
                    
                    {/* Source Badge */}
                    <div className="absolute bottom-3 left-3 bg-gray-900/90 backdrop-blur-sm text-white text-xs font-bold px-3 py-1.5 rounded-full border border-white/20">
                      {product.source}
                    </div>
                  </div>

                  {/* Product Info */}
                  <div className="p-5">
                    <h3 className="font-bold text-gray-900 mb-2 line-clamp-2 text-base group-hover:text-blue-700 transition-colors min-h-[3rem]">
                      {product.title}
                    </h3>
                    
                    <div className="flex items-center justify-between mb-3 pt-2 border-t border-gray-100">
                      <span className="text-2xl font-bold text-gray-900">
                        ₹{product.price.toFixed(2)}
                      </span>
                      {product.rating && (
                        <div className="flex items-center gap-1.5 bg-amber-50 px-2 py-1 rounded-lg">
                          <Star className="w-4 h-4 fill-amber-400 text-amber-400" />
                          <span className="text-sm font-bold text-gray-800">{product.rating.toFixed(1)}</span>
                        </div>
                      )}
                    </div>

                    {/* Match Tags */}
                    {product.match_tags && product.match_tags.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 pt-2 border-t border-gray-100">
                        {product.match_tags.slice(0, 2).map((tag, idx) => (
                          <span
                            key={idx}
                            className="text-xs px-2.5 py-1 bg-gradient-to-r from-blue-50 to-indigo-50 text-blue-700 rounded-md font-semibold border border-blue-200"
                          >
                            {tag.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Sentiment Details - Show when sentiment is enabled */}
                    {enableSentiment && product.sentiment && (
                      <div className="mt-3 pt-3 border-t border-purple-100 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg p-2.5">
                        <div className="text-xs font-semibold text-purple-900 mb-1.5 flex items-center gap-1">
                          <Sparkles className="w-3 h-3" />
                          Visual Sentiment Analysis
                        </div>
                        <div className="grid grid-cols-2 gap-1.5 text-xs">
                          <div className="flex justify-between">
                            <span className="text-purple-700">Color Harmony:</span>
                            <span className="font-bold text-purple-900">{Math.round(product.sentiment.color_harmony * 100)}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-purple-700">Brightness:</span>
                            <span className="font-bold text-purple-900">{Math.round(product.sentiment.brightness_score * 100)}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-purple-700">Warmth:</span>
                            <span className="font-bold text-purple-900">{Math.round(product.sentiment.warmth_score * 100)}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-purple-700">Aesthetic:</span>
                            <span className="font-bold text-purple-900">{Math.round(product.sentiment.aesthetic_score * 100)}%</span>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Occasion Details - Show when occasion ranking is enabled */}
                    {enableOccasion && product.occasion && (
                      <div className="mt-3 pt-3 border-t border-amber-100 bg-gradient-to-r from-amber-50 to-orange-50 rounded-lg p-2.5">
                        <div className="text-xs font-semibold text-amber-900 mb-1.5">
                          Occasion Match Analysis
                        </div>
                        <div className="space-y-1 text-xs">
                          {product.occasion.matched_occasion && (
                            <div className="flex justify-between">
                              <span className="text-amber-700">Best For:</span>
                              <span className="font-bold text-amber-900 capitalize">{product.occasion.matched_occasion}</span>
                            </div>
                          )}
                          {product.occasion.matched_mood && (
                            <div className="flex justify-between">
                              <span className="text-amber-700">Mood:</span>
                              <span className="font-bold text-amber-900 capitalize">{product.occasion.matched_mood}</span>
                            </div>
                          )}
                          <div className="flex justify-between">
                            <span className="text-amber-700">Match Score:</span>
                            <span className="font-bold text-amber-900">{Math.round(product.occasion.occasion_score * 100)}%</span>
                          </div>
                          {product.occasion.boost_applied > 1.0 && (
                            <div className="flex justify-between bg-amber-100 -mx-2.5 -mb-2.5 px-2.5 py-1.5 mt-1.5 rounded-b-lg">
                              <span className="text-amber-800 font-semibold">Relevance Boost:</span>
                              <span className="font-bold text-amber-900">+{Math.round((product.occasion.boost_applied - 1) * 100)}%</span>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {!loading && results.length === 0 && !meta && (
          <div className="bg-white rounded-xl shadow-md border border-gray-200 text-center py-20 px-6">
            <div className="inline-flex items-center justify-center w-24 h-24 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-full mb-6 border-4 border-blue-100">
              <ImageIcon className="w-12 h-12 text-blue-600" />
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-3">System Ready for Analysis</h3>
            <p className="text-gray-600 max-w-lg mx-auto text-lg leading-relaxed mb-6">
              Upload a product image or enter a text description to initiate cross-modal similarity search across multiple e-commerce platforms
            </p>
            <div className="flex items-center justify-center gap-8 text-sm text-gray-500">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="font-medium">CLIP Model Active</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="font-medium">5 Data Sources Online</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

