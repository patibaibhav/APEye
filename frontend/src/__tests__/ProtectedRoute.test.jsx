import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { describe, it, expect } from 'vitest';
import AuthContext from '../context/AuthContext';
import ProtectedRoute from '../routes/ProtectedRoute';
import RoleRoute from '../routes/RoleRoute';

describe('ProtectedRoute and RoleRoute', () => {
  it('renders children when authenticated in ProtectedRoute', () => {
    const authValue = {
      isAuthenticated: true,
      user: { id: 1, username: 'admin', role: 'ADMIN' },
      isLoadingAuth: false,
    };

    render(
      <AuthContext.Provider value={authValue}>
        <MemoryRouter initialEntries={['/protected']}>
          <Routes>
            <Route
              path="/protected"
              element={
                <ProtectedRoute>
                  <div>Secret Dashboard Content</div>
                </ProtectedRoute>
              }
            />
          </Routes>
        </MemoryRouter>
      </AuthContext.Provider>
    );

    expect(screen.getByText('Secret Dashboard Content')).toBeInTheDocument();
  });

  it('redirects to /login when unauthenticated in ProtectedRoute', () => {
    const authValue = {
      isAuthenticated: false,
      user: null,
      isLoadingAuth: false,
    };

    render(
      <AuthContext.Provider value={authValue}>
        <MemoryRouter initialEntries={['/protected']}>
          <Routes>
            <Route
              path="/protected"
              element={
                <ProtectedRoute>
                  <div>Secret Dashboard Content</div>
                </ProtectedRoute>
              }
            />
            <Route path="/login" element={<div>Login Page Target</div>} />
          </Routes>
        </MemoryRouter>
      </AuthContext.Provider>
    );

    expect(screen.queryByText('Secret Dashboard Content')).not.toBeInTheDocument();
    expect(screen.getByText('Login Page Target')).toBeInTheDocument();
  });

  it('renders children in RoleRoute when user has required role', () => {
    const authValue = {
      isAuthenticated: true,
      user: { id: 1, username: 'admin', role: 'ADMIN' },
      isLoadingAuth: false,
    };

    render(
      <AuthContext.Provider value={authValue}>
        <MemoryRouter initialEntries={['/admin-only']}>
          <Routes>
            <Route
              path="/admin-only"
              element={
                <RoleRoute allowedRoles={['ADMIN']}>
                  <div>Admin Secret Area</div>
                </RoleRoute>
              }
            />
          </Routes>
        </MemoryRouter>
      </AuthContext.Provider>
    );

    expect(screen.getByText('Admin Secret Area')).toBeInTheDocument();
  });

  it('redirects to /forbidden in RoleRoute when user lacks required role', () => {
    const authValue = {
      isAuthenticated: true,
      user: { id: 2, username: 'analyst1', role: 'ANALYST' },
      isLoadingAuth: false,
    };

    render(
      <AuthContext.Provider value={authValue}>
        <MemoryRouter initialEntries={['/admin-only']}>
          <Routes>
            <Route
              path="/admin-only"
              element={
                <RoleRoute allowedRoles={['ADMIN']}>
                  <div>Admin Secret Area</div>
                </RoleRoute>
              }
            />
            <Route path="/forbidden" element={<div>Access Denied Page</div>} />
          </Routes>
        </MemoryRouter>
      </AuthContext.Provider>
    );

    expect(screen.queryByText('Admin Secret Area')).not.toBeInTheDocument();
    expect(screen.getByText('Access Denied Page')).toBeInTheDocument();
  });
});
