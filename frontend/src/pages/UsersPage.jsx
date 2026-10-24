import React, { useState } from 'react';
import { Users, UserPlus, RefreshCw, AlertCircle, CheckCircle, XCircle } from 'lucide-react';
import useApiQuery from '../hooks/useApiQuery';
import usersApi from '../api/usersApi';
import { useAuth } from '../context/AuthContext';
import { Role } from '../utils/constants';
import { formatTimestamp } from '../utils/formatters';
import Pagination from '../components/common/Pagination';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import EmptyState from '../components/common/EmptyState';

export function UsersPage() {
  const { user: currentUser } = useAuth();

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  // Create User Modal state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [newUsername, setNewUsername] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newRole, setNewRole] = useState(Role.ANALYST);
  const [createError, setCreateError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const usersQuery = useApiQuery(
    () => usersApi.list({ page, page_size: pageSize }),
    [page, pageSize]
  );

  const handleCreateUser = async (e) => {
    e.preventDefault();
    if (newPassword.length < 12) {
      setCreateError('Password must be at least 12 characters long');
      return;
    }

    setIsSubmitting(true);
    setCreateError('');

    try {
      await usersApi.create({
        username: newUsername.trim(),
        password: newPassword,
        role: newRole,
      });
      setIsCreateModalOpen(false);
      setNewUsername('');
      setNewPassword('');
      setNewRole(Role.ANALYST);
      usersQuery.refetch();
    } catch (err) {
      setCreateError(err.message || 'Failed to create user');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleToggleStatus = async (user) => {
    if (user.id === currentUser?.id) {
      alert('You cannot deactivate your own administrative account.');
      return;
    }

    try {
      await usersApi.update(user.id, { is_active: !user.is_active });
      usersQuery.refetch();
    } catch (err) {
      alert(`Update failed: ${err.message || 'Unknown error'}`);
    }
  };

  const handleChangeRole = async (user, newRoleValue) => {
    try {
      await usersApi.update(user.id, { role: newRoleValue });
      usersQuery.refetch();
    } catch (err) {
      alert(`Role update failed: ${err.message || 'Unknown error'}`);
    }
  };

  const pageData = usersQuery.data;
  const items = pageData?.items || [];
  const isLoading = usersQuery.isLoading && !usersQuery.data;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-matte-100 flex items-center gap-2">
            <Users className="w-5 h-5 text-pastel-lavender" />
            <span>User Management</span>
          </h1>
          <p className="text-xs text-matte-400 mt-0.5">
            Admin console: manage platform credentials, analyst access, and account status
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setIsCreateModalOpen(true)}
            className="btn-primary text-xs py-2 px-3 flex items-center gap-1.5"
          >
            <UserPlus className="w-4 h-4" />
            <span>New User</span>
          </button>
          <button
            type="button"
            onClick={() => usersQuery.refetch()}
            className="p-2 rounded-lg bg-matte-800 border border-matte-700 text-matte-300 hover:text-matte-100 hover:bg-matte-700 transition"
            title="Refresh users"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${usersQuery.isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Main States */}
      {isLoading && <LoadingState message="Loading system users..." rows={5} />}

      {!isLoading && usersQuery.error && (
        <ErrorState
          title="Failed to load users"
          message={usersQuery.error.message}
          requestId={usersQuery.error.requestId}
          onRetry={() => usersQuery.refetch()}
        />
      )}

      {!isLoading && !usersQuery.error && items.length === 0 && (
        <EmptyState
          title="No users found"
          description="No user accounts were found in the database."
        />
      )}

      {!isLoading && !usersQuery.error && items.length > 0 && (
        <div className="matte-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-matte-900/80 border-b border-matte-800 text-matte-400 font-medium">
                <tr>
                  <th className="py-3 px-4 w-16">ID</th>
                  <th className="py-3 px-4">Username</th>
                  <th className="py-3 px-4">Role</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Created At</th>
                  <th className="py-3 px-4">Last Login</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-matte-800/60 bg-matte-950/40">
                {items.map((u) => {
                  const isCurrent = u.id === currentUser?.id;
                  return (
                    <tr key={u.id} className="hover:bg-matte-800/20">
                      <td className="py-3 px-4 font-mono text-matte-400">#{u.id}</td>
                      <td className="py-3 px-4 font-semibold text-matte-100">
                        {u.username}
                        {isCurrent && (
                          <span className="ml-2 px-1.5 py-0.5 rounded bg-matte-800 text-[10px] text-pastel-lavender font-mono">
                            You
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        <select
                          value={u.role}
                          onChange={(e) => handleChangeRole(u, e.target.value)}
                          disabled={isCurrent}
                          className="bg-matte-900 border border-matte-800 rounded px-2 py-1 text-xs text-matte-200 focus:outline-none focus:border-matte-600 disabled:opacity-60"
                        >
                          <option value={Role.ADMIN}>ADMIN</option>
                          <option value={Role.ANALYST}>ANALYST</option>
                        </select>
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium border ${
                            u.is_active
                              ? 'bg-pastel-mint-bg text-pastel-mint-light border-pastel-mint-border'
                              : 'bg-matte-800 text-matte-400 border-matte-700'
                          }`}
                        >
                          {u.is_active ? <CheckCircle className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                          <span>{u.is_active ? 'Active' : 'Inactive'}</span>
                        </span>
                      </td>
                      <td className="py-3 px-4 font-mono text-matte-400">
                        {formatTimestamp(u.created_at)}
                      </td>
                      <td className="py-3 px-4 font-mono text-matte-400">
                        {u.last_login_at ? formatTimestamp(u.last_login_at) : 'Never'}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          type="button"
                          onClick={() => handleToggleStatus(u)}
                          disabled={isCurrent}
                          className={`text-xs px-2.5 py-1 rounded transition border ${
                            u.is_active
                              ? 'btn-danger disabled:opacity-40'
                              : 'btn-secondary disabled:opacity-40'
                          }`}
                        >
                          {u.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <Pagination
            page={pageData.page}
            pageSize={pageData.page_size}
            totalItems={pageData.total_items}
            totalPages={pageData.total_pages}
            onPageChange={(p) => setPage(p)}
            onPageSizeChange={(ps) => {
              setPageSize(ps);
              setPage(1);
            }}
          />
        </div>
      )}

      {/* New User Modal */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setIsCreateModalOpen(false)} />
          <div className="relative w-full max-w-md matte-card p-6 bg-matte-900 border border-matte-700 shadow-2xl z-10 space-y-4">
            <h3 className="text-base font-bold text-matte-100">Create New System User</h3>
            <p className="text-xs text-matte-400">
              Users authenticate to the monitoring dashboard via bcrypt hashed credentials.
            </p>

            {createError && (
              <div className="p-2.5 rounded bg-pastel-rose-bg border border-pastel-rose-border text-pastel-rose-light text-xs flex items-center gap-1.5">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{createError}</span>
              </div>
            )}

            <form onSubmit={handleCreateUser} className="space-y-4 text-xs">
              <div>
                <label className="block text-[11px] font-medium text-matte-400 mb-1">Username</label>
                <input
                  type="text"
                  required
                  value={newUsername}
                  onChange={(e) => setNewUsername(e.target.value)}
                  placeholder="e.g. sec_analyst"
                  className="input-matte w-full"
                />
              </div>

              <div>
                <label className="block text-[11px] font-medium text-matte-400 mb-1">
                  Password (min 12 characters)
                </label>
                <input
                  type="password"
                  required
                  minLength={12}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="input-matte w-full"
                />
              </div>

              <div>
                <label className="block text-[11px] font-medium text-matte-400 mb-1">Role</label>
                <select
                  value={newRole}
                  onChange={(e) => setNewRole(e.target.value)}
                  className="input-matte w-full"
                >
                  <option value={Role.ANALYST}>ANALYST (Triage, notes, views)</option>
                  <option value={Role.ADMIN}>ADMIN (Full system access, users, archival)</option>
                </select>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-matte-800">
                <button
                  type="button"
                  onClick={() => setIsCreateModalOpen(false)}
                  disabled={isSubmitting}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="btn-primary"
                >
                  {isSubmitting ? 'Creating...' : 'Create User'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default UsersPage;
