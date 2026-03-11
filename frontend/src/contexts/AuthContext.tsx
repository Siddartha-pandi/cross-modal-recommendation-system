'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

interface User {
  user_id: string;
  email: string;
  full_name: string;
  created_at: string;
  is_active: boolean;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api/v1';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load user from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('auth_token');
    const storedUser = localStorage.getItem('auth_user');

    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(JSON.parse(storedUser));
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        let error_message = 'Login failed';
        try {
          const error = await response.json();
          error_message = error.detail || error.message || error_message;
        } catch (e) {
          error_message = `Error ${response.status}: ${response.statusText}`;
        }
        throw new Error(error_message);
      }

      const data = await response.json();

      setToken(data.access_token);
      setUser(data.user);

      localStorage.setItem('auth_token', data.access_token);
      localStorage.setItem('auth_user', JSON.stringify(data.user));
    } catch (error: any) {
      console.error('Login error:', error);
      throw new Error(error.message || 'Login failed. Please try again.');
    }
  };

  const register = async (email: string, password: string, fullName: string) => {
    try {
      const response = await fetch(`${API_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          password,
          full_name: fullName,
        }),
      });

      if (!response.ok) {
        let error_message = 'Registration failed';
        try {
          const error = await response.json();
          error_message = error.detail || error.message || error_message;
        } catch (e) {
          error_message = `Error ${response.status}: ${response.statusText}`;
        }
        throw new Error(error_message);
      }

      const data = await response.json();

      setToken(data.access_token);
      setUser(data.user);

      localStorage.setItem('auth_token', data.access_token);
      localStorage.setItem('auth_user', JSON.stringify(data.user));
    } catch (error: any) {
      console.error('Registration error:', error);
      throw new Error(error.message || 'Registration failed. Please try again.');
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        login,
        register,
        logout,
        isAuthenticated: !!user,
        isLoading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
