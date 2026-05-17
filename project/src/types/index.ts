export interface ResumeEvaluationResponse {
  success: boolean;
  resume_text?: string;
  resume_summary: string;
  evaluation: string;
  message: string;
}

export interface QuestionGenerationResponse {
  success: boolean;
  session_id: string;
  questions: string[];
  message: string;
}

export interface QAPair {
  question: string;
  answer: string;
}

export interface InterviewEvaluationResponse {
  success: boolean;
  technical_score?: number;
  communication_score?: number;
  role_fit_score?: number;
  final_score?: number;
  feedback?: string;
  raw_evaluation?: string;
  message: string;
}

export interface SpeechToTextResponse {
  success: boolean;
  transcription: string;
  message: string;
}
