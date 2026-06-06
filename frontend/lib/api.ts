import type {
  Lead,
  Outreach,
  SearchRequest,
  SearchResponse,
  ApiResponse,
  ApiError,
} from '@/types';

const API_BASE_URL = 'http://localhost:8000';

class ApiClient {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          success: false,
          error: {
            type: data.error?.type || 'API_ERROR',
            message: data.error?.message || 'An error occurred',
            details: data.error?.details,
          },
        };
      }

      return {
        success: true,
        data,
      };
    } catch (error) {
      return {
        success: false,
        error: {
          type: 'NETWORK_ERROR',
          message: error instanceof Error ? error.message : 'Network request failed',
          details: error,
        },
      };
    }
  }

  async searchLeads(request: SearchRequest): Promise<ApiResponse<SearchResponse>> {
    return this.request<SearchResponse>('/api/search', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getLeads(): Promise<ApiResponse<Lead[]>> {
    const response = await this.request<{ data: Lead[] }>('/api/leads', {
      method: 'GET',
    });

    if (response.success && response.data) {
      return {
        success: true,
        data: response.data.data,
      };
    }

    return response as ApiResponse<Lead[]>;
  }

  async getLead(leadId: string): Promise<ApiResponse<Lead>> {
    return this.request<Lead>(`/api/leads/${leadId}`, {
      method: 'GET',
    });
  }

  async deleteLead(leadId: string): Promise<ApiResponse<{ message: string }>> {
    return this.request<{ message: string }>(`/api/leads/${leadId}`, {
      method: 'DELETE',
    });
  }

  async getOutreach(leadId: string): Promise<ApiResponse<Outreach>> {
    const response = await this.request<{ data: Outreach }> (`/api/outreach/${leadId}`, {
      method: 'GET',
    });

    if (response.success && response.data) {
      return {
        success: true,
        data: response.data.data,
      };
    }

    return response as ApiResponse<Outreach>;
  }

  async regenerateOutreach(
    leadId: string,
    tone?: 'friendly' | 'professional' | 'casual'
  ): Promise<ApiResponse<Outreach>> {
    const url = tone
      ? `/api/outreach/${leadId}/regenerate?tone=${tone}`
      : `/api/outreach/${leadId}/regenerate`;

    const response = await this.request<{ data: Outreach }>(url, {
      method: 'POST',
    });

    if (response.success && response.data) {
      return {
        success: true,
        data: response.data.data,
      };
    }

    return response as ApiResponse<Outreach>;
  }

  async sendOutreach(outreachId: string): Promise<ApiResponse<{ message: string; sent: boolean }>> {
    return this.request<{ message: string; sent: boolean }>(`/api/outreach/send/${outreachId}`, {
      method: 'POST',
    });
  }

  async updateOutreach(
    outreachId: string,
    data: { subject: string; message: string }
  ): Promise<ApiResponse<Outreach>> {
    const response = await this.request<{ data: Outreach }>(`/api/outreach/${outreachId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });

    if (response.success && response.data) {
      return {
        success: true,
        data: response.data.data,
      };
    }

    return response as ApiResponse<Outreach>;
  }


  async getStats(): Promise<ApiResponse<{
    total: number;
    avg_score: number;
    high_score_count: number;
  }>> {
    return this.request('/api/leads/stats', {
      method: 'GET',
    });
  }
}

export const api = new ApiClient();

export async function searchLeads(request: SearchRequest): Promise<SearchResponse> {
  const response = await api.searchLeads(request);

  if (!response.success || !response.data) {
    throw new Error(response.error?.message || 'Failed to search leads');
  }

  return response.data;
}

export async function getLeads(): Promise<Lead[]> {
  const response = await api.getLeads();

  if (!response.success || !response.data) {
    throw new Error(response.error?.message || 'Failed to fetch leads');
  }

  return response.data;
}

export async function getLead(leadId: string): Promise<Lead> {
  const response = await api.getLead(leadId);

  if (!response.success || !response.data) {
    throw new Error(response.error?.message || 'Failed to fetch lead');
  }

  return response.data;
}

export async function deleteLead(leadId: string): Promise<void> {
  const response = await api.deleteLead(leadId);

  if (!response.success) {
    throw new Error(response.error?.message || 'Failed to delete lead');
  }
}

export async function getOutreach(leadId: string): Promise<Outreach> {
  const response = await api.getOutreach(leadId);

  if (!response.success || !response.data) {
    throw new Error(response.error?.message || 'Failed to fetch outreach');
  }

  return response.data;
}

export async function regenerateOutreach(
  leadId: string,
  tone?: 'friendly' | 'professional' | 'casual'
): Promise<Outreach> {
  const response = await api.regenerateOutreach(leadId, tone);

  if (!response.success || !response.data) {
    throw new Error(response.error?.message || 'Failed to regenerate outreach');
  }

  return response.data;
}

export async function updateOutreach(
  outreachId: string,
  data: { subject: string; message: string }
): Promise<Outreach> {
  const response = await api.updateOutreach(outreachId, data);

  if (!response.success || !response.data) {
    throw new Error(response.error?.message || 'Failed to update outreach');
  }

  return response.data;
}

export async function sendOutreach(outreachId: string): Promise<{ message: string; sent: boolean }> {
  const response = await api.sendOutreach(outreachId);

  if (!response.success || !response.data) {
    throw new Error(response.error?.message || 'Failed to send outreach');
  }

  return response.data;
}

