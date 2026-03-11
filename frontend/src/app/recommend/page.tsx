'use client';

import { useState, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useCart } from '@/contexts/CartContext';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import UserMenu from '@/components/UserMenu';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api/v1';

// ── Types ────────────────────────────────────────────────────────────────────

interface RecommendedProduct {
    title: string;
    source: string;
    url: string;
    image_url: string;
    similarity_score: number;
    visual_score?: number;
    text_score?: number;
    price?: string;
    currency?: string;
    snippet?: string;
    rank: number;
}

interface RecommendResponse {
    results: RecommendedProduct[];
    total_results: number;
    query_time: number;
    search_phrase: string;
    alpha_used: number;
    search_type: string;
    total_candidates: number;
    model_used: string;
}

// ── Source badge colours ─────────────────────────────────────────────────────
const SOURCE_STYLES: Record<string, { bg: string; text: string; border: string }> = {
    Myntra: { bg: 'bg-pink-500/20', text: 'text-pink-300', border: 'border-pink-500/40' },
    Amazon: { bg: 'bg-orange-500/20', text: 'text-orange-300', border: 'border-orange-500/40' },
    Flipkart: { bg: 'bg-blue-500/20', text: 'text-blue-300', border: 'border-blue-500/40' },
    AJIO: { bg: 'bg-purple-500/20', text: 'text-purple-300', border: 'border-purple-500/40' },
    default: { bg: 'bg-slate-500/20', text: 'text-slate-300', border: 'border-slate-500/40' },
};

function SourceBadge({ source }: { source: string }) {
    const s = SOURCE_STYLES[source] || SOURCE_STYLES.default;
    return (
        <span className={`text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded border ${s.bg} ${s.text} ${s.border}`}>
            {source}
        </span>
    );
}


