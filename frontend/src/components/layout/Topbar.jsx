import React from 'react';
import { Menu, LogOut, Shield } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Role } from '../../utils/constants';

export function Topbar({ onOpenSidebar }) {
  const { user, logout } = useAuth();

  const isRoleAdmin = user?.role === Role.ADMIN;

  return (
    <header className="h-16 bg-[#121216] border-b border-matte-800 px-4 sm:px-8 flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onOpenSidebar}
          className="p-2 rounded-lg text-matte-400 hover:text-matte-100 hover:bg-matte-800 lg:hidden"
          aria-label="Open navigation menu"
        >
          <Menu className="w-5 h-5" />
        </button>
        <div className="hidden sm:flex items-center gap-2 text-xs text-matte-400">
          <Shield className="w-4 h-4 text-pastel-lavender" />
          <span className="font-medium text-matte-200">APEye Security Hub</span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {user && (
          <div className="flex items-center gap-3">
            <div className="text-right">
              <span className="block text-xs font-semibold text-matte-200">{user.username}</span>
              <span
                className={`inline-block text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.2 rounded border ${
                  isRoleAdmin
                    ? 'bg-pastel-lavender-bg text-pastel-lavender-light border-pastel-lavender-border'
                    : 'bg-matte-800 text-matte-400 border-matte-700'
                }`}
              >
                {user.role}
              </span>
            </div>

            <button
              type="button"
              onClick={logout}
              className="p-2 rounded-lg bg-matte-800/80 border border-matte-700/60 text-matte-300 hover:text-pastel-rose-light hover:bg-pastel-rose-bg/30 hover:border-pastel-rose-border transition-colors text-xs flex items-center gap-1.5"
              title="Sign out"
              aria-label="Log out"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span className="hidden md:inline">Sign Out</span>
            </button>
          </div>
        )}
      </div>
    </header>
  );
}

export default Topbar;
