import { notFound } from "next/navigation";
import { ArrowLeft, ExternalLink, Mail, Phone, MapPin, Target, Briefcase, DollarSign } from "lucide-react";
import Link from "next/link";
import { createClient } from "@/utils/supabase/server";

interface LeadDetailPageProps {
  params: Promise<{ id: string }>;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default async function LeadDetailPage({ params }: LeadDetailPageProps) {
  const { id } = await params;

  const supabase = await createClient();
  const { data: { session } } = await supabase.auth.getSession();

  if (!session) {
    notFound();
  }

  let lead;

  try {
    // Call backend directly with server-side token instead of api-client
    const response = await fetch(`${API_BASE_URL}/api/leads/${id}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
      },
      cache: 'no-store',
    });

    if (!response.ok) {
      notFound();
    }

    const data = await response.json();
    lead = data.data?.lead; // LeadDetailResponse → data → LeadWithOutreach → lead

    if (!lead) {
      notFound();
    }
  } catch (error) {
    console.error("Error fetching lead:", error);
    notFound();
  }

  return (
    <div className="min-h-screen bg-[#0A0A0A] text-gray-100 p-8 md:p-12 font-sans">
      <Link
        href="/"
        className="inline-flex items-center text-gray-500 hover:text-[#DC2626] transition-colors mb-10 group"
      >
        <ArrowLeft className="w-5 h-5 mr-2 group-hover:-translate-x-1 transition-transform" />
        Back to Dashboard
      </Link>

      <div className="max-w-5xl mx-auto space-y-8">
        {/* Header Section */}
        <header className="flex flex-col md:flex-row md:justify-between md:items-start gap-6 border-b border-gray-800 pb-8">
          <div>
            <h1 className="text-4xl md:text-5xl font-bold tracking-tight mb-3 text-white">
              {lead.business_name}
            </h1>
            <div className="flex flex-wrap items-center gap-3 text-gray-400 text-lg">
              <span className="bg-gray-800 px-3 py-1 rounded-full text-sm font-medium text-gray-200">
                {lead.business_type}
              </span>
              <span>•</span>
              <div className="flex items-center gap-1.5">
                <MapPin className="w-4 h-4" />
                {lead.city}, {lead.country}
              </div>
            </div>
          </div>

          <div className="bg-[#DC2626]/10 border border-[#DC2626]/20 text-[#DC2626] px-6 py-3 rounded-xl flex items-center gap-3">
            <Target className="w-6 h-6" />
            <div>
              <div className="text-xs font-semibold uppercase tracking-wider text-[#DC2626]/80">Opportunity</div>
              <div className="text-2xl font-bold text-white">{lead.opportunity_score}/10</div>
            </div>
          </div>
        </header>

        {/* Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

          {/* Main Info */}
          <div className="lg:col-span-2 space-y-8">
            <section className="bg-[#111111] border border-gray-800 rounded-2xl p-8">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <Briefcase className="w-5 h-5 text-[#DC2626]" />
                Business Overview
              </h2>
              <p className="text-gray-400 leading-relaxed text-lg">
                {lead.business_description || "No description available for this business."}
              </p>
            </section>

            <section className="bg-[#111111] border border-gray-800 rounded-2xl p-8">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <Target className="w-5 h-5 text-[#DC2626]" />
                Identified Pain Point
              </h2>
              <div className="bg-[#DC2626]/5 border border-[#DC2626]/10 p-6 rounded-xl">
                <p className="text-white text-lg font-medium leading-relaxed">
                  {lead.identified_problem}
                </p>
              </div>
            </section>

            {/* Website Benefits */}
            {lead.website_benefits && lead.website_benefits.length > 0 && (
              <section className="bg-[#111111] border border-gray-800 rounded-2xl p-8">
                <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                  <Target className="w-5 h-5 text-[#DC2626]" />
                  Website Benefits
                </h2>
                <ul className="space-y-2">
                  {lead.website_benefits.map((benefit: string, index: number) => (
                    <li key={index} className="flex items-start gap-2 text-gray-300">
                      <span className="text-[#DC2626] mt-1">•</span>
                      {benefit}
                    </li>
                  ))}
                </ul>
              </section>
            )}
          </div>

          {/* Sidebar */}
          <aside className="space-y-8">
            <section className="bg-[#111111] border border-gray-800 rounded-2xl p-8">
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-6">Contact</h3>
              <div className="space-y-4">
                {lead.owner_name && (
                  <div className="flex items-center gap-3 text-gray-300">
                    <span className="text-[#DC2626] font-medium">Owner:</span>
                    {lead.owner_name}
                  </div>
                )}
                <div className="flex items-center gap-3 text-gray-300">
                  <MapPin className="w-5 h-5 text-[#DC2626]" />
                  {lead.address}
                </div>
                <div className="flex items-center gap-3 text-gray-300">
                  <Mail className="w-5 h-5 text-[#DC2626]" />
                  {lead.email || "N/A"}
                </div>
                <div className="flex items-center gap-3 text-gray-300">
                  <Phone className="w-5 h-5 text-[#DC2626]" />
                  {lead.phone}
                </div>
                {lead.google_maps_url && (
                    <a
                    href={lead.google_maps_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 text-[#DC2626] hover:text-white transition-colors pt-2"
                  >
                    View on Maps <ExternalLink className="w-4 h-4" />
                  </a>
                )}
              </div>
            </section>

            <section className="bg-[#111111] border border-gray-800 rounded-2xl p-8">
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-6">Opportunity Value</h3>
              <div className="flex items-center gap-3 text-2xl font-bold text-white">
                <DollarSign className="w-8 h-8 text-green-500" />
                {lead.estimated_value || "N/A"}
              </div>
            </section>

            {/* Social Profiles */}
            {lead.social_profiles && Object.keys(lead.social_profiles).length > 0 && (
              <section className="bg-[#111111] border border-gray-800 rounded-2xl p-8">
                <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-6">Social Profiles</h3>
                <div className="space-y-3">
                  {Object.entries(lead.social_profiles).map(([platform, url]) => (
                    <a
                      key={platform}
                      href={url as string}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 text-[#DC2626] hover:text-white transition-colors capitalize"
                    >
                      <ExternalLink className="w-4 h-4" />
                      {platform}
                    </a>
                  ))}
                </div>
              </section>
            )}
          </aside>
        </div>
      </div>
    </div>
  );
}