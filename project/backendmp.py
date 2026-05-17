# ----------------------------------------------------------
#  HireMateAI Backend  —  FINAL STABLE VERSION
# ----------------------------------------------------------

import os
import warnings
import time
import uuid
import tempfile
import shutil
import io
import re
import traceback
from typing import List, Dict, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

import pyttsx3
import speech_recognition as sr

# Optional: Gemini
try:
    import google.generativeai as genai
except Exception:
    genai = None

from pdfminer.high_level import extract_text
from pydub import AudioSegment
from pydub.utils import which

# ----------------------------------------------------------
# FFMPEG — FIXED & STABLE
# ----------------------------------------------------------
FFMPEG_EXE = r"C:\ffmpeg\ffmpegfile\bin\ffmpeg.exe"
FFPROBE_EXE = r"C:\ffmpeg\ffmpegfile\bin\ffprobe.exe"

# Converter
if os.path.exists(FFMPEG_EXE):
    AudioSegment.converter = FFMPEG_EXE
else:
    fallback = which("ffmpeg")
    if fallback:
        AudioSegment.converter = fallback
    else:
        print("❌ FFMPEG NOT FOUND. Audio conversion will fail.")

# Probe
if os.path.exists(FFPROBE_EXE):
    AudioSegment.ffprobe = FFPROBE_EXE

# ----------------------------------------------------------
# BASIC
# ----------------------------------------------------------
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
warnings.filterwarnings('ignore')

GEMINI_API_KEY = "AIzaSyCJF-X5XmWRCEeFPlt3cWGl7a7htSJcU1c"
if GEMINI_API_KEY and genai:
    genai.configure(api_key=GEMINI_API_KEY)

try:
    model = genai.GenerativeModel("models/gemini-2.5-flash") if genai else None
except:
    model = None

recognizer = sr.Recognizer()
recognizer.pause_threshold = 1.2

# ----------------------------------------------------------
# FASTAPI
# ----------------------------------------------------------
app = FastAPI(title="HireMate AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

QUESTIONS_STORE: Dict[str, Dict] = {}
QUESTIONS_TTL_SECONDS = 3600


# ----------------------------------------------------------
# HELPERS
# ----------------------------------------------------------
def ensure_model_ready():
    if model is None:
        raise HTTPException(status_code=500, detail="Model not initialized")
    return True


def extract_resume_text_from_file(file_path: str) -> Optional[str]:
    try:
        if file_path.endswith(".pdf"):
            return extract_text(file_path)
        elif file_path.endswith(".txt"):
            return open(file_path, "r", encoding="utf-8").read()
    except:
        return None
    return None


def parse_scores_from_text(text: str):
    out = {"technical": None, "communication": None, "role_fit": None, "final": None, "feedback": None}
    try:
        m = re.search(r"Technical.*?(\d+(?:\.\d+)?)", text, re.I)
        if m: out["technical"] = float(m.group(1))

        m = re.search(r"Communication.*?(\d+(?:\.\d+)?)", text, re.I)
        if m: out["communication"] = float(m.group(1))

        m = re.search(r"(Role[- ]?fit).*?(\d+(?:\.\d+)?)", text, re.I)
        if m: out["role_fit"] = float(m.group(2))

        m = re.search(r"(Final|Overall).*?(\d+(?:\.\d+)?)", text, re.I)
        if m: out["final"] = float(m.group(2))

        m = re.search(r"(Feedback|Recommendation)[:\-]?\s*(.+)", text, re.I | re.S)
        if m: out["feedback"] = m.group(2).strip()
    except:
        pass
    return out


# ----------------------------------------------------------
# MODELS
# ----------------------------------------------------------
class ResumeEvaluationResponse(BaseModel):
    success: bool
    resume_text: Optional[str] = None
    resume_summary: str
    evaluation: str
    message: str


class QuestionGenerationRequest(BaseModel):
    company: str
    role: str
    resume_summary: str
    num_questions: int


class QuestionGenerationResponse(BaseModel):
    success: bool
    session_id: str
    questions: List[str]
    message: str


class QAPair(BaseModel):
    question: str
    answer: str


class InterviewEvaluationRequest(BaseModel):
    qa_list: List[QAPair]
    role: str
    resume_summary: str


class InterviewEvaluationResponse(BaseModel):
    success: bool
    technical_score: Optional[float]
    communication_score: Optional[float]
    role_fit_score: Optional[float]
    final_score: Optional[float]
    feedback: Optional[str]
    raw_evaluation: Optional[str]
    message: str


class TextToSpeechRequest(BaseModel):
    text: str
    rate: Optional[int] = 150


class SpeechToTextResponse(BaseModel):
    success: bool
    transcription: str
    message: str


# ----------------------------------------------------------
# ROOT
# ----------------------------------------------------------
@app.get("/")
async def root():
    return {"message": "HireMate AI API is running"}


# ----------------------------------------------------------
# SPEECH TO TEXT — *FULLY FIXED*
# ----------------------------------------------------------
@app.post("/speech_to_text", response_model=SpeechToTextResponse)
async def speech_to_text(audio_file: UploadFile = File(...)):
    """
    FIXED:
    - Always converts to WAV PCM 16k Mono
    - Works with .webm from your React MediaRecorder
    - Stable Google SpeechRecognizer transcription
    """

    tmp_in = None
    tmp_wav = None

    try:
        # Save uploaded file
        ext = os.path.splitext(audio_file.filename)[1].lower()
        if ext not in [".webm", ".ogg", ".mp3", ".wav", ".m4a"]:
            ext = ".webm"

        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            shutil.copyfileobj(audio_file.file, tmp)
            tmp_in = tmp.name

        # Convert to WAV 16k mono
        audio = AudioSegment.from_file(tmp_in)
        audio = audio.set_channels(1).set_frame_rate(16000)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp2:
            tmp_wav = tmp2.name
            audio.export(tmp_wav, format="wav")

        # Transcribe
        with sr.AudioFile(tmp_wav) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.3)
            audio_data = recognizer.record(source)

        text = recognizer.recognize_google(audio_data)

        return SpeechToTextResponse(
            success=True,
            transcription=text,
            message="OK"
        )

    except sr.UnknownValueError:
        return SpeechToTextResponse(success=False, transcription="", message="Could not understand audio")

    except Exception as e:
        return SpeechToTextResponse(success=False, transcription="", message=str(e))

    finally:
        if tmp_in and os.path.exists(tmp_in):
            os.unlink(tmp_in)
        if tmp_wav and os.path.exists(tmp_wav):
            os.unlink(tmp_wav)


