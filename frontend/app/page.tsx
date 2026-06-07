'use client';

import { useState, useEffect } from 'react';
import type { Lead, Outreach, SearchRequest } from '@/types';
import { getLeads, searchLeads, deleteLead, getOutreach, regenerateOutreach, sendOutreach } from '@/lib/api';
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
  const [stats, setStats] = useState({
    total: 0,
    avgScore: 0,
    highScoreCount: 0,
  });

  useEffect(() => {
    loadInitialLeads();
  }, []);

  useEffect(() => {
    calculateStats();
  }, [leads]);

  const loadInitialLeads = async () => {
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
  };

  const calculateStats = () => {
    const total = leads.length;
    const avgScore = total > 0 ? leads.reduce((sum, lead) => sum + lead.opportunity_score, 0) / total : 0;
    const highScoreCount = leads.filter((lead) => lead.opportunity_score >= 8).length;

    setStats({
      total,
      avgScore,
      highScoreCount,
    });
  };

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

      // Poll for completion — AgentProgress owns the SSE UI, we just reload leads when done
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const eventSource = new EventSource(`${API_BASE_URL}/api/status/${result.job_id}/stream`);

      eventSource.addEventListener('progress', (event) => {
        const data = JSON.parse(event.data);
        if (data.status === 'completed') {
          eventSource.close();
          setTimeout(async () => {
            setSearching(false);
            setActiveJobId(null);
            // Reload leads from DB to pick up the new ones
            try {
              const freshLeads = await getLeads();
              setLeads(freshLeads);
            } catch {
              setError('Pipeline finished but failed to refresh leads.');
            }
          }, 1200);
        }
      });

      eventSource.onerror = () => {
        eventSource.close();
        setError('Error during real-time progress tracking');
        setSearching(false);
        setActiveJobId(null);
      };

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

      // Update the outreach to show it's been sent
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
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">AI Lead Generator</h1>
          <p className="text-gray-400">
            Discover local businesses and generate personalized outreach emails
          </p>
        </header>

        {error && (
          <div className="bg-red-500/10 border border-red-500 rounded-lg p-4 mb-6">
            <p className="text-red-500">{error}</p>
            <button
              onClick={() => setError(null)}
              className="text-red-400 hover:text-red-300 text-sm mt-2 underline"
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
              <div className="animate-spin h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4" />
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
