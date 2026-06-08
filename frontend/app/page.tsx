'use client';

import { useState, useEffect, useCallback } from 'react';
import { LogOut, User } from 'lucide-react';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import type { Lead, Outreach, SearchRequest } from '@/types';
import { getLeads, searchLeads, deleteLead, getOutreach, regenerateOutreach, sendOutreach } from '@/lib/api';
import { createClient } from '@/utils/supabase/client';
import { logout } from './auth/actions';

import SearchForm from '@/components/SearchForm';
import StatsBar from '@/components/StatsBar';
import LeadCard from '@/components/LeadCard';
import AgentProgress from '@/components/AgentProgress';
import OutreachModal from '@/components/OutreachModal';

export default function Home() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [selectedOutreach, setSelectedOutreach] = useState<Outreach | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [stats, setStats] = useState({
    total: 0,
    avgScore: 0,
    highScoreCount: 0,
  });

  const calculateStats = useCallback(() => {
    const total = leads.length;
    const avgScore = total > 0 ? leads.reduce((sum, lead) => sum + lead.opportunity_score, 0) / total : 0;
    const highScoreCount = leads.filter((lead) => lead.opportunity_score >= 8).length;

    setStats({
      total,
      avgScore,
      highScoreCount,
    });
  }, [leads]);

  const loadInitialLeads = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const fetchedLeads = await getLeads();
      setLeads(fetchedLeads);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load leads');
    } finally {
      setLoading(false);
    }
  }, []);

  const getUser = useCallback(async () => {
    const supabase = createClient();
    const { data: { user } } = await supabase.auth.getUser();
    setUserEmail(user?.email || null);
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      loadInitialLeads();
      getUser();
    }, 0);
    return () => clearTimeout(timer);
  }, [loadInitialLeads, getUser]);

  useEffect(() => {
    const timer = setTimeout(() => {
      calculateStats();
    }, 0);
    return () => clearTimeout(timer);
  }, [leads, calculateStats]);

  const handleSearch = async (request: SearchRequest) => {
    setSearching(true);
    setError(null);
    setActiveJobId(null);

    try {
      const result = await searchLeads(request);
      if (!result.success || !result.job_id) {
        throw new Error('Failed to initiate search');
      }

      setActiveJobId(result.job_id);

      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      const token = session?.access_token;

      await fetchEventSource(`${API_BASE_URL}/api/status/${result.job_id}/stream`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        onmessage(event) {
          if (event.event === 'progress') {
            const data = JSON.parse(event.data);
            if (data.status === 'completed') {
              setTimeout(async () => {
                setSearching(false);
                setActiveJobId(null);
                try {
                  const freshLeads = await getLeads();
                  setLeads(freshLeads);
                } catch {
                  setError('Pipeline finished but failed to refresh leads.');
                }
              }, 1200);
            }
          }
        },
        onerror(err) {
          console.error('SSE Error:', err);
          setError('Error during real-time progress tracking');
          setSearching(false);
          setActiveJobId(null);
          throw err;
        }
      });

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
      setSearching(false);
    }
  };

  const handleViewOutreach = async (lead: Lead) => {
    setSelectedLead(lead);
    setSelectedOutreach(null);
    setShowModal(true);

    try {
      const outreach = await getOutreach(lead.id);
      setSelectedOutreach(outreach);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load outreach');
    }
  };

  const handleDeleteLead = async (leadId: string) => {
    try {
      await deleteLead(leadId);
      setLeads((prevLeads) => prevLeads.filter((lead) => lead.id !== leadId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete lead');
    }
  };

  const handleRegenerateOutreach = async (
    leadId: string,
    tone?: 'friendly' | 'professional' | 'casual'
  ) => {
    try {
      const outreach = await regenerateOutreach(leadId, tone);
      setSelectedOutreach(outreach);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to regenerate outreach');
    }
  };

  const handleSendOutreach = async (outreachId: string) => {
    try {
      await sendOutreach(outreachId);

      if (selectedOutreach) {
        setSelectedOutreach({
          ...selectedOutreach,
          sent: true,
          sent_at: new Date().toISOString(),
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send outreach');
    }
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setSelectedLead(null);
    setSelectedOutreach(null);
  };

  return (
    <main className="min-h-screen bg-gray-900 text-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        <header className="mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2 tracking-tight">
              AI Lead <span className="text-[#DC2626]">Gen</span>
            </h1>
            <p className="text-zinc-400">
              Discover local businesses and generate personalized outreach emails
            </p>
          </div>
          
          <div className="flex items-center gap-4 bg-zinc-900/50 border border-zinc-800 p-2 pl-4 rounded-2xl backdrop-blur-sm">
            <div className="flex items-center gap-2 pr-4 border-r border-zinc-800">
              <User className="w-4 h-4 text-[#DC2626]" />
              <span className="text-sm font-medium text-zinc-300 max-w-[150px] truncate">{userEmail || 'Loading...'}</span>
            </div>
            <form action={logout}>
              <button 
                type="submit"
                className="flex items-center gap-2 hover:bg-red-500/10 hover:text-red-500 p-2 px-3 rounded-xl transition-all group"
              >
                <LogOut className="w-4 h-4 group-active:scale-90 transition-transform" />
                <span className="text-sm font-semibold tracking-wide">Logout</span>
              </button>
            </form>
          </div>
        </header>

        {error && (
          <div className="bg-red-500/10 border border-red-500 rounded-lg p-4 mb-6 flex justify-between items-center">
            <p className="text-red-500">{error}</p>
            <button
              onClick={() => setError(null)}
              className="text-red-400 hover:text-red-300 text-sm underline"
            >
              Dismiss
            </button>
          </div>
        )}

        <SearchForm onSubmit={handleSearch} />

        {searching && activeJobId && <AgentProgress jobId={activeJobId} />}

        <StatsBar total={stats.total} avgScore={stats.avgScore} highScoreCount={stats.highScoreCount} />

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="animate-spin h-12 w-12 border-4 border-[#DC2626] border-t-transparent rounded-full mx-auto mb-4" />
              <p className="text-gray-400">Loading leads...</p>
            </div>
          </div>
        ) : leads.length === 0 ? (
          <div className="bg-gray-800 rounded-lg p-12 text-center border border-gray-700">
            <p className="text-xl text-gray-400 mb-2">No leads found</p>
            <p className="text-gray-500">Use the search form above to discover new leads</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {leads.map((lead) => (
              <LeadCard
                key={lead.id}
                lead={lead}
                onViewOutreach={handleViewOutreach}
                onDelete={handleDeleteLead}
              />
            ))}
          </div>
        )}
      </div>

      {showModal && selectedLead && (
        <OutreachModal
          lead={selectedLead}
          outreach={selectedOutreach}
          onClose={handleCloseModal}
          onRegenerate={handleRegenerateOutreach}
          onSend={handleSendOutreach}
          onUpdate={(updated) => setSelectedOutreach(updated)}
        />
      )}
    </main>
  );
}
