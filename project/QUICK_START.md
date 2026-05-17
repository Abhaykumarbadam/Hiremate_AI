# HireMate AI - Quick Start Guide

## Fastest Way to Get Started

### Step 1: Get Your Gemini API Key
1. Go to https://makersuite.google.com/app/apikey
2. Create a new API key
3. Copy the key

### Step 2: Place Backend File
Place your `backend.py` file in the project root directory (same folder as package.json)

### Step 3: Set API Key

**Linux/Mac:**
```bash
export GEMINI_API_KEY="your-api-key-here"
```

**Windows:**
```bash
set GEMINI_API_KEY=your-api-key-here
```

### Step 4: Install Python Dependencies
```bash
pip install fastapi uvicorn pyttsx3 speechrecognition google-generativeai pdfminer.six python-multipart
```

### Step 5: Run the Application

**Option A - Use Startup Scripts (Recommended):**

Linux/Mac:
```bash
./start.sh
```

Windows:
```bash
start.bat
```

**Option B - Manual Start:**

Terminal 1:
```bash
python backend.py
```

Terminal 2:
```bash
npm run dev
```

### Step 6: Open Your Browser
Navigate to: http://localhost:5173

## Application Flow

1. **Home Page** → Click "Start Interview"
2. **Resume Analyzer** → Upload resume, fill form, analyze
3. **Interview** → Answer AI-generated questions
4. **Results** → View scores and download PDF

## Important Notes

- Backend MUST be running on port 8000
- Frontend runs on port 5173
- Microphone access required for voice recording
- Internet connection required for AI features
- Use Chrome or Firefox for best compatibility

## Troubleshooting

**"GEMINI_API_KEY not configured"**
- Solution: Set the environment variable before starting backend

**"Failed to connect"**
- Solution: Ensure backend is running on http://localhost:8000

**Microphone not working**
- Solution: Grant microphone permissions in browser settings

**Audio not playing**
- Solution: Check browser volume and autoplay settings

## Tech Support

If you encounter issues:
1. Check both backend and frontend terminals for errors
2. Verify Python dependencies are installed
3. Ensure Node.js packages are installed (npm install)
4. Check browser console for errors (F12)
5. Verify GEMINI_API_KEY is valid

## File Checklist

Before running, ensure you have:
- ✅ backend.py in project root
- ✅ GEMINI_API_KEY environment variable set
- ✅ Python dependencies installed
- ✅ Node.js dependencies installed (npm install)

## URLs to Remember

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

Enjoy using HireMate AI!
