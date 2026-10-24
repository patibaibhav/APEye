import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export function RoleRoute({ allowedRoles = [], children }) {
  const { isAuthenticated, user, isLoadingAuth } = useAuth();
  const location = useLocation();

  if (isLoadingAuth) {
    return null;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  const role = user?.role?.toUpperCase();
  const allowed = allowedRoles.map((r) => r.toUpperCase());

  if (!role || !allowed.includes(role)) {
    return <Navigate to="/forbidden" replace />;
  }

  return children;
}

export default RoleRoute;
