'use client';

import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import type { Lead, Outreach } from '@/types';
import { updateOutreach } from '@/lib/api'; // Import update function

interface OutreachModalProps {
  lead: Lead;
  outreach: Outreach | null;
  onClose: () => void;
  onRegenerate: (leadId: string, tone?: 'friendly' | 'professional' | 'casual') => Promise<void>;
  onSend: (leadId: string) => Promise<void>;
  onUpdate: (updated: Outreach) => void; // New callback
}

export default function OutreachModal({
  lead,
  outreach,
  onClose,
  onRegenerate,
  onSend,
  onUpdate,
}: OutreachModalProps) {
  const [mounted, setMounted] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [sending, setSending] = useState(false);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editSubject, setEditSubject] = useState('');
  const [editMessage, setEditMessage] = useState('');
  const [selectedTone, setSelectedTone] = useState<'friendly' | 'professional' | 'casual'>(
    'professional'
  );

  useEffect(() => {
    setMounted(true);
    if (outreach) {
      setEditSubject(outreach.subject);
      setEditMessage(outreach.message);
    }
    return () => setMounted(false);
  }, [outreach]);

  const handleSaveEdit = async () => {
    if (!outreach) return;
    setSaving(true);
    try {
      const updated = await updateOutreach(outreach.id, {
        subject: editSubject,
        message: editMessage,
      });
      onUpdate(updated);
      setEditing(false);
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const handleRegenerate = async () => {
    setRegenerating(true);
    try {
      await onRegenerate(lead.id, selectedTone);
    } finally {
      setRegenerating(false);
    }
  };

  const handleSend = async () => {
    if (!lead.email || !outreach) return;

    setSending(true);
    try {
      await onSend(outreach.id);
    } finally {
      setSending(false);
    }
  };

  const getToneBadgeColor = (tone: string) => {
    switch (tone) {
      case 'friendly':
        return 'bg-green-500/20 text-green-400';
      case 'professional':
        return 'bg-blue-500/20 text-blue-400';
      case 'casual':
        return 'bg-purple-500/20 text-purple-400';
      default:
        return 'bg-gray-500/20 text-gray-400';
    }
  };

  const modalContent = (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="bg-gray-800 rounded-lg shadow-2xl border border-gray-700 w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-700 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-white">Outreach Email</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
            aria-label="Close modal"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {!outreach ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-center">
                <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4" />
                <p className="text-gray-400">Loading outreach...</p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Business Info */}
              <div className="bg-gray-700/50 rounded-lg p-4">
                <h3 className="font-semibold text-white mb-2">{lead.business_name}</h3>
                <div className="text-sm text-gray-300 space-y-1">
                  <p>{lead.city}</p>
                  {lead.email && <p>To: {lead.email}</p>}
                </div>
              </div>

              {/* Tone Badge */}
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-400">Tone:</span>
                <span
                  className={`text-xs px-3 py-1 rounded-full ${getToneBadgeColor(
                    outreach.tone
                  )}`}
                >
                  {outreach.tone}
                </span>
                {outreach.sent && (
                  <span className="text-xs px-3 py-1 rounded-full bg-green-500/20 text-green-400 ml-2">
                    Sent ✓
                  </span>
                )}
              </div>

              {/* Subject */}
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">Subject</label>
                {editing ? (
                  <input
                    value={editSubject}
                    onChange={(e) => setEditSubject(e.target.value)}
                    className="w-full bg-gray-700 text-white rounded-lg p-3 border border-gray-600 focus:border-blue-500 focus:outline-none"
                  />
                ) : (
                  <p className="text-xl font-semibold text-white">{outreach.subject}</p>
                )}
              </div>

              {/* Message */}
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">Message</label>
                <div className="bg-gray-700/50 rounded-lg p-4">
                  {editing ? (
                    <textarea
                      value={editMessage}
                      onChange={(e) => setEditMessage(e.target.value)}
                      rows={10}
                      className="w-full bg-transparent text-gray-200 resize-none focus:outline-none leading-relaxed"
                    />
                  ) : (
                    <p className="text-gray-200 whitespace-pre-wrap leading-relaxed">
                      {outreach.message}
                    </p>
                  )}
                </div>
              </div>

              {/* Tone Selector for Regenerate */}
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Select Tone for Regeneration
                </label>
                <div className="flex gap-2">
                  {(['friendly', 'professional', 'casual'] as const).map((tone) => (
                    <button
                      key={tone}
                      onClick={() => setSelectedTone(tone)}
                      className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors capitalize ${
                        selectedTone === tone
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                      }`}
                    >
                      {tone}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-700 flex gap-3">
          {editing ? (
            <button
              onClick={handleSaveEdit}
              disabled={saving}
              className="flex-1 bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          ) : (
            <button
              onClick={() => setEditing(true)}
              className="flex-1 bg-gray-700 hover:bg-gray-600 text-white font-medium py-2 px-4 rounded-lg transition-colors"
            >
              Edit Email
            </button>
          )}
          
          {!editing && (
            <>
              <button
                onClick={handleRegenerate}
                disabled={regenerating || !outreach}
                className="flex-1 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:cursor-not-allowed text-white font-medium py-2 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                {regenerating ? (
                  <>
                    <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                    <span>Regenerating...</span>
                  </>
                ) : (
                  <span>Regenerate</span>
                )}
              </button>

              <button
                onClick={handleSend}
                disabled={sending || !outreach || !lead.email || outreach?.sent}
                title={!lead.email ? 'No email found' : outreach?.sent ? 'Already sent' : ''}
                className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-medium py-2 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                {sending ? (
                  <>
                    <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                    <span>Sending...</span>
                  </>
                ) : outreach?.sent ? (
                  <span>Sent ✓</span>
                ) : (
                  <span>Send Email</span>
                )}
              </button>
            </>
          )}

          <button
            onClick={editing ? () => setEditing(false) : onClose}
            className="bg-gray-700 hover:bg-gray-600 text-white font-medium py-2 px-4 rounded-lg transition-colors"
          >
            {editing ? 'Cancel' : 'Close'}
          </button>
        </div>
      </div>
    </div>
  );

  if (!mounted) return null;

  return createPortal(modalContent, document.body);
}
