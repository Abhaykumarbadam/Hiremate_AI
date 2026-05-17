# 🚀 START HERE - HireMate AI Setup

Welcome to HireMate AI! Follow these simple steps to get your interview application running.

## ⚡ Quick Setup (5 Minutes)

### Step 1: Place Your Backend File
Copy your `backend.py` file to this directory (project root).

```
project/
├── backend.py    ← Place it here
├── package.json
├── src/
└── ...
```

### Step 2: Get Your API Key
1. Visit: https://makersuite.google.com/app/apikey
2. Create an API key
3. Copy it

### Step 3: Install Dependencies

**Python dependencies:**
```bash
pip install fastapi uvicorn pyttsx3 speechrecognition google-generativeai pdfminer.six python-multipart
```

**Node.js dependencies:**
```bash
npm install
```

### Step 4: Set Your API Key

**Linux/Mac:**
```bash
export GEMINI_API_KEY="your-api-key-here"
```

**Windows:**
```bash
set GEMINI_API_KEY=your-api-key-here
```

### Step 5: Start the Application

**Easy Way (Recommended):**
```bash
./start.sh        # Linux/Mac
start.bat         # Windows
```

**Manual Way:**
```bash
# Terminal 1 - Backend
python backend.py

# Terminal 2 - Frontend
npm run dev
```

### Step 6: Open Your Browser
Navigate to: **http://localhost:5173**

---

## 🎯 Application Flow

1. **Home Page** → Click "Start Interview"
2. **Resume Analyzer** → Upload resume, fill form, click analyze
3. **Interview** → Answer AI questions (text or voice)
4. **Results** → View scores, download PDF

---

## 📚 Documentation Guide

Start with these files in order:

1. **START_HERE.md** (You are here!) - Quick setup
2. **README.md** - Full project documentation
3. **QUICK_START.md** - Fast troubleshooting
4. **BACKEND_SETUP.md** - Backend configuration details
5. **PROJECT_SUMMARY.md** - Complete overview
6. **FEATURES_CHECKLIST.md** - All 200+ features
7. **DEPLOYMENT_CHECKLIST.md** - Pre-deployment guide

---

## ✅ Verification Checklist

Before starting, ensure:
- [ ] `backend.py` is in project root directory
- [ ] Python 3.8+ installed
- [ ] Node.js 18+ installed
- [ ] Python dependencies installed
- [ ] Node dependencies installed (`npm install`)
- [ ] `GEMINI_API_KEY` environment variable set
- [ ] Microphone permissions enabled in browser

---

## 🎨 What You'll See

### Theme
- Neon teal (#05fcd3) accents
- Black background with animations
- Futuristic, professional design

### Features
- Upload PDF/TXT resumes
- AI-generated interview questions
- Voice recording for answers
- Text-to-speech for questions
- Detailed performance scores
- PDF export of results

---

## 🆘 Quick Troubleshooting

### "GEMINI_API_KEY not configured"
Set the environment variable before starting backend:
```bash
export GEMINI_API_KEY="your-key"  # Linux/Mac
set GEMINI_API_KEY=your-key       # Windows
```

### "Failed to connect"
Ensure backend is running on port 8000:
```bash
python backend.py
```

### "Microphone not working"
Grant microphone permissions in browser settings.

### Build errors
Reinstall dependencies:
```bash
rm -rf node_modules package-lock.json
npm install
```

---

## 📞 Support Resources

- **README.md** - Complete documentation
- **QUICK_START.md** - Fast setup guide
- **BACKEND_SETUP.md** - Backend help
- **PROJECT_SUMMARY.md** - Technical details
- **DIRECTORY_STRUCTURE.txt** - File organization

---

## 🎉 That's It!

Once both servers are running:
1. Open **http://localhost:5173**
2. Click **"Start Interview"**
3. Experience the AI interview platform!

The application is production-ready with:
- ✅ Zero mock data
- ✅ Full backend integration
- ✅ Professional design
- ✅ Complete documentation
- ✅ Error handling
- ✅ Loading states
- ✅ Responsive UI

**Enjoy HireMate AI - From Candidacy to Career! 🚀**
