import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect } from 'vitest';
import AuthContext from '../context/AuthContext';
import AppRoutes from '../routes/AppRoutes';

function renderWithRouter(initialRoute = '/', authValue = {}) {
  const defaultAuth = {
    user: null,
    token: null,
    login: async () => {},
    logout: async () => {},
    isAuthenticated: false,
    hasRole: () => false,
    isLoadingAuth: false,
    ...authValue,
  };

  return render(
    <AuthContext.Provider value={defaultAuth}>
      <MemoryRouter initialEntries={[initialRoute]}>
        <AppRoutes />
      </MemoryRouter>
    </AuthContext.Provider>
  );
}

describe('Frontend Routing and Access Control', () => {
  it('renders login page on /login', () => {
    renderWithRouter('/login');
    expect(screen.getByRole('heading', { name: /APEye Monitor/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
  });

  it('redirects unauthenticated user from /dashboard to /login', () => {
    renderWithRouter('/dashboard', { isAuthenticated: false });
    expect(screen.getByRole('heading', { name: /APEye Monitor/i })).toBeInTheDocument();
  });

  it('redirects unauthenticated user from /alerts to /login', () => {
    renderWithRouter('/alerts', { isAuthenticated: false });
    expect(screen.getByRole('heading', { name: /APEye Monitor/i })).toBeInTheDocument();
  });

  it('renders forbidden page on /forbidden', () => {
    renderWithRouter('/forbidden');
    expect(screen.getByText(/403 — Access Denied/i)).toBeInTheDocument();
  });

  it('renders 404 not found page on unknown route', () => {
    renderWithRouter('/some-nonexistent-path-12345');
    expect(screen.getByText(/404 — Page Not Found/i)).toBeInTheDocument();
  });

  it('blocks analyst from accessing /users and redirects to /forbidden', () => {
    renderWithRouter('/users', {
      isAuthenticated: true,
      user: { id: 2, username: 'analyst1', role: 'ANALYST' },
      hasRole: (role) => role === 'ANALYST',
    });
    expect(screen.getByText(/403 — Access Denied/i)).toBeInTheDocument();
  });
});
