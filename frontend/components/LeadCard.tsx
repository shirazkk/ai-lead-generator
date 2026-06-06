'use client';

import type { Lead } from '@/types';

interface LeadCardProps {
  lead: Lead;
  onViewOutreach: (lead: Lead) => void;
  onDelete: (leadId: string) => void;
}

export default function LeadCard({ lead, onViewOutreach, onDelete }: LeadCardProps) {
  const getScoreColor = (score: number) => {
    if (score >= 8) return 'bg-green-500';
    if (score >= 5) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const handleDelete = () => {
    if (confirm(`Are you sure you want to delete ${lead.business_name}?`)) {
      onDelete(lead.id);
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6 shadow-lg border border-gray-700 hover:bg-gray-750 transition-colors duration-200">
      <div className="flex items-start justify-between mb-3">
        <h3 className="text-xl font-bold text-white flex-1">{lead.business_name}</h3>
        <span
          className={`${getScoreColor(
            lead.opportunity_score
          )} text-white text-sm font-bold px-3 py-1 rounded-full ml-2`}
        >
          {lead.opportunity_score}/10
        </span>
      </div>

      <div className="space-y-2 mb-4">
        <div className="flex items-center gap-2 text-gray-300 text-sm">
          <span className="text-gray-400">📍</span>
          <span>{lead.city}</span>
        </div>

        <div className="flex items-center gap-2 text-gray-300 text-sm">
          <span className="text-gray-400">🏢</span>
          <span>{lead.business_type}</span>
        </div>

        <div className="flex items-center gap-2 text-gray-300 text-sm">
          <span className="text-gray-400">📞</span>
          <span>{lead.phone}</span>
        </div>

        {lead.email ? (
          <div className="flex items-center gap-2 text-gray-300 text-sm">
            <span className="text-gray-400">✉️</span>
            <span>{lead.email}</span>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-sm">
            <span className="bg-gray-700 text-gray-400 px-2 py-1 rounded text-xs">
              No email found
            </span>
          </div>
        )}
      </div>

      <div className="mb-4">
        <p className="text-gray-400 text-sm font-medium mb-1">Identified Problem:</p>
        <p className="text-gray-300 text-sm line-clamp-2">{lead.identified_problem}</p>
      </div>

      {lead.website_status && (
        <div className="mb-4">
          <span
            className={`inline-block text-xs px-2 py-1 rounded ${
              lead.website_status === 'none'
                ? 'bg-red-500/20 text-red-400'
                : lead.website_status === 'outdated'
                ? 'bg-yellow-500/20 text-yellow-400'
                : 'bg-orange-500/20 text-orange-400'
            }`}
          >
            Website: {lead.website_status}
          </span>
        </div>
      )}

      <div className="flex gap-2">
        <button
          onClick={() => onViewOutreach(lead)}
          className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200"
        >
          View Outreach
        </button>
        <button
          onClick={handleDelete}
          className="bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200"
        >
          Delete
        </button>
      </div>
    </div>
  );
}
