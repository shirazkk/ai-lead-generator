// TypeScript interfaces matching backend Pydantic models

export interface Lead {
  id: string;
  business_name: string;
  business_type: string;
  owner_name?: string;
  email?: string;
  phone: string;
  address: string;
  city: string;
  country: string;
  google_maps_url?: string;
  social_profiles: string[];
  website_status: 'none' | 'outdated' | 'weak';
  business_description?: string;
  opportunity_score: number; // 1-10
  identified_problem: string;
  website_benefits: string[];
  estimated_value?: string;
  created_at: string;
}

export interface Outreach {
  id: string;
  lead_id: string;
  subject: string;
  message: string;
  tone: 'friendly' | 'professional' | 'casual';
  generated_at: string;
  sent: boolean;
  sent_at?: string;
}

export interface SearchRequest {
  city: string;
  business_type: string;
  count: number;
}

export interface SearchResponse {
  success: boolean;
  job_id: string;
  leads: Lead[];
  stats: {
    total: number;
    high_score_count: number;
    avg_score: number;
  };
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    type: string;
    message: string;
    details?: any;
  };
}

export interface ApiError {
  type: string;
  message: string;
  details?: any;
}
