'use client';

import { useEffect, useState } from 'react';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { createClient } from '@/utils/supabase/client';

interface AgentProgressProps {
  jobId: string;
}

const STEPS = [
  { id: 0, name: 'Discovery', icon: '🔍' },
  { id: 1, name: 'Scraping', icon: '🌐' },
  { id: 2, name: 'Analysis', icon: '🧠' },
  { id: 3, name: 'Outreach', icon: '✉️' },
];

export default function AgentProgress({ jobId }: AgentProgressProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);

  useEffect(() => {
    if (!jobId) return;

    const controller = new AbortController();

    const startStreaming = async () => {
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      const token = session?.access_token;

      await fetchEventSource(`${API_BASE_URL}/api/status/${jobId}/stream`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        signal: controller.signal,
        onmessage(event) {
          if (event.event === 'progress') {
            const data = JSON.parse(event.data);
            
            if (data && data.agents) {
              const agentSteps = ['discovery', 'scraper', 'analyzer', 'outreach'];
              const completed: number[] = [];
              let current = 0;

              agentSteps.forEach((agent, index) => {
                const agentStatus = data.agents[agent];
                if (agentStatus && agentStatus.status === 'completed') {
                  completed.push(index);
                } else if (agentStatus && agentStatus.status === 'running') {
                  current = index;
                }
              });

              setCurrentStep(current);
              setCompletedSteps(completed);
            }
          }
        },
        onerror(err) {
          if (err.name === 'AbortError') {
            return;
          }
          console.error('SSE Error:', err);
          throw err;
        }
      });
    };

    startStreaming();

    return () => {
      controller.abort();
    };
  }, [jobId]);

  const getStepStatus = (stepId: number) => {
    if (completedSteps.includes(stepId)) return 'completed';
    if (stepId === currentStep) return 'in_progress';
    return 'pending';
  };

  const getStepStyles = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500 border-green-500';
      case 'in_progress':
        return 'bg-blue-500 border-blue-500 animate-pulse';
      case 'pending':
      default:
        return 'bg-gray-500 border-gray-500';
    }
  };

  const getConnectorStyles = (stepId: number) => {
    if (completedSteps.includes(stepId) && completedSteps.includes(stepId + 1)) {
      return 'bg-green-500';
    }
    if (completedSteps.includes(stepId) && stepId + 1 === currentStep) {
      return 'bg-gradient-to-r from-green-500 to-blue-500';
    }
    return 'bg-gray-500';
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6 shadow-lg border border-gray-700 mb-6">
      <h2 className="text-xl font-bold text-white mb-6">Agent Pipeline Progress</h2>

      <div className="flex items-center justify-between">
        {STEPS.map((step, index) => (
          <div key={step.id} className="flex items-center flex-1">
            <div className="flex flex-col items-center flex-shrink-0">
              <div
                className={`w-16 h-16 rounded-full border-4 flex items-center justify-center ${getStepStyles(
                  getStepStatus(step.id)
                )}`}
              >
                <span className="text-2xl">
                  {getStepStatus(step.id) === 'completed' ? '✓' : step.icon}
                </span>
              </div>
              <p className="text-sm text-gray-300 mt-2 font-medium">{step.name}</p>
              <p className="text-xs text-gray-500 mt-1 capitalize">
                {getStepStatus(step.id).replace('_', ' ')}
              </p>
            </div>

            {index < STEPS.length - 1 && (
              <div className="flex-1 h-1 mx-4">
                <div
                  className={`h-full rounded ${getConnectorStyles(step.id)}`}
                  style={{
                    transition: 'background 0.3s ease',
                  }}
                />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
