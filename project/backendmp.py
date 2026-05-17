# ----------------------------------------------------------
#  HireMateAI Backend  —  FINAL STABLE VERSION
# ----------------------------------------------------------
'''
import os
import warnings
import time
import uuid
import tempfile
import shutil
import io
import re
import traceback
from pathlib import Path
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

def load_env_file(env_path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not env_path.exists():
        return values

    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.startswith("export "):
                stripped = stripped[len("export "):].strip()
            if "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                values[key] = value
    except Exception:
        return values

    return values


def load_api_key_from_env_files() -> Optional[str]:
    project_dir = Path(__file__).resolve().parent
    candidate_files = [project_dir / ".env", project_dir.parent / ".env"]

    for env_path in candidate_files:
        values = load_env_file(env_path)
        api_key = values.get("GEMINI_API_KEY") or values.get("GOOGLE_API_KEY")
        if api_key:
            os.environ.setdefault("GEMINI_API_KEY", api_key)
            os.environ.setdefault("GOOGLE_API_KEY", api_key)
            return api_key

    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


GEMINI_API_KEY = load_api_key_from_env_files()
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
            try:
                return open(file_path, "r", encoding="utf-8").read()
            except Exception:
                with open(file_path, "rb") as f:
                    raw = f.read()
                if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
                    return raw.decode("utf-16", errors="ignore")
                return raw.decode("utf-8", errors="ignore")
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


def simple_summary(text: str, max_sentences: int = 2) -> str:
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s for s in sentences if s]
    if not sentences:
        return text[:200].strip()
    return " ".join(sentences[:max_sentences]).strip()


def simple_resume_evaluation(text: str, role: str) -> str:
    keywords = [
        "python", "java", "react", "node", "docker", "aws",
        "sql", "tensorflow", "pytorch", "machine learning", "ml",
    ]
    lowered = text.lower()
    matches = [keyword for keyword in keywords if keyword in lowered]
    technical_score = min(10.0, 3.0 + len(matches) * 1.2)
    communication_score = 6.0 if len(text.split()) > 120 else 5.0
    feedback = (
        f"Technical Score: {technical_score:.1f}/10\n"
        f"Communication Score: {communication_score:.1f}/10\n"
        f"Recommendation: Resume appears relevant for {role}."
    )
    return feedback


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

        summary = None
        evaluation_text = None

        if model is not None:
            try:
                ensure_model_ready()

                resp = model.generate_content(
                    f"You are a concise resume evaluator for role: {role}.\nResume:\n{text[:3000]}\n"
                    "Give:\nTechnical Score: X/10\nFeedback (2 sentences)"
                )
                evaluation_text = resp.text.strip()

                summary = model.generate_content(
                    f"Summarize this resume in 2 sentences:\n{text[:2000]}"
                ).text.strip()
            except Exception as e:
                print("Resume analysis model call failed, falling back:", e)

        if not summary or not evaluation_text:
            summary = simple_summary(text, max_sentences=2)
            evaluation_text = simple_resume_evaluation(text, role)

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
    '''

# ----------------------------------------------------------
#  HireMateAI Backend  —  FINAL WORKING VERSION
# ----------------------------------------------------------

import os
import warnings
import time
import uuid
import tempfile
import shutil
import io
import re
from pathlib import Path
from typing import List, Dict, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import pyttsx3
import speech_recognition as sr

# ----------------------------------------------------------
# GEMINI IMPORT
# ----------------------------------------------------------
try:
    import google.generativeai as genai
except Exception:
    genai = None

from pdfminer.high_level import extract_text
from pydub import AudioSegment
from pydub.utils import which

# ----------------------------------------------------------
# FFMPEG
# ----------------------------------------------------------
FFMPEG_EXE = r"C:\ffmpeg\ffmpegfile\bin\ffmpeg.exe"
FFPROBE_EXE = r"C:\ffmpeg\ffmpegfile\bin\ffprobe.exe"

