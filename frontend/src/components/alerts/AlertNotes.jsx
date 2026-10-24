import React, { useState } from 'react';
import { MessageSquare, Send, User, Bot } from 'lucide-react';
import { formatTimestamp } from '../../utils/formatters';

export function AlertNotes({ notes = [], onAddNote, isSubmitting = false }) {
  const [newNote, setNewNote] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    const trimmed = newNote.trim();
    if (!trimmed) return;
    if (trimmed.length > 2000) {
      setErrorMsg('Note cannot exceed 2000 characters');
      return;
    }

    setErrorMsg('');
    try {
      await onAddNote(trimmed);
      setNewNote('');
    } catch (err) {
      setErrorMsg(err.message || 'Failed to submit note');
    }
  };

  return (
    <div className="matte-card p-5 space-y-4">
      <div className="flex items-center gap-2 border-b border-matte-800 pb-3">
        <MessageSquare className="w-4 h-4 text-pastel-lavender" />
        <h3 className="text-sm font-semibold text-matte-200">Investigation Notes & Activity</h3>
        <span className="text-xs text-matte-500 font-mono">({notes.length})</span>
      </div>

      {/* Notes List */}
      <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
        {notes.length === 0 ? (
          <p className="text-xs text-matte-500 italic py-2">No notes added yet for this alert.</p>
        ) : (
          notes.map((item) => {
            const isSystem = !item.author_username;
            return (
              <div
                key={item.id}
                className="p-3 rounded-lg bg-matte-900 border border-matte-800 space-y-1 text-xs"
              >
                <div className="flex items-center justify-between text-[11px] text-matte-400">
                  <div className="flex items-center gap-1.5 font-medium">
                    {isSystem ? (
                      <Bot className="w-3.5 h-3.5 text-matte-500" />
                    ) : (
                      <User className="w-3.5 h-3.5 text-pastel-lavender" />
                    )}
                    <span className={isSystem ? 'text-matte-500 italic' : 'text-matte-200'}>
                      {item.author_username || 'System Event'}
                    </span>
                  </div>
                  <span className="font-mono text-matte-500 text-[10px]">
                    {formatTimestamp(item.created_at)}
                  </span>
                </div>
                <p className="text-matte-300 whitespace-pre-wrap pt-1">{item.note}</p>
              </div>
            );
          })
        )}
      </div>

      {/* Add Note Form */}
      <form onSubmit={handleSubmit} className="pt-2 border-t border-matte-800 space-y-2">
        <label htmlFor="note-input" className="block text-[11px] font-medium text-matte-400">
          Add an investigation note:
        </label>
        <textarea
          id="note-input"
          rows={3}
          value={newNote}
          onChange={(e) => setNewNote(e.target.value)}
          placeholder="Document triage actions, forensic findings, or mitigation steps..."
          maxLength={2000}
          className="input-matte w-full text-xs resize-none"
        />
        <div className="flex items-center justify-between pt-1">
          <span className="text-[10px] text-matte-500 font-mono">
            {newNote.length}/2000 chars
          </span>
          <button
            type="submit"
            disabled={isSubmitting || !newNote.trim()}
            className="btn-primary text-xs py-1.5 px-3 flex items-center gap-1.5 disabled:opacity-50"
          >
            <Send className="w-3 h-3" />
            <span>{isSubmitting ? 'Saving...' : 'Add Note'}</span>
          </button>
        </div>
        {errorMsg && <p className="text-xs text-pastel-rose-light">{errorMsg}</p>}
      </form>
    </div>
  );
}

export default AlertNotes;
