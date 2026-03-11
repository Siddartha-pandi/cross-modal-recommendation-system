'use client';

import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';

export default function Home() {
  const { isAuthenticated, user, logout } = useAuth();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  const handleStartShopping = () => {
    if (isAuthenticated) {
      router.push('/recommend');
    } else {
      router.push('/login');
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Hero Section with Dark Gradient Background */}
      <div
        className="min-h-screen relative flex flex-col items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-neutral-900"
      >
        {/* Navigation */}
        <nav className="absolute top-0 left-0 right-0 z-50 px-4 py-6">
          <div className="max-w-7xl mx-auto flex justify-between items-center">
            <div className="text-2xl font-bold text-white">
              Fashion Finder
            </div>
            <div className="flex gap-4 items-center">
              {isAuthenticated ? (
                <>
                  <span className="text-gray-300">Welcome, {user?.full_name}!</span>
                  <button
                    onClick={handleLogout}
                    className="px-6 py-2 text-white hover:text-gray-300 transition font-medium"
                  >
                    Logout
                  </button>
                </>
              ) : (
                <>
                  <Link
                    href="/login"
                    className="px-6 py-2 text-white hover:text-gray-300 transition font-medium"
                  >
                    Login
                  </Link>
                  <Link
                    href="/register"
                    className="px-6 py-2 border-2 border-white rounded-lg hover:bg-white hover:text-slate-950 transition font-medium"
                  >
                    Register
                  </Link>
                </>
              )}
            </div>
          </div>
        </nav>

        {/* Content */}
        <div className="relative z-10 text-center max-w-3xl px-4">
          <h1 className="text-6xl md:text-7xl font-bold mb-6 leading-tight text-white">
            Hybrid Cross-Modal
            <br />
            Fashion Recommendation System
          </h1>

          <p className="text-lg md:text-xl text-gray-300 mb-12">
            Search with text, images, or both using AI-powered similarity matching
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={handleStartShopping}
              className="inline-block px-10 py-4 bg-blue-600 rounded-lg font-bold text-lg hover:bg-blue-700 transition cursor-pointer"
            >
              {isAuthenticated ? 'Start Search →' : 'Login to Start Matching →'}
            </button>
            {/* <Link
              href="/recommend"
              className="inline-block px-10 py-4 bg-gradient-to-r from-violet-600 to-pink-600 rounded-lg font-bold text-lg hover:from-violet-500 hover:to-pink-500 transition text-center"
            >
              Live Web Recommend ✨
            </Link> */}
          </div>
        </div>
      </div>

      {/* Features Section */}
    </div>
  );
}
