'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';
import { Eye, EyeOff, Check, X, Mail, Lock } from 'lucide-react';

type ValidationErrors = {
  email?: string;
  password?: string;
};

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [isLoading, setIsLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [toastMessage, setToastMessage] = useState('');
  const [toastVariant, setToastVariant] = useState<'error' | 'success'>('error');
  const toastTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const { login } = useAuth();
  const router = useRouter();

  useEffect(() => {
    return () => {
      if (toastTimeoutRef.current) {
        clearTimeout(toastTimeoutRef.current);
      }
    };
  }, []);

  const showToast = (message: string, variant: 'error' | 'success') => {
    setToastMessage(message);
    setToastVariant(variant);
    if (toastTimeoutRef.current) {
      clearTimeout(toastTimeoutRef.current);
    }
    toastTimeoutRef.current = setTimeout(() => {
      setToastMessage('');
    }, 3000);
  };

  // Real-time validation
  const validateField = (name: string, value: string) => {
    const newErrors = { ...errors };

    switch (name) {
      case 'email':
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (value && !emailRegex.test(value)) {
          newErrors.email = 'Please enter a valid email address';
        } else {
          delete newErrors.email;
        }
        break;

      case 'password':
        if (value && value.length < 8) {
          newErrors.password = 'Password must be at least 8 characters';
        } else {
          delete newErrors.password;
        }
        break;
    }

    setErrors(newErrors);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setSuccessMessage('');

    // Validate fields
    const newErrors: ValidationErrors = {};
    if (!email) newErrors.email = 'Email is required';
    if (!password) newErrors.password = 'Password is required';

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setIsLoading(true);

    try {
      setSuccessMessage('Signing in...');
      await login(email, password);
      showToast('Login successful', 'success');
      setSuccessMessage('✓ Login successful! Redirecting...');
      setTimeout(() => {
        router.push('/recommend');
      }, 1500);
    } catch (err: any) {
      setErrors({});
      setSuccessMessage('');
      showToast(err.message || 'Login failed. Please check your credentials.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const isFormValid = email && password && !errors.email && !errors.password;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-neutral-900 flex items-center justify-center px-4">
      {toastMessage && (
        <div
          className={`fixed bottom-6 right-6 z-50 px-4 py-3 rounded-lg shadow-lg text-sm text-white ${toastVariant === 'success' ? 'bg-green-500/90' : 'bg-red-500/90'
            }`}
        >
          {toastMessage}
        </div>
      )}
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <Link href="/" className="inline-block text-3xl font-bold text-white hover:text-gray-300 transition">
            Fashion Finder
          </Link>
          <h2 className="mt-6 text-3xl font-bold text-white">
            Welcome Back
          </h2>
          <p className="mt-2 text-sm text-gray-400">
            Sign in to continue exploring fashion
          </p>
        </div>

        {/* Login Form */}
        <div className="bg-slate-800 rounded-lg shadow-2xl p-8 border border-slate-700 backdrop-blur-sm">
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Success Message */}
            {successMessage && (
              <div className="bg-green-500/10 border border-green-500 text-green-400 px-4 py-3 rounded-lg text-sm flex items-center gap-2 animate-pulse">
                <Check size={16} />
                {successMessage}
              </div>
            )}

            {/* Error Message */}
            {(errors.email || errors.password) && (
              <div className="bg-red-500/10 border border-red-500 text-red-400 px-4 py-3 rounded-lg text-sm flex items-start gap-2">
                <X size={16} className="mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-semibold">Login Error</p>
                  <p className="text-xs mt-1">{errors.email || errors.password}</p>
                </div>
              </div>
            )}

            {/* Email Input */}
            <div>
              <label htmlFor="email" className="block text-sm font-semibold text-gray-300 mb-2">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-3.5 text-gray-500" size={18} />
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    validateField('email', e.target.value);
                  }}
                  className={`w-full pl-10 pr-4 py-3 bg-slate-900 border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:border-transparent transition ${errors.email
                    ? 'border-red-500 focus:ring-red-500'
                    : email && !errors.email
                      ? 'border-green-500 focus:ring-green-500'
                      : 'border-slate-600 focus:ring-blue-500'
                    }`}
                  placeholder="you@example.com"
                />
              </div>
              {email && !errors.email && (
                <p className="mt-1 text-xs text-green-400 flex items-center gap-1">
                  <Check size={14} /> Email is valid
                </p>
              )}
            </div>

            {/* Password Input */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <label htmlFor="password" className="block text-sm font-semibold text-gray-300">
                  Password
                </label>
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-3.5 text-gray-500" size={18} />
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    validateField('password', e.target.value);
                  }}
                  className={`w-full pl-10 pr-10 py-3 bg-slate-900 border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:border-transparent transition ${errors.password
                    ? 'border-red-500 focus:ring-red-500'
                    : password && !errors.password
                      ? 'border-green-500 focus:ring-green-500'
                      : 'border-slate-600 focus:ring-blue-500'
                    }`}
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-3.5 text-gray-500 hover:text-gray-300 transition"
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              {password && !errors.password && (
                <p className="mt-1 text-xs text-green-400 flex items-center gap-1">
                  <Check size={14} /> Password is valid
                </p>
              )}
              <div className="mt-2 text-right">
                <Link href="/forgot-password" className="text-xs text-blue-400 hover:text-blue-300 transition">
                  Forgot password?
                </Link>
              </div>
            </div>

            {/* Remember Me */}
            <div className="flex items-center">
              <input
                id="remember"
                name="remember"
                type="checkbox"
                className="h-4 w-4 rounded bg-slate-900 border-slate-600 text-blue-600 focus:ring-blue-500 cursor-pointer"
              />
              <label htmlFor="remember" className="ml-2 block text-sm text-gray-400 cursor-pointer">
                Remember me
              </label>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading || !isFormValid}
              className="w-full py-3 px-4 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-semibold rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed mt-6 shadow-lg hover:shadow-blue-500/50"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Signing in...
                </span>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="mt-6 flex items-center gap-4">
            <div className="flex-1 h-px bg-slate-700" />
            <span className="text-xs text-gray-500">New to Fashion Finder?</span>
            <div className="flex-1 h-px bg-slate-700" />
          </div>

          {/* Register Link */}
          <div className="mt-6 text-center">
            <Link
              href="/register"
              className="text-blue-400 hover:text-blue-300 font-semibold transition"
            >
              Create a new account
            </Link>
          </div>
        </div>

        {/* Back to Home */}
        <div className="text-center">
          <Link href="/" className="text-sm text-gray-400 hover:text-gray-300 transition">
            ← Back to Home
          </Link>
        </div>


      </div>
    </div>
  );
}
