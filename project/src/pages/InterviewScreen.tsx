// InterviewScreen.tsx
import { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Mic, MicOff, Loader2, Volume2, Send } from 'lucide-react';
// Ensure API_ENDPOINTS.speechToText === "http://localhost:8000/speech_to_text"
import { API_ENDPOINTS } from '../config/api';
import type { QuestionGenerationResponse, QAPair, SpeechToTextResponse } from '../types';

interface LocationState {
  company: string;
  role: string;
  numQuestions: number;
  resumeSummary: string;
}

const InterviewScreen = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const state = location.state as LocationState;

  const [questions, setQuestions] = useState<string[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [qaList, setQaList] = useState<QAPair[]>([]);
  const [loading, setLoading] = useState(true);
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState('');
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [isProcessingAnswer, setIsProcessingAnswer] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    if (!state) {
      navigate('/');
      return;
    }
    generateQuestions();
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
      }
    };
  }, []);

  const generateQuestions = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.generateQuestions, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company: state.company,
          role: state.role,
          resume_summary: state.resumeSummary,
          num_questions: state.numQuestions,
        }),
      });

      if (!response.ok) throw new Error('Failed to generate questions');

      const data: QuestionGenerationResponse = await response.json();
      setQuestions(data.questions);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate questions');
    } finally {
      setLoading(false);
    }
  };

  const playQuestionAudio = async (questionText: string) => {
    try {
      setIsPlayingAudio(true);
      const response = await fetch(API_ENDPOINTS.tts, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: questionText, rate: 150 }),
      });

      if (!response.ok) throw new Error('Failed to generate audio');

      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);

      if (audioRef.current) {
        audioRef.current.pause();
      }

      const audio = new Audio(audioUrl);
      audioRef.current = audio;

      audio.onended = () => {
        setIsPlayingAudio(false);
        URL.revokeObjectURL(audioUrl);
      };

      await audio.play();
    } catch (err) {
      console.error('Audio playback error:', err);
      setIsPlayingAudio(false);
      setError('Audio playback failed');
    }
  };

  const startRecording = async () => {
    try {
      setError('');
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      let mimeType = '';
      if ((MediaRecorder as any).isTypeSupported && (MediaRecorder as any).isTypeSupported('audio/webm;codecs=opus')) {
        mimeType = 'audio/webm;codecs=opus';
      } else if ((MediaRecorder as any).isTypeSupported && (MediaRecorder as any).isTypeSupported('audio/webm')) {
        mimeType = 'audio/webm';
      }

      const mediaRecorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);

      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await transcribeAudio(audioBlob, 'recording.webm');
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((t) => t.stop());
          streamRef.current = null;
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error(err);
      setError('Microphone access failed. Check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      try {
        mediaRecorderRef.current.stop();
      } catch (e) {
        console.warn('Stop recording error', e);
      } finally {
        setIsRecording(false);
      }
    }
  };

  const transcribeAudio = async (audioBlob: Blob, filename = 'recording.webm') => {
    try {
      setIsProcessingAnswer(true);
      setError('');

      const formData = new FormData();
      formData.append('audio_file', audioBlob, filename);

      const res = await fetch(API_ENDPOINTS.speechToText, {
        method: 'POST',
        body: formData,
      });

      const text = await res.text();

      if (!res.ok) {
        try {
          const parsed = JSON.parse(text);
          throw new Error(parsed.message || parsed.detail || JSON.stringify(parsed));
        } catch {
          throw new Error(text || `HTTP ${res.status}`);
        }
      }

      const data: SpeechToTextResponse = JSON.parse(text);
      if (data.success) {
        setCurrentAnswer(data.transcription);
      } else {
        setError(data.message || 'Could not understand audio');
      }
    } catch (err) {
      console.error('Transcription error:', err);
      setError(err instanceof Error ? err.message : 'Transcription failed');
    } finally {
      setIsProcessingAnswer(false);
    }
  };

  const handleSubmitAnswer = () => {
    if (!currentAnswer.trim()) {
      setError('Answer cannot be empty');
      return;
    }

    const newQA: QAPair = {
      question: questions[currentQuestionIndex],
      answer: currentAnswer,
    };

    const updatedQAList = [...qaList, newQA];
    setQaList(updatedQAList);
    setCurrentAnswer('');
    setError('');

    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    } else {
      navigate('/results', {
        state: {
          qaList: updatedQAList,
          role: state.role,
          resumeSummary: state.resumeSummary,
        },
      });
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-16 h-16 text-[#05fcd3] animate-spin mx-auto mb-4" />
          <p className="text-white text-xl">Generating interview questions...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black relative overflow-hidden">
      <div className="relative z-10 container mx-auto px-4 py-12">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <div className="inline-block px-6 py-2 bg-[#05fcd3]/20 border border-[#05fcd3]/50 rounded-full mb-4">
              <p className="text-[#05fcd3]">Question {currentQuestionIndex + 1} of {questions.length}</p>
            </div>
            <h1 className="text-4xl font-bold text-white mb-2">AI Interview</h1>
            <p className="text-gray-400">Role: {state.role}</p>
          </div>

          <div className="relative bg-gray-900/50 border border-[#05fcd3]/20 rounded-2xl p-8 shadow-2xl mb-6">
            <div className="flex items-start gap-4 mb-6">
              <h2 className="text-2xl text-white flex-1">{questions[currentQuestionIndex]}</h2>
              <button
                onClick={() => playQuestionAudio(questions[currentQuestionIndex])}
                disabled={isPlayingAudio}
                className="p-3 bg-[#05fcd3]/20 border border-[#05fcd3]/50 rounded-lg hover:bg-[#05fcd3]/30 disabled:opacity-50"
              >
                <Volume2 className={`w-6 h-6 text-[#05fcd3] ${isPlayingAudio ? 'animate-pulse' : ''}`} />
              </button>
            </div>

            <textarea
              value={currentAnswer}
              onChange={(e) => setCurrentAnswer(e.target.value)}
              className="w-full px-4 py-3 bg-black/50 border border-[#05fcd3]/30 rounded-lg text-white focus:border-[#05fcd3]"
              rows={6}
              placeholder="Type your answer or use the microphone..."
            />

            <div className="flex items-center gap-4 mt-4">
              <button
                onClick={isRecording ? stopRecording : startRecording}
                disabled={isProcessingAnswer}
                className={`flex-1 py-4 rounded-lg flex items-center justify-center gap-2 ${
                  isRecording ? 'bg-red-500 text-white animate-pulse' : 'bg-[#05fcd3]/20 border border-[#05fcd3]/50 text-[#05fcd3]'
                } disabled:opacity-50`}
              >
                {isProcessingAnswer ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" /> Processing...
                  </>
                ) : isRecording ? (
                  <>
                    <MicOff className="w-5 h-5" /> Stop Recording
                  </>
                ) : (
                  <>
                    <Mic className="w-5 h-5" /> Record Answer
                  </>
                )}
              </button>

              <button
                onClick={handleSubmitAnswer}
                disabled={!currentAnswer.trim() || isRecording || isProcessingAnswer}
                className="flex-1 py-4 bg-[#05fcd3] text-black rounded-lg font-semibold hover:bg-[#04dab8] disabled:opacity-50"
              >
                {currentQuestionIndex < questions.length - 1 ? 'Next Question' : 'Finish Interview'}
              </button>
            </div>

            {error && (
              <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4 mt-4">
                <p className="text-red-400">{error}</p>
              </div>
            )}

            <button
              onClick={handleSubmitAnswer}
              disabled={!currentAnswer.trim() || isRecording || isProcessingAnswer}
              aria-label="Submit answer"
              className="absolute bottom-4 right-4 p-3 rounded-full bg-[#05fcd3] text-black shadow-lg disabled:opacity-50 flex items-center justify-center"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>

          <div className="bg-gray-900/30 border border-[#05fcd3]/10 rounded-lg p-4 text-center text-gray-400">
            Questions answered: {qaList.length} / {questions.length}
          </div>
        </div>
      </div>
    </div>
  );
};

export default InterviewScreen;
