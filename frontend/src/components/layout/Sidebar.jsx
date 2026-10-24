import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  ShieldAlert,
  LayoutDashboard,
  ScrollText,
  AlertTriangle,
  UserCheck,
  FileArchive,
  Users,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Role } from '../../utils/constants';

export function Sidebar({ isOpen, onClose }) {
  const { hasRole } = useAuth();
  const isAdmin = hasRole(Role.ADMIN);

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Request Logs', path: '/logs', icon: ScrollText },
    { name: 'Security Alerts', path: '/alerts', icon: AlertTriangle },
    { name: 'Suspicious IPs', path: '/suspicious-ips', icon: UserCheck },
    { name: 'Reports & Export', path: '/reports', icon: FileArchive },
  ];

  if (isAdmin) {
    navItems.push({ name: 'User Management', path: '/users', icon: Users });
  }

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-64 bg-[#121216] border-r border-matte-800 flex flex-col transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand */}
        <div className="h-16 px-6 flex items-center gap-3 border-b border-matte-800">
          <div className="w-8 h-8 rounded-lg bg-matte-800 border border-matte-700 flex items-center justify-center text-pastel-lavender">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <h1 className="font-bold text-sm tracking-tight text-matte-100 flex items-center gap-1.5">
              <span>APEye</span>
              <span className="text-[10px] font-normal px-1.5 py-0.5 rounded bg-matte-800 text-matte-400">v1.0</span>
            </h1>
            <p className="text-[11px] text-matte-500">Security Monitoring</p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          <div className="px-3 pb-2 text-[10px] font-semibold tracking-wider text-matte-500 uppercase">
            Platform
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={onClose}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-colors ${
                    isActive
                      ? 'bg-matte-800 text-pastel-lavender font-semibold border-l-2 border-pastel-lavender shadow-sm'
                      : 'text-matte-400 hover:text-matte-200 hover:bg-matte-800/40'
                  }`
                }
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* Footer info */}
        <div className="p-4 border-t border-matte-800 text-[11px] text-matte-500">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-pastel-mint animate-pulse" />
            <span className="text-matte-400 font-medium">Monitoring Active</span>
          </div>
          <p className="mt-1 text-[10px] text-matte-600">Educational Security SIEM</p>
        </div>
      </aside>
    </>
  );
}

export default Sidebar;