function formatPrice(price?: string, currency?: string) {
    if (!price) return null;

    // If it already has a currency symbol (₹, $, etc.), just return it
    if (/[₹$€£]/.test(price)) return price;

    // Otherwise, assume INR if it's just a number or if currency is INR
    const numericPart = price.replace(/[^\d.]/g, '');
    if (numericPart && !isNaN(parseFloat(numericPart))) {
        const symbol = (currency === 'USD' || price.includes('$')) ? '$' : '₹';
        return `${symbol}${parseFloat(numericPart).toLocaleString('en-IN')}`;
    }

    return price;
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function RecommendPage() {
    const [textQuery, setTextQuery] = useState('');
    const [imageFile, setImageFile] = useState<File | null>(null);
    const [imagePreview, setImagePreview] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [response, setResponse] = useState<RecommendResponse | null>(null);
    const [dragOver, setDragOver] = useState(false);
    const [cartLoading, setCartLoading] = useState<string | null>(null);
    const [addedItems, setAddedItems] = useState<Set<string>>(new Set());
    const { addToCart, itemCount } = useCart();
    const router = useRouter();
    const { user } = useAuth();
    const handleAddToCart = async (product: RecommendedProduct) => {
        try {
            setCartLoading(product.url);
            await addToCart({
                product_id: product.url,
                title: product.title,
                price: product.price ? parseFloat(product.price.replace(/[^\d.]/g, '')) : 0,
                quantity: 1,
                image_url: product.image_url,
            });
            setAddedItems(new Set([...addedItems, product.url]));
            setTimeout(() => {
                setAddedItems((prev) => {
                    const newSet = new Set(prev);
                    newSet.delete(product.url);
                    return newSet;
                });
            }, 2000);
        } catch (err) {
            // Optionally handle error
        } finally {
            setCartLoading(null);
        }
    };

    const handleBuyNow = async (product: RecommendedProduct) => {
        try {
            setCartLoading(product.url);
            await addToCart({
                product_id: product.url,
                title: product.title,
                price: product.price ? parseFloat(product.price.replace(/[^\d.]/g, '')) : 0,
                quantity: 1,
                image_url: product.image_url,
            });
            router.push('/cart');
        } catch (err) {
            // Optionally handle error
        } finally {
            setCartLoading(null);
        }
    };

    // ── Image handling ──────────────────────────────────────────────────────

    const handleImageSelect = useCallback((file: File) => {
        setImageFile(file);
        const reader = new FileReader();
        reader.onloadend = () => setImagePreview(reader.result as string);
        reader.readAsDataURL(file);
    }, []);

    const handleDrop = useCallback(
        (e: React.DragEvent) => {
            e.preventDefault();
            setDragOver(false);
            const file = e.dataTransfer.files?.[0];
            if (file && file.type.startsWith('image/')) handleImageSelect(file);
        },
        [handleImageSelect]
    );

    // ── Search ──────────────────────────────────────────────────────────────

    const handleSearch = async () => {
        if (!textQuery.trim() && !imageFile) {
            setError('Please provide a text query or upload a fashion image.');
            return;
        }

        setLoading(true);
        setError(null);
        setResponse(null);

        try {
            const formData = new FormData();
            if (textQuery.trim()) formData.append('text_query', textQuery.trim());
            if (imageFile) formData.append('image', imageFile);
            formData.append('top_k', '10');
            formData.append('alpha', '0.6');

            const res = await fetch(`${API_URL}/recommend`, {
                method: 'POST',
                body: formData,
            });

            if (!res.ok) {
                const err = await res.text();
                let msg = `Error ${res.status}`;
                try { msg = JSON.parse(err).detail || msg; } catch { msg = err || msg; }
                throw new Error(msg);
            }

            const data: RecommendResponse = await res.json();
            setResponse(data);
        } catch (err: any) {
            setError(err.message || 'Request failed. Check that the backend is running.');
        } finally {
            setLoading(false);
        }
    };

    // ── Render ───────────────────────────────────────────────────────────────

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-neutral-900 text-white">

            {/* ── Navigation ── */}
            <nav className="sticky top-0 z-50 bg-slate-900/80 backdrop-blur-md border-b border-slate-800">
                <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
                    <Link href="/" className="text-2xl font-bold text-white hover:text-blue-400">
                        Fashion Finder
                    </Link>
                    <div className="flex items-center gap-4">
                        {/* <span className="text-sm font-semibold text-violet-400 border border-violet-500/40 px-3 py-1 rounded-full bg-violet-500/10">
                            ✨ Live Recommend
                        </span> */}
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

            <div className="max-w-7xl mx-auto px-4 py-10">

                {/* ── Header ── */}
                <div className="mb-12">
                    <h1 className="text-5xl font-bold text-white mb-4">Fashion Discovery</h1>
                    <p className="text-gray-400 text-lg">
                        Search with text & images
                    </p>
                    {user && (
                        <p className="text-gray-300 mt-4">Welcome, {user.full_name}!</p>
                    )}
                </div>

                {/* ── Search Card ── */}
                <div className="bg-slate-800/40 backdrop-blur-sm rounded-2xl border border-slate-700/60 p-8 mb-8 shadow-2xl">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">

                        {/* Text Query */}
                        <div className="space-y-2">
                            <label className="block text-[10px] font-bold tracking-widest text-slate-400 uppercase">
                                Text Description
                            </label>
                            <textarea
                                value={textQuery}
                                onChange={(e) => setTextQuery(e.target.value)}
                                placeholder="e.g. blue denim jacket men casual, floral dress women summer..."
                                rows={4}
                                className="w-full px-4 py-3 bg-slate-900 border border-slate-600 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent resize-none transition"
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' && e.ctrlKey) handleSearch();
                                }}
                            />
                            <p className="text-[10px] text-slate-600">Ctrl + Enter to search</p>
                        </div>

                        {/* Image Upload */}
                        <div className="space-y-2">
                            <label className="block text-[10px] font-bold tracking-widest text-slate-400 uppercase">
                                Fashion Image
                            </label>
                            <div
                                className={`relative min-h-[120px] rounded-xl border-2 border-dashed transition-all ${dragOver
                                    ? 'border-violet-400 bg-violet-500/10'
                                    : imagePreview
                                        ? 'border-slate-600 bg-slate-900'
                                        : 'border-slate-600 bg-slate-900/50 hover:border-slate-500 hover:bg-slate-800/50'
                                    }`}
                                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                                onDragLeave={() => setDragOver(false)}
                                onDrop={handleDrop}
                            >
                                <input
                                    id="image-upload"
                                    type="file"
                                    accept="image/*"
                                    onChange={(e) => { const f = e.target.files?.[0]; if (f) handleImageSelect(f); }}
                                    className="hidden"
                                />
                                {imagePreview ? (
                                    <div className="flex items-start gap-4 p-4">
                                        <img
                                            src={imagePreview}
                                            alt="Query"
                                            className="w-20 h-20 object-cover rounded-lg border border-slate-600 flex-shrink-0"
                                        />
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm text-white font-medium truncate">{imageFile?.name}</p>
                                            <p className="text-xs text-slate-500 mt-1">Image selected</p>
                                            <button
                                                onClick={() => { setImageFile(null); setImagePreview(null); }}
                                                className="mt-3 text-xs text-red-400 hover:text-red-300 transition flex items-center gap-1"
                                            >
                                                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                                </svg>
                                                Remove
                                            </button>
                                        </div>
                                    </div>
                                ) : (
                                    <label htmlFor="image-upload" className="flex flex-col items-center justify-center h-[120px] cursor-pointer gap-3">
                                        <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center text-slate-500">
                                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                            </svg>
                                        </div>
                                        <span className="text-sm text-slate-400">Click or drag &amp; drop</span>
                                    </label>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Search Button */}
                    <button
                        onClick={handleSearch}
                        disabled={loading}
                        className="w-full py-4 rounded-xl font-bold text-base transition-all bg-gradient-to-r from-violet-600 to-pink-600 hover:from-violet-500 hover:to-pink-500 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-violet-500/25 flex items-center justify-center gap-3"
                    >
                        {loading ? (
                            <>
                                <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                </svg>
                                Searching ...
                            </>
                        ) : (
                            <>
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                </svg>
                                Find Fashion Products
                            </>
                        )}
                    </button>

                    {error && (
                        <div className="mt-4 bg-red-500/10 border border-red-500/40 text-red-300 px-4 py-3 rounded-xl text-sm">
                            {error}
                        </div>
                    )}
                </div>

                {/* ── Results Stats Bar ── */}
                {response && (
                    <div className="mb-6 flex flex-wrap gap-4 items-center">
                        <h2 className="text-2xl font-bold text-white">
                            {response.total_results > 0
                                ? `${response.total_results} Recommendations`
                                : 'No Results Found'}
                        </h2>
                        <div className="flex flex-wrap gap-2 ml-auto">
                            {response.search_phrase && (
                                <span className="text-xs bg-slate-800 border border-slate-700 text-slate-300 px-3 py-1 rounded-full">
                                    🔍 &quot;{response.search_phrase}&quot;
                                </span>
                            )}
                            <span className="text-xs bg-slate-800 border border-slate-700 text-slate-400 px-3 py-1 rounded-full">
                                {response.model_used} · {response.search_type}
                            </span>
                            <span className="text-xs bg-slate-800 border border-slate-700 text-slate-400 px-3 py-1 rounded-full">
                                ⏱ {response.query_time.toFixed(2)}s
                            </span>
                            <span className="text-xs bg-slate-800 border border-slate-700 text-slate-400 px-3 py-1 rounded-full">
                                {response.total_candidates} candidates scanned
                            </span>
                        </div>
                    </div>
                )}

                {/* ── No Results ── */}
                {response && response.total_results === 0 && (
                    <div className="flex flex-col items-center py-20">
                        <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-12 text-center max-w-md">
                            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-slate-700 flex items-center justify-center">
                                <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
                                </svg>
                            </div>
                            <h3 className="text-xl font-bold text-white mb-2">No products found</h3>
                            <p className="text-slate-400 text-sm">
                                Try a more descriptive query like &quot;blue denim jacket men casual&quot; or upload a clear product image.
                            </p>
                        </div>
                    </div>
                )}

                {/* ── Product Grid ── */}
                {response && response.total_results > 0 && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
                        {response.results.slice(0, 2).map((product) => (
                            <div
                                key={`${product.url}-${product.rank}`}
                                className="group bg-slate-800/40 backdrop-blur-sm rounded-2xl border border-slate-700/60 overflow-hidden hover:border-violet-500/60 hover:shadow-xl hover:shadow-violet-500/10 transition-all duration-300 flex flex-col"
                            >
                                {/* Rank badge + Image */}
                                <div className="relative overflow-hidden">
                                    <img
                                        src={product.image_url}
                                        alt={product.title}
                                        className="w-full h-52 object-cover group-hover:scale-105 transition-transform duration-500"
                                        onError={(e) => {
                                            (e.target as HTMLImageElement).src =
                                                'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwOCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwOCIgZmlsbD0iIzFlMjkzYiIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmaWxsPSIjNjQ3NDhiIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiPk5vIEltYWdlPC90ZXh0Pjwvc3ZnPg==';
                                        }}
                                    />
                                    {/* Rank pill */}
                                    <div className="absolute top-2 left-2 bg-black/70 backdrop-blur-sm rounded-full w-7 h-7 flex items-center justify-center text-xs font-bold text-white border border-white/20">
                                        #{product.rank}
                                    </div>
                                    {/* Source badge */}
                                    <div className="absolute top-2 right-2">
                                        <SourceBadge source={product.source} />
                                    </div>
                                </div>

                                {/* Content */}
                                <div className="p-4 flex flex-col flex-1 gap-3">
                                    <h3 className="text-sm font-semibold text-white leading-snug group-hover:text-violet-300 transition-colors">
                                        {product.title}
                                    </h3>

                                    {product.price && (
                                        <p className="text-sm font-bold text-emerald-400">{formatPrice(product.price, product.currency)}</p>
                                    )}

                                    {/* Score bars */}
                                    {/* Score bars hidden as requested */}

                                    {/* Open on site button */}
                                    <div className="mt-auto flex items-center justify-center gap-2">
                                        <button
                                            className="py-2.5 px-4 rounded-xl bg-emerald-600/20 border border-emerald-500/40 text-emerald-300 text-sm font-semibold hover:bg-emerald-600/40 hover:border-emerald-400 transition-all"
                                            onClick={() => handleAddToCart(product)}
                                            disabled={cartLoading === product.url}
                                        >
                                            {cartLoading === product.url ? 'Adding...' : addedItems.has(product.url) ? 'Added!' : 'Add to Cart'}
                                        </button>
                                        <button
                                            className="py-2.5 px-4 rounded-xl bg-pink-600/20 border border-pink-500/40 text-pink-300 text-sm font-semibold hover:bg-pink-600/40 hover:border-pink-400 transition-all"
                                            onClick={() => handleBuyNow(product)}
                                            disabled={cartLoading === product.url}
                                        >
                                            {cartLoading === product.url ? 'Processing...' : 'Buy Now'}
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* ── Pipeline Info Footer ── */}
                <div className="mt-16 pt-8 border-t border-slate-800">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
                        {[
                            { step: '01', label: 'CLIP ViT-L/14', sub: 'Image + Text encoding' },
                            { step: '02', label: 'Embedding Fusion', sub: 'α·Img + β·Text (0.6/0.4)' },
                            { step: '03', label: 'SerpAPI Search', sub: 'Myntra · Amazon · Flipkart · AJIO' },
                            { step: '04', label: 'Cosine Re-Rank', sub: 'Top-K semantic similarity' },
                        ].map((item) => (
                            <div key={item.step} className="space-y-1">
                                <div className="text-2xl font-black text-slate-700">{item.step}</div>
                                <div className="text-sm font-bold text-slate-300">{item.label}</div>
                                <div className="text-xs text-slate-500">{item.sub}</div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
