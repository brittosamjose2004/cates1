import React from 'react';
import {
  FileText,
  Upload,
  Building2,
  Banknote,
  Leaf,
  Search,
  Globe,
  Edit,
  Calculator,
  HelpCircle,
  History,
  TrendingUp
} from 'lucide-react';

interface SourceDetails {
  display_name?: string;
  name?: string;  // API returns 'name', component expects 'display_name'
  resource: string;
  location: string;
  method: string;
  reliability: string;
  reliability_score: number;
  icon: string;
  color: string;
  badge_text: string;
  tooltip: string;
  verification: string;
  update_frequency: string;
}

interface SourceBadgeProps {
  source_details?: SourceDetails;
  source?: string;
  className?: string;
  showTooltip?: boolean;
}

const SOURCE_ICONS = {
  document: FileText,
  upload: Upload,
  industry: Building2,
  bank: Banknote,
  leaf: Leaf,
  search: Search,
  globe: Globe,
  edit: Edit,
  calculator: Calculator,
  question: HelpCircle,
  history: History,
  'trending-up': TrendingUp
};

const SOURCE_COLORS = {
  green: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  blue: 'bg-blue-100 text-blue-800 border-blue-200',
  purple: 'bg-purple-100 text-purple-800 border-purple-200',
  gold: 'bg-amber-100 text-amber-800 border-amber-200',
  amber: 'bg-amber-100 text-amber-800 border-amber-200',
  orange: 'bg-orange-100 text-orange-800 border-orange-200',
  teal: 'bg-teal-100 text-teal-800 border-teal-200',
  gray: 'bg-gray-100 text-gray-800 border-gray-200',
};

const RELIABILITY_COLORS = {
  'VERY HIGH': 'bg-emerald-500',
  'HIGH': 'bg-green-500',
  'MEDIUM': 'bg-amber-500',
  'LOW': 'bg-orange-500',
  'UNKNOWN': 'bg-gray-500'
};

