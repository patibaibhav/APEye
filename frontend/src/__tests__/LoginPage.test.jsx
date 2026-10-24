import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import AuthContext from '../context/AuthContext';
import LoginPage from '../pages/LoginPage';

function renderLoginPage({ authValue = {}, initialEntries = ['/login'] } = {}) {
  const defaultAuth = {
    user: null,
    token: null,
    login: vi.fn(),
    logout: vi.fn(),
    isAuthenticated: false,
    hasRole: () => false,
    isLoadingAuth: false,
    ...authValue,
  };

  const renderResult = render(
    <AuthContext.Provider value={defaultAuth}>
      <MemoryRouter initialEntries={initialEntries}>
        <LoginPage />
      </MemoryRouter>
    </AuthContext.Provider>
  );

  return { ...renderResult, auth: defaultAuth };
}

describe('LoginPage Component', () => {
  it('renders login fields and submit button', () => {
    renderLoginPage();

    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('displays session expired alert when reason=expired query param is present', () => {
    renderLoginPage({ initialEntries: ['/login?reason=expired'] });

    expect(screen.getByText(/your session has expired/i)).toBeInTheDocument();
  });

  it('validates empty inputs before submission', async () => {
    const { auth } = renderLoginPage();

    const submitBtn = screen.getByRole('button', { name: /sign in/i });
    fireEvent.click(submitBtn);

    expect(auth.login).not.toHaveBeenCalled();
  });

  it('calls login on submission and displays error when credentials fail', async () => {
    const loginMock = vi.fn().mockRejectedValue(new Error('Invalid username or password'));
    renderLoginPage({ authValue: { login: loginMock } });

    const userInput = screen.getByLabelText(/username/i);
    const passInput = screen.getByLabelText(/password/i);
    const submitBtn = screen.getByRole('button', { name: /sign in/i });

    fireEvent.change(userInput, { target: { value: 'admin' } });
    fireEvent.change(passInput, { target: { value: 'wrongpass123' } });
    fireEvent.click(submitBtn);

    expect(loginMock).toHaveBeenCalledWith('admin', 'wrongpass123');

    await waitFor(() => {
      expect(screen.getByText(/invalid username or password/i)).toBeInTheDocument();
    });
  });
});