if os.path.exists(FFMPEG_EXE):
    AudioSegment.converter = FFMPEG_EXE
else:
    fallback = which("ffmpeg")
    if fallback:
        AudioSegment.converter = fallback
    else:
        print("WARNING: FFMPEG NOT FOUND")

if os.path.exists(FFPROBE_EXE):
    AudioSegment.ffprobe = FFPROBE_EXE

# ----------------------------------------------------------
# BASIC SETTINGS
# ----------------------------------------------------------
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
warnings.filterwarnings('ignore')

# ----------------------------------------------------------
# GEMINI API KEY (from .env or environment)
# ----------------------------------------------------------
def load_env_file(env_path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not env_path.exists():
        return values
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.startswith("export "):
                stripped = stripped[len("export "):].strip()
            if "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                values[key] = value
    except Exception:
        return values
    return values


def load_api_key() -> Optional[str]:
    project_dir = Path(__file__).resolve().parent
    for env_path in (project_dir / ".env", project_dir.parent / ".env"):
        values = load_env_file(env_path)
        api_key = values.get("GEMINI_API_KEY") or values.get("GOOGLE_API_KEY")
        if api_key:
            return api_key
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


GEMINI_API_KEY = load_api_key()

if genai is not None and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)

        model = genai.GenerativeModel("models/gemini-2.5-flash")

        print("Gemini initialized successfully")

    except Exception as e:
        print("Gemini initialization failed")
        print("ERROR:", str(e))
        model = None
elif genai is None:
    print("google.generativeai package not installed")
    model = None
else:
    print("GEMINI_API_KEY not set — add it to project/.env")
    model = None

# ----------------------------------------------------------
# SPEECH RECOGNIZER
# ----------------------------------------------------------
recognizer = sr.Recognizer()
recognizer.pause_threshold = 1.2

# ----------------------------------------------------------
# FASTAPI
# ----------------------------------------------------------
app = FastAPI(
    title="HireMate AI API",
    version="1.0.0"
)

_DEFAULT_CORS = (
    "http://localhost:5173,http://localhost:5174,"
    "http://127.0.0.1:5173,http://127.0.0.1:5174"
)
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", _DEFAULT_CORS).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

QUESTIONS_STORE: Dict[str, Dict] = {}

# ----------------------------------------------------------
# HELPERS
# ----------------------------------------------------------
def ensure_model_ready():
    if model is None:
        raise HTTPException(
            status_code=500,
            detail="Gemini model not initialized"
        )
    return True


def get_gemini_text(response) -> str:
    try:
        return (response.text or "").strip()
    except Exception:
        try:
            parts = response.candidates[0].content.parts
            return "".join(getattr(part, "text", "") or "" for part in parts).strip()
        except Exception:
            return ""


def call_gemini(prompt: str) -> Optional[str]:
    if model is None:
        return None
    try:
        response = model.generate_content(prompt)
        text = get_gemini_text(response)
        return text or None
    except Exception as e:
        print("Gemini call failed:", e)
        return None


def extract_resume_text_from_file(file_path: str) -> Optional[str]:
    try:
        if file_path.endswith(".pdf"):
            return extract_text(file_path)

        elif file_path.endswith(".txt"):
            try:
                return open(file_path, "r", encoding="utf-8").read()

            except Exception:
                with open(file_path, "rb") as f:
                    raw = f.read()

                if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
                    return raw.decode("utf-16", errors="ignore")

                return raw.decode("utf-8", errors="ignore")

    except Exception as e:
        print("Resume extraction error:", e)
        return None

    return None


