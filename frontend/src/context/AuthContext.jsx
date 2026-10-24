import React, { createContext, useState, useEffect, useCallback } from 'react';
import authApi from '../api/authApi';
import { setClientToken, clearClientToken } from '../api/client';

const AuthContext = createContext(null);

const TOKEN_KEY = 'apeye_token';
const USER_KEY = 'apeye_user';

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => {
    try {
      return sessionStorage.getItem(TOKEN_KEY) || null;
    } catch {
      return null;
    }
  });

  const [user, setUser] = useState(() => {
    try {
      const stored = sessionStorage.getItem(USER_KEY);
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  const [isLoadingAuth, setIsLoadingAuth] = useState(false);

  // Sync token with apiClient
  useEffect(() => {
    if (token) {
      setClientToken(token);
    } else {
      clearClientToken();
    }
  }, [token]);

  const login = useCallback(async (username, password) => {
    setIsLoadingAuth(true);
    try {
      const response = await authApi.login({ username, password });
      const newToken = response.access_token;
      const newUser = response.user;

      setToken(newToken);
      setUser(newUser);

      try {
        sessionStorage.setItem(TOKEN_KEY, newToken);
        sessionStorage.setItem(USER_KEY, JSON.stringify(newUser));
      } catch (err) {
        console.warn('SessionStorage unavailable', err);
      }

      setClientToken(newToken);
      return { success: true, user: newUser };
    } finally {
      setIsLoadingAuth(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch (err) {
      // Ignore network / logout errors during teardown
    } finally {
      setToken(null);
      setUser(null);
      clearClientToken();
      try {
        sessionStorage.removeItem(TOKEN_KEY);
        sessionStorage.removeItem(USER_KEY);
      } catch {
        // ignore
      }
    }
  }, []);

  const hasRole = useCallback((role) => {
    if (!user || !user.role) return false;
    return user.role.toUpperCase() === role.toUpperCase();
  }, [user]);

  const isAuthenticated = Boolean(token && user);

  const value = {
    user,
    token,
    login,
    logout,
    isAuthenticated,
    hasRole,
    isLoadingAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export { useAuth } from './useAuth';
export default AuthContext;
