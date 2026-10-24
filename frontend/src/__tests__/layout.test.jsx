import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import AuthContext from '../context/AuthContext';
import Sidebar from '../components/layout/Sidebar';
import Topbar from '../components/layout/Topbar';

describe('Layout Components (Sidebar and Topbar)', () => {
  it('renders Sidebar with links and displays User Management for ADMIN', () => {
    const authAdmin = {
      user: { id: 1, username: 'admin', role: 'ADMIN' },
      hasRole: (r) => r === 'ADMIN',
    };

    render(
      <AuthContext.Provider value={authAdmin}>
        <MemoryRouter>
          <Sidebar isOpen={true} onClose={() => {}} />
        </MemoryRouter>
      </AuthContext.Provider>
    );

    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Request Logs')).toBeInTheDocument();
    expect(screen.getByText('Security Alerts')).toBeInTheDocument();
    expect(screen.getByText('Suspicious IPs')).toBeInTheDocument();
    expect(screen.getByText('Reports & Export')).toBeInTheDocument();
    expect(screen.getByText('User Management')).toBeInTheDocument();
  });

  it('hides User Management in Sidebar for ANALYST', () => {
    const authAnalyst = {
      user: { id: 2, username: 'analyst1', role: 'ANALYST' },
      hasRole: (r) => r === 'ANALYST',
    };

    render(
      <AuthContext.Provider value={authAnalyst}>
        <MemoryRouter>
          <Sidebar isOpen={true} onClose={() => {}} />
        </MemoryRouter>
      </AuthContext.Provider>
    );

    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.queryByText('User Management')).not.toBeInTheDocument();
  });

  it('renders Topbar with username, role badge, and fires logout on sign out click', () => {
    const logoutMock = vi.fn();
    const authValue = {
      user: { id: 1, username: 'security_lead', role: 'ADMIN' },
      logout: logoutMock,
    };

    render(
      <AuthContext.Provider value={authValue}>
        <MemoryRouter>
          <Topbar onOpenSidebar={() => {}} />
        </MemoryRouter>
      </AuthContext.Provider>
    );

    expect(screen.getByText('security_lead')).toBeInTheDocument();
    expect(screen.getByText('ADMIN')).toBeInTheDocument();

    const signoutBtn = screen.getByRole('button', { name: /log out/i });
    fireEvent.click(signoutBtn);
    expect(logoutMock).toHaveBeenCalledTimes(1);
  });
});
