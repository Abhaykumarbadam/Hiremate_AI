# Backend Setup Guide for HireMate AI

## Overview

The HireMate AI backend is built with FastAPI and uses Google's Gemini AI for natural language processing. This guide will help you set up the backend correctly.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Google Gemini API key

## Step-by-Step Setup

### 1. Get Google Gemini API Key

1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated API key
5. Keep it secure - do not share or commit to git

### 2. Install Python Dependencies

Run the following command in your project directory:

```bash
pip install fastapi uvicorn pyttsx3 speechrecognition google-generativeai pdfminer.six python-multipart
```

**Dependency Breakdown:**
- `fastapi` - Web framework for building the API
- `uvicorn` - ASGI server to run FastAPI
- `pyttsx3` - Text-to-speech conversion
- `speechrecognition` - Speech-to-text transcription
- `google-generativeai` - Google Gemini AI SDK
- `pdfminer.six` - PDF text extraction
- `python-multipart` - File upload handling

### 3. Set Environment Variable

The backend requires the GEMINI_API_KEY environment variable to be set.

**Linux/Mac:**
```bash
export GEMINI_API_KEY="your-api-key-here"
```

To make it permanent, add to your shell profile:
```bash
echo 'export GEMINI_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

**Windows Command Prompt:**
```bash
set GEMINI_API_KEY=your-api-key-here
```

**Windows PowerShell:**
```powershell
$env:GEMINI_API_KEY="your-api-key-here"
```

To make it permanent on Windows:
1. Search for "Environment Variables" in Start Menu
2. Click "Edit system environment variables"
3. Click "Environment Variables" button
4. Under "User variables", click "New"
5. Variable name: `GEMINI_API_KEY`
6. Variable value: your API key
7. Click OK

### 4. Place backend.py File

Place your `backend.py` file in the project root directory:

```
project/
├── backend.py          ← Place here
├── package.json
├── src/
└── ...
```

### 5. Run the Backend

Start the backend server:

```bash
python backend.py
```

Or with Python 3 explicitly:

```bash
python3 backend.py
```

You should see output like:
```
Starting HireMate AI backend on http://0.0.0.0:8000
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 6. Verify Backend is Running

Open your browser and visit:
- http://localhost:8000 - Should show API info
- http://localhost:8000/docs - Interactive API documentation

## Backend API Endpoints

### POST /upload_resume
Uploads and analyzes a resume file.

**Request:**
- `file`: Resume file (PDF or TXT)
- `role`: Job role (string)

**Response:**
```json
{
  "success": true,
  "resume_summary": "Brief summary...",
  "evaluation": "Technical Score: 8/10...",
  "message": "Resume evaluated"
}
```

### POST /generate_questions
Generates interview questions based on resume and role.

**Request:**
```json
{
  "company": "Company Name",
  "role": "Software Engineer",
  "resume_summary": "Resume summary...",
  "num_questions": 5
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "uuid",
  "questions": ["Question 1", "Question 2", ...],
  "message": "Generated questions"
}
```

### GET /questions/{session_id}
Retrieves questions for a specific session.

**Response:**
```json
{
  "success": true,
  "session_id": "uuid",
  "questions": ["Question 1", "Question 2", ...]
}
```

### POST /tts
Converts text to speech audio.

**Request:**
```json
{
  "text": "Question to speak",
  "rate": 150
}
```

**Response:**
- Audio/WAV stream

### POST /speech_to_text
Transcribes audio to text.

**Request:**
- `audio_file`: Audio file (WAV, MP3, FLAC, OGG, M4A)

**Response:**
```json
{
  "success": true,
  "transcription": "Transcribed text",
  "message": "Transcribed successfully"
}
```

### POST /evaluate_interview
Evaluates interview performance.

**Request:**
```json
{
  "qa_list": [
    {
      "question": "Question 1",
      "answer": "Answer 1"
    }
  ],
  "role": "Software Engineer",
  "resume_summary": "Resume summary..."
}
```

**Response:**
```json
{
  "success": true,
  "technical_score": 8.0,
  "communication_score": 7.5,
  "role_fit_score": 8.5,
  "final_score": 8.0,
  "feedback": "Detailed feedback...",
  "raw_evaluation": "Full evaluation text",
  "message": "Evaluation complete"
}
```

## Troubleshooting

### "GEMINI_API_KEY not configured"

**Problem:** Environment variable not set.

**Solution:**
```bash
export GEMINI_API_KEY="your-key-here"  # Linux/Mac
set GEMINI_API_KEY=your-key-here       # Windows
```

### "ModuleNotFoundError"

**Problem:** Missing Python dependencies.

**Solution:**
```bash
pip install [missing-module]
```

Or reinstall all:
```bash
pip install fastapi uvicorn pyttsx3 speechrecognition google-generativeai pdfminer.six python-multipart
```

### "Address already in use"

**Problem:** Port 8000 is already in use.

**Solution:**

Find and kill the process:
```bash
# Linux/Mac
lsof -ti:8000 | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID [PID] /F
```

Or change the port in `backend.py`:
```python
uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
```

And update `src/config/api.ts`:
```typescript
const API_BASE_URL = 'http://localhost:8001';
```

### "Could not understand audio"

**Problem:** Speech recognition failed.

**Causes:**
- Poor audio quality
- Background noise
- No internet connection (Google Speech API requires internet)
- Microphone not working

**Solution:**
- Test microphone
- Record in quiet environment
- Check internet connection
- Try shorter recordings

### "Model not initialized"

**Problem:** Invalid API key or model not available.

**Solution:**
- Verify API key is correct
- Check API key has Gemini access
- Check internet connection
- Verify model name in backend.py

## Configuration Options

### Change AI Model

In `backend.py`, modify:
```python
MODEL_NAME = "models/gemini-2.5-flash"  # Or another available model
```

Available models:
- `models/gemini-2.5-flash`
- `models/gemini-pro`
- Check Google AI Studio for latest models

### Change TTS Voice Rate

In `backend.py`, modify the default rate:
```python
engine.setProperty('rate', 150)  # Words per minute
```

### Adjust Session TTL

In `backend.py`, modify:
```python
QUESTIONS_TTL_SECONDS = 60 * 60  # 1 hour (in seconds)
```

## Security Best Practices

1. **Never commit API key to git**
   - Add `.env` to `.gitignore`
   - Use environment variables

2. **Restrict CORS in production**
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://yourdomain.com"],  # Specific domain
       ...
   )
   ```

3. **Add authentication**
   - Implement JWT tokens
   - Use API keys for frontend

4. **Rate limiting**
   - Add rate limiting middleware
   - Prevent API abuse

5. **Input validation**
   - Validate file sizes
   - Sanitize text inputs
   - Check file types

## Production Deployment

For production, use a production WSGI server:

**Using Gunicorn:**
```bash
pip install gunicorn
gunicorn backend:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**Using Docker:**
Create `Dockerfile`:
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY backend.py .
CMD ["python", "backend.py"]
```

Build and run:
```bash
docker build -t hiremate-backend .
docker run -p 8000:8000 -e GEMINI_API_KEY="your-key" hiremate-backend
```

## Monitoring

Add logging:
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use in endpoints
logger.info(f"Resume uploaded: {file.filename}")
logger.error(f"Error processing: {str(e)}")
```

## Support

If you encounter issues:
1. Check the backend terminal for error messages
2. Verify all dependencies are installed
3. Test API endpoints using http://localhost:8000/docs
4. Check Google Gemini API status
5. Review the troubleshooting section above

For more help, check the main README.md and QUICK_START.md files.