def parse_scores_from_text(text: str):

    out = {
        "technical": None,
        "communication": None,
        "role_fit": None,
        "final": None,
        "feedback": None
    }

    try:
        m = re.search(r"Technical.*?(\d+(?:\.\d+)?)", text, re.I)
        if m:
            out["technical"] = float(m.group(1))

        m = re.search(r"Communication.*?(\d+(?:\.\d+)?)", text, re.I)
        if m:
            out["communication"] = float(m.group(1))

        m = re.search(r"(Role[- ]?fit).*?(\d+(?:\.\d+)?)", text, re.I)
        if m:
            out["role_fit"] = float(m.group(2))

        m = re.search(r"(Final|Overall).*?(\d+(?:\.\d+)?)", text, re.I)
        if m:
            out["final"] = float(m.group(2))

        m = re.search(
            r"(Feedback|Recommendation)[:\-]?\s*(.+)",
            text,
            re.I | re.S
        )

        if m:
            out["feedback"] = m.group(2).strip()

    except Exception as e:
        print("Score parsing error:", e)

    return out


def simple_summary(text: str, max_sentences: int = 2):

    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s for s in sentences if s]

    if not sentences:
        return text[:200]

    return " ".join(sentences[:max_sentences])


def parse_questions_from_text(text: str) -> List[str]:
    raw = text.split("\n")
    return [
        re.sub(r"^\d+[\.\)]\s*", "", q).strip()
        for q in raw
        if q.strip()
    ]


def fallback_interview_questions(
    company: str,
    role: str,
    num: int
) -> List[str]:

    pool = [
        f"Tell me about yourself and why you want the {role} role at {company}.",
        f"What experience do you have that is most relevant to this {role} position?",
        f"Describe a technical challenge you solved and the outcome.",
        f"How do you stay current with technologies used in {role} work?",
        f"Tell me about a team project you contributed to and your specific role.",
        f"What are your strongest skills for this {role} role?",
        f"Describe a time you had to deliver under a tight deadline.",
        f"How do you handle constructive feedback on your work?",
        f"Walk me through a project from your background that fits this role.",
        f"How would you approach your first 30 days as a {role} at {company}?",
        f"Describe a time you had to learn something new quickly for work.",
        f"What outcomes or metrics do you use to measure success?",
        f"How do you prioritize when handling multiple responsibilities?",
        f"Tell me about a mistake you made and what you learned from it.",
        f"Why should {company} hire you for this {role} position?",
    ]

    return pool[:max(1, min(num, len(pool)))]


def simple_resume_evaluation(text: str, role: str):

    keywords = [
        "python",
        "java",
        "react",
        "node",
        "docker",
        "aws",
        "sql",
        "tensorflow",
        "pytorch",
        "machine learning",
        "ml",
    ]

    lowered = text.lower()

    matches = [
        keyword
        for keyword in keywords
        if keyword in lowered
    ]

    technical_score = min(10.0, 3.0 + len(matches) * 1.2)

    communication_score = (
        6.0 if len(text.split()) > 120 else 5.0
    )

    feedback = (
        f"Technical Score: {technical_score:.1f}/10\n"
        f"Communication Score: {communication_score:.1f}/10\n"
        f"Recommendation: Resume appears relevant for {role}."
    )

    return feedback

# ----------------------------------------------------------
# RESPONSE MODELS
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
    return {
        "message": "HireMate AI API is running"
    }

# ----------------------------------------------------------
# SPEECH TO TEXT
# ----------------------------------------------------------
@app.post(
    "/speech_to_text",
    response_model=SpeechToTextResponse
)
async def speech_to_text(
    audio_file: UploadFile = File(...)
):

    tmp_in = None
    tmp_wav = None

    try:
        ext = os.path.splitext(audio_file.filename)[1].lower()

        if ext not in [
            ".webm",
            ".ogg",
            ".mp3",
            ".wav",
            ".m4a"
        ]:
            ext = ".webm"

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=ext
        ) as tmp:

            shutil.copyfileobj(audio_file.file, tmp)
            tmp_in = tmp.name

        audio = AudioSegment.from_file(tmp_in)

        audio = audio.set_channels(1).set_frame_rate(16000)

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".wav"
        ) as tmp2:

            tmp_wav = tmp2.name

            audio.export(
                tmp_wav,
                format="wav"
            )

        with sr.AudioFile(tmp_wav) as source:

            recognizer.adjust_for_ambient_noise(
                source,
                duration=0.3
            )

            audio_data = recognizer.record(source)

        text = recognizer.recognize_google(audio_data)

        return SpeechToTextResponse(
            success=True,
            transcription=text,
            message="OK"
        )

    except sr.UnknownValueError:

        return SpeechToTextResponse(
            success=False,
            transcription="",
            message="Could not understand audio"
        )

    except Exception as e:

        return SpeechToTextResponse(
            success=False,
            transcription="",
            message=str(e)
        )

    finally:

        if tmp_in and os.path.exists(tmp_in):
            os.unlink(tmp_in)

        if tmp_wav and os.path.exists(tmp_wav):
            os.unlink(tmp_wav)

