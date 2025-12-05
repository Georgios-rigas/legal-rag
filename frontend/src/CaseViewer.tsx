import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Download, Calendar, Scale, FileText, Users } from 'lucide-react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

interface Opinion {
  author?: string;
  type?: string;
  text?: string;
}

interface CaseData {
  case_id: number;
  name: string;
  name_abbreviation: string;
  citation: string;
  court: string;
  decision_date: string;
  docket_number: string;
  opinions: Opinion[];
  attorneys: string[];
  judges: string[];
  parties: string[];
}

export default function CaseViewer() {
  const { caseId } = useParams<{ caseId: string }>();
  const navigate = useNavigate();
  const [caseData, setCaseData] = useState<CaseData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCase = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await axios.get(`${API_BASE_URL}/api/case/${caseId}`);
        setCaseData(response.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load case content');
        console.error('Error fetching case:', err);
      } finally {
        setLoading(false);
      }
    };

    if (caseId) {
      fetchCase();
    }
  }, [caseId]);

  const handleDownload = () => {
    window.open(`${API_BASE_URL}/api/download/${caseId}`, '_blank');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#0a1929] via-[#0d2438] to-[#0a1929]">
        <div className="max-w-6xl mx-auto px-4 py-8">
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400 mx-auto mb-4"></div>
              <p className="text-gray-400">Loading case...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !caseData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#0a1929] via-[#0d2438] to-[#0a1929]">
        <div className="max-w-6xl mx-auto px-4 py-8">
          <button
            onClick={() => navigate('/')}
            className="mb-6 flex items-center gap-2 text-blue-400 hover:text-blue-300 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            Back to Search
          </button>
          <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-6 text-center">
            <p className="text-red-400">{error || 'Case not found'}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a1929] via-[#0d2438] to-[#0a1929]">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-2 text-blue-400 hover:text-blue-300 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            Back to Search
          </button>
          <button
            onClick={handleDownload}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            <Download className="w-4 h-4" />
            Download PDF
          </button>
        </div>

        {/* Case Card */}
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 shadow-2xl">
          {/* Case Header */}
          <div className="p-6 border-b border-slate-700/50">
            <h1 className="text-2xl font-bold text-white mb-4">{caseData.name}</h1>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div className="flex items-start gap-3">
                <FileText className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-gray-400">Citation</p>
                  <p className="text-white font-medium">{caseData.citation}</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <Scale className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-gray-400">Court</p>
                  <p className="text-white font-medium">{caseData.court}</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <Calendar className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-gray-400">Decision Date</p>
                  <p className="text-white font-medium">{caseData.decision_date}</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <FileText className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-gray-400">Docket Number</p>
                  <p className="text-white font-medium">{caseData.docket_number}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Case Metadata */}
          {(caseData.judges.length > 0 || caseData.attorneys.length > 0 || caseData.parties.length > 0) && (
            <div className="p-6 border-b border-slate-700/50 bg-slate-900/30">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {caseData.judges.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <Users className="w-4 h-4 text-blue-400" />
                      <h3 className="font-semibold text-white">Judges</h3>
                    </div>
                    <ul className="text-sm text-gray-300 space-y-1">
                      {caseData.judges.map((judge, idx) => (
                        <li key={idx}>{judge}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {caseData.attorneys.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <Users className="w-4 h-4 text-blue-400" />
                      <h3 className="font-semibold text-white">Attorneys</h3>
                    </div>
                    <ul className="text-sm text-gray-300 space-y-1">
                      {caseData.attorneys.map((attorney, idx) => (
                        <li key={idx}>{attorney}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {caseData.parties.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <Users className="w-4 h-4 text-blue-400" />
                      <h3 className="font-semibold text-white">Parties</h3>
                    </div>
                    <ul className="text-sm text-gray-300 space-y-1">
                      {caseData.parties.map((party, idx) => (
                        <li key={idx}>{party}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Opinions */}
          <div className="p-6">
            <h2 className="text-xl font-bold text-white mb-4">Opinion{caseData.opinions.length > 1 ? 's' : ''}</h2>

            {caseData.opinions.length === 0 ? (
              <p className="text-gray-400 italic">No opinion text available</p>
            ) : (
              <div className="space-y-6">
                {caseData.opinions.map((opinion, idx) => (
                  <div key={idx} className="space-y-3">
                    {(opinion.author || opinion.type) && (
                      <div className="flex items-center gap-3 text-sm">
                        {opinion.author && (
                          <span className="text-blue-400 font-semibold">{opinion.author}</span>
                        )}
                        {opinion.type && (
                          <span className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs uppercase">
                            {opinion.type}
                          </span>
                        )}
                      </div>
                    )}

                    <div className="text-gray-300 leading-relaxed whitespace-pre-wrap">
                      {opinion.text || 'No text available'}
                    </div>

                    {idx < caseData.opinions.length - 1 && (
                      <div className="border-t border-slate-700/50 my-6" />
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
