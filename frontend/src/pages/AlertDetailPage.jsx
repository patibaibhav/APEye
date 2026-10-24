import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, ShieldAlert, Globe, Clock, Layers, User } from 'lucide-react';
import useApiQuery from '../hooks/useApiQuery';
import alertsApi from '../api/alertsApi';
import SeverityBadge from '../components/common/SeverityBadge';
import StatusBadge from '../components/common/StatusBadge';
import AlertStatusSelect from '../components/alerts/AlertStatusSelect';
import AlertEvidencePanel from '../components/alerts/AlertEvidencePanel';
import AlertNotes from '../components/alerts/AlertNotes';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import { ThreatCategoryLabels } from '../utils/constants';
import { formatTimestamp, formatRelativeTime } from '../utils/formatters';

export function AlertDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);
  const [isSubmittingNote, setIsSubmittingNote] = useState(false);
  const [actionError, setActionError] = useState('');

  const alertQuery = useApiQuery(() => alertsApi.get(id), [id]);

  const handleStatusChange = async (newStatus) => {
    setIsUpdatingStatus(true);
    setActionError('');
    try {
      await alertsApi.setStatus(id, { status: newStatus });
      await alertQuery.refetch();
    } catch (err) {
      setActionError(err.message || 'Failed to update alert status');
    } finally {
      setIsUpdatingStatus(false);
    }
  };

  const handleAddNote = async (noteText) => {
    setIsSubmittingNote(true);
    setActionError('');
    try {
      await alertsApi.addNote(id, { note: noteText });
      await alertQuery.refetch();
    } catch (err) {
      setActionError(err.message || 'Failed to add note');
      throw err;
    } finally {
      setIsSubmittingNote(false);
    }
  };

  const alert = alertQuery.data;

  if (alertQuery.isLoading && !alert) {
    return <LoadingState message="Loading alert details..." rows={6} />;
  }

  if (alertQuery.error) {
    return (
      <div className="space-y-4">
        <button
          type="button"
          onClick={() => navigate('/alerts')}
          className="btn-secondary text-xs inline-flex items-center gap-1.5"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Alerts</span>
        </button>
        <ErrorState
          title="Alert Not Found or Error"
          message={alertQuery.error.message || `Unable to load details for alert #${id}`}
          requestId={alertQuery.error.requestId}
          onRetry={() => alertQuery.refetch()}
        />
      </div>
    );
  }

  if (!alert) return null;

  return (
    <div className="space-y-6">
      {/* Navigation & Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-matte-800 pb-5">
        <div className="space-y-2">
          <button
            type="button"
            onClick={() => navigate('/alerts')}
            className="text-xs text-matte-400 hover:text-matte-200 inline-flex items-center gap-1.5 transition"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to All Alerts</span>
          </button>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold tracking-tight text-matte-100 flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-pastel-rose" />
              <span>Alert #{alert.id}</span>
            </h1>
            <SeverityBadge severity={alert.severity} />
            <StatusBadge status={alert.status} />
          </div>
          <p className="text-xs text-matte-300 font-medium">
            {ThreatCategoryLabels[alert.category] || alert.category}
          </p>
        </div>

        {/* Status Transition Control */}
        <div>
          <AlertStatusSelect
            currentStatus={alert.status}
            onStatusChange={handleStatusChange}
            isLoading={isUpdatingStatus}
          />
        </div>
      </div>

      {actionError && (
        <div className="p-3 rounded-lg bg-pastel-rose-bg border border-pastel-rose-border text-pastel-rose-light text-xs">
          {actionError}
        </div>
      )}

      {/* Primary Alert Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        <div className="matte-card p-4 space-y-1">
          <div className="flex items-center gap-1.5 text-matte-500 text-[11px] font-medium">
            <Globe className="w-3.5 h-3.5 text-pastel-lavender" />
            <span>Source IP Address</span>
          </div>
          <p className="font-mono text-sm font-semibold text-matte-100">{alert.source_ip}</p>
        </div>

        <div className="matte-card p-4 space-y-1">
          <div className="flex items-center gap-1.5 text-matte-500 text-[11px] font-medium">
            <Clock className="w-3.5 h-3.5 text-pastel-amber" />
            <span>Detection Timing</span>
          </div>
          <p className="font-mono text-xs text-matte-200" title={formatTimestamp(alert.last_detected_at)}>
            {formatRelativeTime(alert.last_detected_at)}
          </p>
          <span className="text-[10px] text-matte-500 block">
            First seen: {formatTimestamp(alert.first_detected_at)}
          </span>
        </div>

        <div className="matte-card p-4 space-y-1">
          <div className="flex items-center gap-1.5 text-matte-500 text-[11px] font-medium">
            <Layers className="w-3.5 h-3.5 text-pastel-mint" />
            <span>Aggregation & Events</span>
          </div>
          <p className="font-mono text-sm font-semibold text-matte-100">
            {alert.event_count} {alert.event_count === 1 ? 'event' : 'events'}
          </p>
          <span className="text-[10px] text-matte-500 block">
            Dedup key: <span className="font-mono select-all">{alert.dedup_key || '—'}</span>
          </span>
        </div>

        <div className="matte-card p-4 space-y-1">
          <div className="flex items-center gap-1.5 text-matte-500 text-[11px] font-medium">
            <User className="w-3.5 h-3.5 text-pastel-slate" />
            <span>Associated User</span>
          </div>
          <p className="font-mono text-xs text-matte-200">
            {alert.user_id ? `User #${alert.user_id}` : 'Unauthenticated / Anonymous'}
          </p>
        </div>
      </div>

      {/* Targeted Endpoints */}
      <div className="matte-card p-5 space-y-3">
        <h2 className="text-xs font-semibold text-matte-300 uppercase tracking-wider">
          Observed Targeted Endpoints
        </h2>
        {alert.endpoints && alert.endpoints.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {alert.endpoints.map((ep, idx) => (
              <span
                key={idx}
                className="px-2.5 py-1 rounded bg-matte-900 border border-matte-800 font-mono text-xs text-matte-200"
              >
                {ep}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-xs text-matte-500 italic">No specific endpoints recorded.</p>
        )}
      </div>

      {/* Grid: Evidence and Notes */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AlertEvidencePanel
          evidence={alert.evidence}
          threshold={alert.threshold}
          windowSeconds={alert.window_seconds}
          requestCount={alert.request_count}
        />
        <AlertNotes
          notes={alert.notes || []}
          onAddNote={handleAddNote}
          isSubmitting={isSubmittingNote}
        />
      </div>
    </div>
  );
}

export default AlertDetailPage;
