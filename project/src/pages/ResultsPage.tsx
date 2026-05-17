import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Home, Download, Loader2, Award, MessageSquare, Target, TrendingUp } from 'lucide-react';
import { API_ENDPOINTS } from '../config/api';
import type { QAPair, InterviewEvaluationResponse } from '../types';
import { generatePDF } from '../utils/pdfGenerator';

interface LocationState {
  qaList: QAPair[];
  role: string;
  resumeSummary: string;
}

const ResultsPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const state = location.state as LocationState;

  const [evaluation, setEvaluation] = useState<InterviewEvaluationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!state) {
      navigate('/');
      return;
    }
    evaluateInterview();
  }, []);

  const evaluateInterview = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.evaluateInterview, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          qa_list: state.qaList,
          role: state.role,
          resume_summary: state.resumeSummary,
        }),
      });

      if (!response.ok) throw new Error('Failed to evaluate interview');

      const data: InterviewEvaluationResponse = await response.json();
      setEvaluation(data);
      setLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to evaluate interview');
      setLoading(false);
    }
  };

  const handleDownloadPDF = () => {
    if (!evaluation) return;
    generatePDF(evaluation, state.qaList, state.role);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-16 h-16 text-[#05fcd3] animate-spin mx-auto mb-4" />
          <p className="text-white text-xl">Evaluating your interview performance...</p>
        </div>
      </div>
    );
  }

  if (error || !evaluation) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 text-xl mb-6">{error || 'No evaluation data available'}</p>
          <button
            onClick={() => navigate('/')}
            className="px-6 py-3 bg-[#05fcd3] text-black rounded-lg hover:bg-[#04dab8] transition-colors"
          >
            Return Home
          </button>
        </div>
      </div>
    );
  }

  const getScoreColor = (score?: number) => {
    if (!score) return 'text-gray-400';
    if (score >= 8) return 'text-green-400';
    if (score >= 6) return 'text-[#05fcd3]';
    if (score >= 4) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getScoreWidth = (score?: number) => {
    if (!score) return '0%';
    return `${(score / 10) * 100}%`;
  };

  return (
    <div className="min-h-screen bg-black relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-black via-gray-900 to-black">
        <div className="absolute inset-0">
          {[...Array(30)].map((_, i) => (
            <div
              key={i}
              className="absolute rounded-full bg-[#05fcd3] animate-pulse"
              style={{
                width: Math.random() * 3 + 1 + 'px',
                height: Math.random() * 3 + 1 + 'px',
                left: Math.random() * 100 + '%',
                top: Math.random() * 100 + '%',
                animationDelay: Math.random() * 3 + 's',
                animationDuration: Math.random() * 4 + 2 + 's',
              }}
            />
          ))}
        </div>
      </div>

      <div className="relative z-10 container mx-auto px-4 py-12">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <Award className="w-20 h-20 text-[#05fcd3] mx-auto mb-4 animate-pulse" />
            <h1 className="text-5xl font-bold text-white mb-3">Interview Results</h1>
            <p className="text-gray-400 text-lg">Role: {state.role}</p>
          </div>

          <div className="bg-gray-900/50 backdrop-blur-sm border border-[#05fcd3]/20 rounded-2xl p-8 shadow-2xl mb-6">
            <div className="text-center mb-8">
              <p className="text-gray-400 mb-2">Final Score</p>
              <div className="text-7xl font-bold text-[#05fcd3] mb-2">
                {evaluation.final_score?.toFixed(1) || 'N/A'}
                {evaluation.final_score && <span className="text-3xl">/10</span>}
              </div>
            </div>

            <div className="grid md:grid-cols-3 gap-6 mb-8">
              <div className="bg-black/50 border border-[#05fcd3]/30 rounded-lg p-6">
                <div className="flex items-center gap-3 mb-3">
                  <Target className="w-6 h-6 text-[#05fcd3]" />
                  <h3 className="text-white font-semibold">Technical Score</h3>
                </div>
                <div className={`text-4xl font-bold mb-2 ${getScoreColor(evaluation.technical_score)}`}>
                  {evaluation.technical_score?.toFixed(1) || 'N/A'}
                  {evaluation.technical_score && <span className="text-xl">/10</span>}
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-[#05fcd3] h-2 rounded-full transition-all duration-1000"
                    style={{ width: getScoreWidth(evaluation.technical_score) }}
                  />
                </div>
              </div>

              <div className="bg-black/50 border border-[#05fcd3]/30 rounded-lg p-6">
                <div className="flex items-center gap-3 mb-3">
                  <MessageSquare className="w-6 h-6 text-[#05fcd3]" />
                  <h3 className="text-white font-semibold">Communication</h3>
                </div>
                <div className={`text-4xl font-bold mb-2 ${getScoreColor(evaluation.communication_score)}`}>
                  {evaluation.communication_score?.toFixed(1) || 'N/A'}
                  {evaluation.communication_score && <span className="text-xl">/10</span>}
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-[#05fcd3] h-2 rounded-full transition-all duration-1000"
                    style={{ width: getScoreWidth(evaluation.communication_score) }}
                  />
                </div>
              </div>

              <div className="bg-black/50 border border-[#05fcd3]/30 rounded-lg p-6">
                <div className="flex items-center gap-3 mb-3">
                  <TrendingUp className="w-6 h-6 text-[#05fcd3]" />
                  <h3 className="text-white font-semibold">Role Fit</h3>
                </div>
                <div className={`text-4xl font-bold mb-2 ${getScoreColor(evaluation.role_fit_score)}`}>
                  {evaluation.role_fit_score?.toFixed(1) || 'N/A'}
                  {evaluation.role_fit_score && <span className="text-xl">/10</span>}
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-[#05fcd3] h-2 rounded-full transition-all duration-1000"
                    style={{ width: getScoreWidth(evaluation.role_fit_score) }}
                  />
                </div>
              </div>
            </div>

            {evaluation.feedback && (
              <div className="bg-black/50 border border-[#05fcd3]/30 rounded-lg p-6 mb-6">
                <h3 className="text-xl font-semibold text-[#05fcd3] mb-3">Feedback</h3>
                <p className="text-white leading-relaxed whitespace-pre-line">{evaluation.feedback}</p>
              </div>
            )}

            {evaluation.raw_evaluation && (
              <div className="bg-black/50 border border-[#05fcd3]/30 rounded-lg p-6">
                <h3 className="text-xl font-semibold text-[#05fcd3] mb-3">Detailed Evaluation</h3>
                <p className="text-white leading-relaxed whitespace-pre-line">{evaluation.raw_evaluation}</p>
              </div>
            )}
          </div>

          <div className="bg-gray-900/50 backdrop-blur-sm border border-[#05fcd3]/20 rounded-2xl p-6 mb-6">
            <h3 className="text-xl font-semibold text-[#05fcd3] mb-4">Interview Transcript</h3>
            <div className="space-y-4 max-h-96 overflow-y-auto">
              {state.qaList.map((qa, index) => (
                <div key={index} className="bg-black/50 border border-[#05fcd3]/20 rounded-lg p-4">
                  <p className="text-[#05fcd3] font-semibold mb-2">Q{index + 1}: {qa.question}</p>
                  <p className="text-white ml-4">{qa.answer}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="flex gap-4">
            <button
              onClick={() => navigate('/')}
              className="flex-1 py-4 bg-gray-700 text-white font-semibold rounded-lg hover:bg-gray-600 transition-colors flex items-center justify-center gap-2"
            >
              <Home className="w-5 h-5" />
              Return to Home
            </button>
            <button
              onClick={handleDownloadPDF}
              className="flex-1 py-4 bg-[#05fcd3] text-black font-semibold rounded-lg hover:bg-[#04dab8] transition-all duration-300 flex items-center justify-center gap-2 shadow-lg shadow-[#05fcd3]/30"
            >
              <Download className="w-5 h-5" />
              Download Result (PDF)
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResultsPage;