# ----------------------------------------------------------
# TEXT TO SPEECH
# ----------------------------------------------------------
@app.post("/tts")
async def text_to_speech(
    tts_req: TextToSpeechRequest
):

    engine = pyttsx3.init()

    engine.setProperty(
        "rate",
        tts_req.rate
    )

    tmp = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".wav"
    )

    tmp_path = tmp.name
    tmp.close()

    engine.save_to_file(
        tts_req.text,
        tmp_path
    )

    engine.runAndWait()
    engine.stop()

    audio = open(tmp_path, "rb").read()

    os.unlink(tmp_path)

    return StreamingResponse(
        io.BytesIO(audio),
        media_type="audio/wav"
    )

# ----------------------------------------------------------
# RESUME UPLOAD
# ----------------------------------------------------------
@app.post(
    "/upload_resume",
    response_model=ResumeEvaluationResponse
)
async def upload_resume(
    file: UploadFile = File(...),
    role: str = Form(...)
):

    tmp_path = None

    try:
        filename = (file.filename or "resume.txt").lower()
        suffix = ".pdf" if filename.endswith(".pdf") else ".txt"

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as tmp:

            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        text = extract_resume_text_from_file(tmp_path)

        if not text:

            return ResumeEvaluationResponse(
                success=False,
                resume_summary="N/A",
                evaluation="N/A",
                message="Resume unreadable"
            )

        evaluation_text = call_gemini(
            f"""
            You are a professional resume evaluator.

            Role: {role}

            Resume:
            {text[:3000]}

            Give:
            Technical Score: X/10
            Communication Score: X/10
            Feedback in 3 concise sentences.
            """
        )

        summary = call_gemini(
            f"""
            Summarize this resume in 2 concise sentences:

            {text[:2000]}
            """
        )

        used_fallback = not summary or not evaluation_text

        if used_fallback:
            summary = simple_summary(text)
            evaluation_text = simple_resume_evaluation(text, role)

        message = "Resume evaluated successfully"
        if used_fallback and model is not None:
            message = (
                "Resume evaluated using offline scoring "
                "(Gemini quota unavailable or API error)"
            )

        return ResumeEvaluationResponse(
            success=True,
            resume_text=text[:1000],
            resume_summary=summary,
            evaluation=evaluation_text,
            message=message
        )

    except HTTPException:
        raise
    except Exception as e:
        print("upload_resume error:", e)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze resume: {e}"
        )
    finally:

        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

# ----------------------------------------------------------
# GENERATE QUESTIONS
# ----------------------------------------------------------
@app.post(
    "/generate_questions",
    response_model=QuestionGenerationResponse
)
async def generate_questions(
    request: QuestionGenerationRequest
):

    num = max(1, min(15, request.num_questions))

    gemini_text = call_gemini(
        f"""
        Generate {num} interview questions.

        Company: {request.company}
        Role: {request.role}

        Resume Summary:
        {request.resume_summary}

        Give only numbered questions.
        """
    )

    questions = parse_questions_from_text(gemini_text) if gemini_text else []
    used_fallback = not questions

    if used_fallback:
        questions = fallback_interview_questions(
            request.company,
            request.role,
            num
        )

    session_id = str(uuid.uuid4())

    QUESTIONS_STORE[session_id] = {
        "questions": questions,
        "created": time.time()
    }

    message = "Questions generated"
    if used_fallback:
        message = (
            "Questions generated using offline fallback "
            "(Gemini quota unavailable or API error)"
        )

    return QuestionGenerationResponse(
        success=True,
        session_id=session_id,
        questions=questions,
        message=message
    )