export const SourceBadge: React.FC<SourceBadgeProps> = ({
  source_details,
  source,
  className = '',
  showTooltip = true
}) => {
  // Use enhanced source details when available
  if (source_details) {
    const IconComponent = SOURCE_ICONS[source_details.icon as keyof typeof SOURCE_ICONS] || HelpCircle;
    const colorClass = SOURCE_COLORS[source_details.color as keyof typeof SOURCE_COLORS] || SOURCE_COLORS.gray;
    const reliabilityColor = RELIABILITY_COLORS[source_details.reliability as keyof typeof RELIABILITY_COLORS] || RELIABILITY_COLORS.UNKNOWN;

    return (
      <div className={`group relative inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full border ${colorClass} ${className}`}>
        <IconComponent className="w-3 h-3" />
        <div className="flex flex-col items-start">
          <span className="font-medium">{source_details.display_name || source_details.name}</span>
          <span className="text-xs opacity-75 font-mono truncate max-w-[200px]" title={source_details.location}>
            📍 {source_details.location}
          </span>
        </div>
        <div className={`w-2 h-2 rounded-full ${reliabilityColor}`}></div>

        {showTooltip && (
          <div className="invisible group-hover:visible absolute bottom-full left-0 mb-2 w-80 bg-slate-900 text-white text-xs rounded-lg shadow-xl z-50 p-3 opacity-0 group-hover:opacity-100 transition-all duration-200">
            <div className="absolute top-full left-4 border-4 border-transparent border-t-slate-900"></div>

            {/* Source Header */}
            <div className="flex items-center gap-2 mb-2 pb-2 border-b border-slate-700">
              <IconComponent className="w-4 h-4" />
              <span className="font-semibold">{source_details.display_name || source_details.name}</span>
              <span className={`ml-auto px-2 py-0.5 text-xs rounded-full text-white ${reliabilityColor}`}>
                {source_details.reliability}
              </span>
            </div>

            {/* Source Details */}
            <div className="space-y-2">
              <div>
                <span className="text-slate-400">Resource:</span>
                <div className="text-white font-mono text-xs mt-1 break-words">
                  {source_details.resource}
                </div>
              </div>

              <div>
                <span className="text-slate-400">Location:</span>
                <div className="text-white font-mono text-xs mt-1 break-words">
                  📍 {source_details.location}
                </div>
              </div>

              <div>
                <span className="text-slate-400">Method:</span>
                <div className="text-white text-xs mt-1">
                  {source_details.method}
                </div>
              </div>

              <div className="flex justify-between pt-2 border-t border-slate-700 text-xs">
                <span className="text-slate-400">Reliability:</span>
                <span className="text-white font-semibold">{source_details.reliability_score}%</span>
              </div>

              <div className="flex justify-between text-xs">
                <span className="text-slate-400">Updates:</span>
                <span className="text-white">{source_details.update_frequency}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // Fallback handling for specific source types (when source_details not available)

  // Enhanced Company Research (NEW)
  if (source === 'enhanced_company_research') {
    return (
      <div className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full border bg-slate-100 text-slate-800 border-slate-200">
        <Building2 className="w-3 h-3" />
        <div className="flex flex-col items-start">
          <span>Company Research</span>
          <span className="text-xs opacity-75">🔍 Verified company data</span>
        </div>
        <div className="w-2 h-2 rounded-full bg-slate-500"></div>
      </div>
    );
  }

  // BRSR Annual Report Sources (NEW)
  if (source && source.includes('brsr_annual_report')) {
    return (
      <div className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full border bg-indigo-100 text-indigo-800 border-indigo-200">
        <FileText className="w-3 h-3" />
        <div className="flex flex-col items-start">
          <span>BRSR Annual Report</span>
          <span className="text-xs opacity-75">📊 Official company disclosure</span>
        </div>
        <div className="w-2 h-2 rounded-full bg-indigo-500"></div>
      </div>
    );
  }

  // Dynamic IT Industry Patterns (NEW)
  if (source === 'dynamic_it_industry_patterns') {
    return (
      <div className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full border bg-purple-100 text-purple-800 border-purple-200">
        <Building2 className="w-3 h-3" />
        <div className="flex flex-col items-start">
          <span>Dynamic IT Patterns</span>
          <span className="text-xs opacity-75">🌐 Real-time web scraped</span>
        </div>
        <div className="w-2 h-2 rounded-full bg-purple-500"></div>
      </div>
    );
  }

  // Dynamic Financial Patterns (NEW)
  if (source === 'dynamic_financial_sector_patterns') {
    return (
      <div className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full border bg-amber-100 text-amber-800 border-amber-200">
        <Banknote className="w-3 h-3" />
        <div className="flex flex-col items-start">
          <span>Dynamic Financial</span>
          <span className="text-xs opacity-75">🌐 Banking sector data</span>
        </div>
        <div className="w-2 h-2 rounded-full bg-amber-500"></div>
      </div>
    );
  }

  // Dynamic Sustainability Patterns (NEW)
  if (source === 'dynamic_sustainability_patterns') {
    return (
      <div className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full border bg-green-100 text-green-800 border-green-200">
        <Leaf className="w-3 h-3" />
        <div className="flex flex-col items-start">
          <span>Dynamic ESG</span>
          <span className="text-xs opacity-75">🌐 Live sustainability data</span>
        </div>
        <div className="w-2 h-2 rounded-full bg-green-500"></div>
      </div>
    );
  }

  // Website Comprehensive Enhanced (NEW)
  if (source === 'website_comprehensive_enhanced') {
    return (
      <div className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full border bg-blue-100 text-blue-800 border-blue-200">
        <Globe className="w-3 h-3" />
        <div className="flex flex-col items-start">
          <span>Enhanced Website</span>
          <span className="text-xs opacity-75">🌐 Company website scan</span>
        </div>
        <div className="w-2 h-2 rounded-full bg-blue-500"></div>
      </div>
    );
  }

  // Ultra Enhanced Sources (NEW)
  if (source && source.includes('ultra_enhanced')) {
    return (
      <div className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full border bg-emerald-100 text-emerald-800 border-emerald-200">
        <TrendingUp className="w-3 h-3" />
        <div className="flex flex-col items-start">
          <span>Ultra Enhanced</span>
          <span className="text-xs opacity-75">🚀 8-method extraction</span>
        </div>
        <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
      </div>
    );
  }

  // PDF Document Extraction
  if (source === 'real_pdf_extraction') {
    return (
      <div className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full border bg-emerald-100 text-emerald-800 border-emerald-200">
        <FileText className="w-3 h-3" />
        <div className="flex flex-col items-start">
          <span>PDF Document</span>
          <span className="text-xs opacity-75">📍 data/annual_reports/Infosys/</span>
        </div>
        <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
      </div>
    );
  }

  // IT Industry Standards
  if (source === 'it_industry_patterns') {
    return (
      <div className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full border bg-purple-100 text-purple-800 border-purple-200">
        <Building2 className="w-3 h-3" />
        <div className="flex flex-col items-start">
          <span>IT Standards</span>
          <span className="text-xs opacity-75">📍 IT compliance frameworks</span>
        </div>
        <div className="w-2 h-2 rounded-full bg-purple-500"></div>
      </div>
    );
  }

  // Financial Compliance
  if (source === 'financial_sector_patterns') {
    return (
      <div className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full border bg-amber-100 text-amber-800 border-amber-200">
        <Banknote className="w-3 h-3" />
        <div className="flex flex-col items-start">
          <span>Financial Compliance</span>
          <span className="text-xs opacity-75">📍 Financial sector ESG</span>
        </div>
        <div className="w-2 h-2 rounded-full bg-amber-500"></div>
      </div>
    );
  }

  // Sustainability Standards
  if (source === 'sustainability_patterns') {
    return (
      <div className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full border bg-green-100 text-green-800 border-green-200">
        <Leaf className="w-3 h-3" />
        <div className="flex flex-col items-start">
          <span>ESG Standards</span>
          <span className="text-xs opacity-75">📍 GRI, CDP, TCFD</span>
        </div>
        <div className="w-2 h-2 rounded-full bg-green-500"></div>
      </div>
    );
  }

  // Document Mining
  if (source === 'document_mining_patterns') {
    return (
      <div className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full border bg-blue-100 text-blue-800 border-blue-200">
        <Search className="w-3 h-3" />
        <div className="flex flex-col items-start">
          <span>Document Mining</span>
          <span className="text-xs opacity-75">📍 Governance filings</span>
        </div>
        <div className="w-2 h-2 rounded-full bg-blue-500"></div>
      </div>
    );
  }

  // Generic web scraped (fallback for actual web scraping)
  if (source === 'scraped') {
    return (
      <div className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full border bg-blue-100 text-blue-800 border-blue-200">
        <Globe className="w-3 h-3" />
        <div className="flex flex-col items-start">
          <span>Web Scraped</span>
          <span className="text-xs opacity-75">📍 Company websites</span>
        </div>
        <div className="w-2 h-2 rounded-full bg-blue-500"></div>
      </div>
    );
  }

  // Unavailable data
  if (source === 'none' || source === 'unavailable') {
    return (
      <div className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full border bg-gray-100 text-gray-600 border-gray-200">
        <HelpCircle className="w-3 h-3" />
        <span>Unavailable</span>
        <div className="w-2 h-2 rounded-full bg-gray-500"></div>
      </div>
    );
  }

  // Fallback for any unknown sources
  return (
    <span className={`inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-600 ${className}`}>
      {source || 'Unknown'}
    </span>
  );
};

export default SourceBadge;