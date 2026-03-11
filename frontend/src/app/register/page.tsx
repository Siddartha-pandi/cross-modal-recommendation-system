'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';
import { Eye, EyeOff, Check, X, Mail, Lock, User } from 'lucide-react';

type ValidationErrors = {
  email?: string;
  password?: string;
  fullName?: string;
  confirmPassword?: string;
};

export default function RegisterPage() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [isLoading, setIsLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [toastMessage, setToastMessage] = useState('');
  const [toastVariant, setToastVariant] = useState<'error' | 'success'>('error');
  const toastTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const { register } = useAuth();
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
      case 'fullName':
        if (value.trim().length < 2) {
          newErrors.fullName = 'Full name must be at least 2 characters';
        } else {
          delete newErrors.fullName;
        }
        break;

      case 'email':
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
          newErrors.email = 'Please enter a valid email address';
        } else {
          delete newErrors.email;
        }
        break;

      case 'password':
        if (value.length < 8) {
          newErrors.password = 'Password must be at least 8 characters';
        } else if (!hasPasswordStrength(value)) {
          newErrors.password = 'Password should include uppercase, lowercase, and numbers';
        } else {
          delete newErrors.password;
        }
        if (confirmPassword && value !== confirmPassword) {
          newErrors.confirmPassword = 'Passwords do not match';
        } else if (confirmPassword) {
          delete newErrors.confirmPassword;
        }
        break;

      case 'confirmPassword':
        if (value !== password) {
          newErrors.confirmPassword = 'Passwords do not match';
        } else {
          delete newErrors.confirmPassword;
        }
        break;
    }

    setErrors(newErrors);
  };

  const hasPasswordStrength = (pass: string) => {
    const hasUpper = /[A-Z]/.test(pass);
    const hasLower = /[a-z]/.test(pass);
    const hasNumber = /[0-9]/.test(pass);
    return hasUpper && hasLower && hasNumber;
  };

  const getPasswordStrength = () => {
    if (!password) return 0;
    let strength = 0;
    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^a-zA-Z0-9]/.test(password)) strength++;
    return strength;
  };

  const getPasswordStrengthLabel = () => {
    const strength = getPasswordStrength();
    if (strength <= 2) return { label: 'Weak', color: 'bg-red-500' };
    if (strength <= 4) return { label: 'Medium', color: 'bg-yellow-500' };
    return { label: 'Strong', color: 'bg-green-500' };
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setSuccessMessage('');

    // Validate all fields
    const newErrors: ValidationErrors = {};
    if (fullName.trim().length < 2) newErrors.fullName = 'Full name is required';
    if (!email) newErrors.email = 'Email is required';
    if (password.length < 8) newErrors.password = 'Password must be at least 8 characters';
    if (password !== confirmPassword) newErrors.confirmPassword = 'Passwords do not match';

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setIsLoading(true);

    try {
      setSuccessMessage('Creating your account...');
      await register(email, password, fullName);
      showToast('Account created successfully', 'success');
      setSuccessMessage('✓ Account created successfully! Redirecting...');
      setTimeout(() => {
        router.push('/recommend');
      }, 1500);
    } catch (err: any) {
      setErrors({});
      setSuccessMessage('');
      showToast(err.message || 'Registration failed. Please try again.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const isFormValid =
    fullName.trim().length >= 2 &&
    email &&
    password.length >= 8 &&
    password === confirmPassword &&
    !errors.email &&
    !errors.password;

  const strength = getPasswordStrength();
  const strengthLabel = getPasswordStrengthLabel();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-neutral-900 flex items-center justify-center px-4 py-12">
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
            Create Your Account
          </h2>
          <p className="mt-2 text-sm text-gray-400">
            Join our fashion recommendation community
          </p>
        </div>

        {/* Register Form */}
        <div className="bg-slate-800 rounded-lg shadow-2xl p-8 border border-slate-700 backdrop-blur-sm">
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Success Message */}
            {successMessage && (
              <div className="bg-green-500/10 border border-green-500 text-green-400 px-4 py-3 rounded-lg text-sm flex items-center gap-2 animate-pulse">
                <Check size={16} />
                {successMessage}
              </div>
            )}

            {/* Full Name Input */}
            <div>
              <label htmlFor="fullName" className="block text-sm font-semibold text-gray-300 mb-2">
                Full Name
              </label>
              <div className="relative">
                <User className="absolute left-3 top-3.5 text-gray-500" size={18} />
                <input
                  id="fullName"
                  name="fullName"
                  type="text"
                  autoComplete="name"
                  required
                  value={fullName}
                  onChange={(e) => {
                    setFullName(e.target.value);
                    validateField('fullName', e.target.value);
                  }}
                  className={`w-full pl-10 pr-4 py-3 bg-slate-900 border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:border-transparent transition ${errors.fullName
                    ? 'border-red-500 focus:ring-red-500'
                    : fullName && !errors.fullName
                      ? 'border-green-500 focus:ring-green-500'
                      : 'border-slate-600 focus:ring-blue-500'
                    }`}
                  placeholder="John Doe"
                />
              </div>
              {errors.fullName && (
                <p className="mt-1 text-xs text-red-400 flex items-center gap-1">
                  <X size={14} /> {errors.fullName}
                </p>
              )}
              {fullName && !errors.fullName && (
                <p className="mt-1 text-xs text-green-400 flex items-center gap-1">
                  <Check size={14} /> Name looks good
                </p>
              )}
            </div>

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
              {errors.email && (
                <p className="mt-1 text-xs text-red-400 flex items-center gap-1">
                  <X size={14} /> {errors.email}
                </p>
              )}
              {email && !errors.email && (
                <p className="mt-1 text-xs text-green-400 flex items-center gap-1">
                  <Check size={14} /> Email is valid
                </p>
              )}
            </div>

            {/* Password Input */}
            <div>
              <label htmlFor="password" className="block text-sm font-semibold text-gray-300 mb-2">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-3.5 text-gray-500" size={18} />
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="new-password"
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
                  className="absolute right-3 top-3.5 text-gray-500 hover:text-gray-300"
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>

              {/* Password Strength Indicator */}
              {password && (
                <div className="mt-2">
                  <div className="flex gap-1 mb-1">
                    {[...Array(6)].map((_, i) => (
                      <div
                        key={i}
                        className={`h-1 flex-1 rounded-full transition ${i < strength ? strengthLabel.color : 'bg-slate-700'
                          }`}
                      />
                    ))}
                  </div>
                  <p className={`text-xs font-medium ${strengthLabel.color === 'bg-red-500'
                    ? 'text-red-400'
                    : strengthLabel.color === 'bg-yellow-500'
                      ? 'text-yellow-400'
                      : 'text-green-400'
                    }`}>
                    Strength: {strengthLabel.label}
                  </p>
                </div>
              )}

              {errors.password && (
                <p className="mt-1 text-xs text-red-400 flex items-center gap-1">
                  <X size={14} /> {errors.password}
                </p>
              )}
              {!errors.password && password && (
                <p className="mt-1 text-xs text-gray-400">
                  ✓ Use uppercase, lowercase, and numbers for strong password
                </p>
              )}
            </div>

            {/* Confirm Password Input */}
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-semibold text-gray-300 mb-2">
                Confirm Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-3.5 text-gray-500" size={18} />
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  required
                  value={confirmPassword}
                  onChange={(e) => {
                    setConfirmPassword(e.target.value);
                    validateField('confirmPassword', e.target.value);
                  }}
                  className={`w-full pl-10 pr-10 py-3 bg-slate-900 border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:border-transparent transition ${errors.confirmPassword
                    ? 'border-red-500 focus:ring-red-500'
                    : confirmPassword && password === confirmPassword
                      ? 'border-green-500 focus:ring-green-500'
                      : 'border-slate-600 focus:ring-blue-500'
                    }`}
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-3.5 text-gray-500 hover:text-gray-300"
                >
                  {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              {errors.confirmPassword && (
                <p className="mt-1 text-xs text-red-400 flex items-center gap-1">
                  <X size={14} /> {errors.confirmPassword}
                </p>
              )}
              {confirmPassword && password === confirmPassword && (
                <p className="mt-1 text-xs text-green-400 flex items-center gap-1">
                  <Check size={14} /> Passwords match
                </p>
              )}
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
                  Creating account...
                </span>
              ) : (
                'Create Account'
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="mt-6 flex items-center gap-4">
            <div className="flex-1 h-px bg-slate-700" />
            <span className="text-xs text-gray-500">Already have an account?</span>
            <div className="flex-1 h-px bg-slate-700" />
          </div>

          {/* Login Link */}
          <div className="mt-6 text-center">
            <Link
              href="/login"
              className="text-blue-400 hover:text-blue-300 font-semibold transition"
            >
              Sign in instead
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