# ----------------------------------------------------------
# GET QUESTIONS
# ----------------------------------------------------------
@app.get("/questions/{session_id}")
async def get_questions(session_id: str):

    data = QUESTIONS_STORE.get(session_id)

    if not data:
        raise HTTPException(
            status_code=404,
            detail="Session expired"
        )

    return {
        "success": True,
        "questions": data["questions"]
    }

# ----------------------------------------------------------
# INTERVIEW EVALUATION
# ----------------------------------------------------------
@app.post(
    "/evaluate_interview",
    response_model=InterviewEvaluationResponse
)
async def evaluate_interview(
    req: InterviewEvaluationRequest
):

    qa_text = "\n".join([
        f"Q: {q.question}\nA: {q.answer}\n"
        for q in req.qa_list
    ])

    evaluation_text = call_gemini(
        f"""
        Evaluate this interview.

        Role:
        {req.role}

        Resume Summary:
        {req.resume_summary}

        Interview Transcript:
        {qa_text}

        Give:
        Technical Score: X/10
        Communication Score: X/10
        Role-fit Score: X/10
        Final Score: X/10

        Feedback in 4 sentences.
        """
    )

    used_fallback = not evaluation_text

    if used_fallback:
        answer_count = len(req.qa_list)
        avg_len = (
            sum(len(q.answer.split()) for q in req.qa_list) / answer_count
            if answer_count
            else 0
        )
        technical = min(10.0, 4.0 + avg_len / 15)
        communication = min(10.0, 4.0 + avg_len / 20)
        role_fit = round((technical + communication) / 2, 1)
        final = round((technical + communication + role_fit) / 3, 1)
        feedback = (
            f"Solid effort for the {req.role} role. "
            f"You answered {answer_count} question(s) with reasonable detail. "
            "Practice structuring answers with situation, action, and result. "
            "Offline scoring used because Gemini quota is unavailable."
        )
        parsed = {
            "technical": technical,
            "communication": communication,
            "role_fit": role_fit,
            "final": final,
            "feedback": feedback,
        }
        raw_evaluation = feedback
    else:
        parsed = parse_scores_from_text(evaluation_text)
        raw_evaluation = evaluation_text

    final = parsed["final"]

    if (
        final is None and
        all(parsed[x] for x in [
            "technical",
            "communication",
            "role_fit"
        ])
    ):
        final = round(
            (
                parsed["technical"] +
                parsed["communication"] +
                parsed["role_fit"]
            ) / 3,
            2
        )

    message = "Interview evaluation completed"
    if used_fallback:
        message = (
            "Interview evaluation completed using offline fallback "
            "(Gemini quota unavailable or API error)"
        )

    return InterviewEvaluationResponse(
        success=True,
        technical_score=parsed["technical"],
        communication_score=parsed["communication"],
        role_fit_score=parsed["role_fit"],
        final_score=final,
        feedback=parsed["feedback"],
        raw_evaluation=raw_evaluation,
        message=message
    )

# ----------------------------------------------------------
# RUN SERVER
# ----------------------------------------------------------
def _port_in_use(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(("127.0.0.1", port)) == 0


if __name__ == "__main__":

    import sys
    import uvicorn

    port = 8000

    if _port_in_use(port):
        print(f"\nPort {port} is already in use — backend is likely already running.")
        print(f"  Open: http://localhost:{port}/docs")
        print("  To restart, stop the other process first:")
        print("    Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess")
        print("    Stop-Process -Id <PID> -Force")
        sys.exit(1)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port
    )