# ----------------------------------------------------------
# TTS (unchanged)
# ----------------------------------------------------------
@app.post("/tts")
async def text_to_speech(tts_req: TextToSpeechRequest):
    engine = pyttsx3.init()
    engine.setProperty("rate", tts_req.rate)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp_path = tmp.name
    tmp.close()

    engine.save_to_file(tts_req.text, tmp_path)
    engine.runAndWait()
    engine.stop()

    audio = open(tmp_path, "rb").read()
    os.unlink(tmp_path)

    return StreamingResponse(io.BytesIO(audio), media_type="audio/wav")


# ----------------------------------------------------------
# Resume Upload (unchanged)
# ----------------------------------------------------------
@app.post("/upload_resume", response_model=ResumeEvaluationResponse)
async def upload_resume(file: UploadFile = File(...), role: str = Form(...)):
    tmp_path = None
    try:
        suffix = ".pdf" if file.filename.endswith(".pdf") else ".txt"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        text = extract_resume_text_from_file(tmp_path)
        if not text:
            return ResumeEvaluationResponse(success=False, resume_summary="N/A", evaluation="N/A",
                                            message="Resume unreadable")

        ensure_model_ready()

        resp = model.generate_content(
            f"You are a concise resume evaluator for role: {role}.\nResume:\n{text[:3000]}\n"
            "Give:\nTechnical Score: X/10\nFeedback (2 sentences)"
        )
        evaluation_text = resp.text.strip()

        summary = model.generate_content(
            f"Summarize this resume in 2 sentences:\n{text[:2000]}"
        ).text.strip()

        return ResumeEvaluationResponse(
            success=True,
            resume_text=text[:1000],
            resume_summary=summary,
            evaluation=evaluation_text,
            message="Resume evaluated"
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ----------------------------------------------------------
# Generate Questions (unchanged)
# ----------------------------------------------------------
@app.post("/generate_questions", response_model=QuestionGenerationResponse)
async def generate_questions(request: QuestionGenerationRequest):
    ensure_model_ready()

    num = max(1, min(15, request.num_questions))

    resp = model.generate_content(
        f"Generate {num} short interview questions for {request.role} at {request.company}.\n"
        f"Resume summary: {request.resume_summary}\nNumbered list:"
    )

    raw = resp.text.split("\n")
    questions = [re.sub(r"^\d+\.\s*", "", q).strip() for q in raw if q.strip()]

    session_id = str(uuid.uuid4())
    QUESTIONS_STORE[session_id] = {"questions": questions, "created": time.time()}

    return QuestionGenerationResponse(success=True, session_id=session_id, questions=questions, message="OK")


@app.get("/questions/{session_id}")
async def get_questions(session_id: str):
    data = QUESTIONS_STORE.get(session_id)
    if not data:
        raise HTTPException(404, "Session expired")
    return {"success": True, "questions": data["questions"]}


# ----------------------------------------------------------
# Interview Evaluation (unchanged)
# ----------------------------------------------------------
@app.post("/evaluate_interview", response_model=InterviewEvaluationResponse)
async def evaluate_interview(req: InterviewEvaluationRequest):
    ensure_model_ready()

    qa_text = "\n".join([f"Q: {q.question}\nA: {q.answer}\n" for q in req.qa_list])

    resp = model.generate_content(
        f"Evaluate interview for role {req.role}.\nResume summary: {req.resume_summary}\nTranscript:\n{qa_text}\n"
        "Give:\nTechnical Score: X/10\nCommunication Score: X/10\nRole-fit Score: X/10\nFinal Score: X/10\n"
        "Feedback (3–5 sentences)"
    )

    parsed = parse_scores_from_text(resp.text)
    final = parsed["final"]

    if final is None and all(parsed[x] for x in ["technical", "communication", "role_fit"]):
        final = round((parsed["technical"] + parsed["communication"] + parsed["role_fit"]) / 3, 2)

    return InterviewEvaluationResponse(
        success=True,
        technical_score=parsed["technical"],
        communication_score=parsed["communication"],
        role_fit_score=parsed["role_fit"],
        final_score=final,
        feedback=parsed["feedback"],
        raw_evaluation=resp.text,
        message="Evaluation complete"
    )


# ----------------------------------------------------------
# RUN
# ----------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)