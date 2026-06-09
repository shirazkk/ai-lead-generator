'use client';

import type { Lead } from '@/types';
import Link from 'next/link';

interface LeadCardProps {
  lead: Lead;
  onDelete: (leadId: string) => void;
}

export default function LeadCard({ lead, onDelete }: LeadCardProps) {
  const getScoreColor = (score: number) => {
    if (score >= 8) return 'text-emerald-400';
    if (score >= 5) return 'text-amber-400';
    return 'text-rose-400';
  };

  return (
    <div className="bg-surface rounded-xl p-6 border border-surface transition-all duration-300 hover:border-zinc-700 hover:shadow-2xl">
      <div className="flex items-start justify-between mb-5">
        <h3 className="text-lg font-semibold text-text-primary tracking-tight">{lead.business_name}</h3>
        <span className={`font-mono text-sm font-medium ${getScoreColor(lead.opportunity_score)} bg-zinc-900 px-2.5 py-0.5 rounded border border-zinc-800`}>
          Score: {lead.opportunity_score}
        </span>
      </div>

      <div className="space-y-3 mb-6">
        <InfoItem icon="📍" label={lead.city} />
        <InfoItem icon="🏢" label={lead.business_type} />
        <InfoItem icon="📞" label={lead.phone} />
      </div>

      <div className="mb-6">
        <p className="text-zinc-500 text-xs uppercase tracking-wider font-semibold mb-2">Analysis</p>
        <p className="text-text-secondary text-sm leading-relaxed line-clamp-2">{lead.identified_problem}</p>
      </div>

      <div className="flex gap-3 pt-4 border-t border-surface">
        <Link
          href={`/leads/${lead.id}`}
          className="flex-1 bg-white hover:bg-zinc-200 text-black text-center text-sm font-medium py-2 rounded-md transition-colors"
        >
          View Details
        </Link>
        <button
          onClick={() => onDelete(lead.id)}
          className="text-zinc-500 hover:text-rose-400 text-sm font-medium px-4 py-2 transition-colors"
        >
          Delete
        </button>
      </div>
    </div>
  );
}

function InfoItem({ icon, label }: { icon: string; label: string | null }) {
  if (!label) return null;
  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="opacity-50">{icon}</span>
      <span className="text-zinc-400">{label}</span>
    </div>
  );
}
