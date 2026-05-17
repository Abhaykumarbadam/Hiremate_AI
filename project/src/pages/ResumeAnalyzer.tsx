import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileText, Loader2, ArrowRight } from 'lucide-react';
import { API_ENDPOINTS } from '../config/api';
import type { ResumeEvaluationResponse } from '../types';

const ResumeAnalyzer = () => {
  const navigate = useNavigate();
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const [formData, setFormData] = useState({
    company: '',
    role: '',
    numQuestions: 5,
  });
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [resumeResults, setResumeResults] = useState<ResumeEvaluationResponse | null>(null);
  const [error, setError] = useState('');

  // ⚡ ELECTRIC BACKGROUND EFFECT — React Official Way
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };

    resize();
    window.addEventListener("resize", resize);

    const dots: any[] = [];
    const COUNT = 60;

    for (let i = 0; i < COUNT; i++) {
      dots.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        r: Math.random() * 2 + 1,
        vx: (Math.random() - 0.5) * 0.6,
        vy: (Math.random() - 0.5) * 0.6,
      });
    }

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      dots.forEach((dot) => {
        ctx.beginPath();
        ctx.arc(dot.x, dot.y, dot.r, 0, Math.PI * 2);
        ctx.fillStyle = "#0fffe6";
        ctx.shadowBlur = 12;
        ctx.shadowColor = "#0fffe6";
        ctx.fill();

        dot.x += dot.vx * 4.0;
        dot.y += dot.vy * 4.0;

        if (dot.x < 0 || dot.x > canvas.width) dot.vx *= -1;
        if (dot.y < 0 || dot.y > canvas.height) dot.vy *= -1;
      });

      // ELECTRICAL LINES
      // ELECTRIC LINES — MAXIMUM NEON GLOW
for (let i = 0; i < COUNT; i++) {
  for (let j = i + 1; j < COUNT; j++) {

    const dx = dots[i].x - dots[j].x;
    const dy = dots[i].y - dots[j].y;
    const dist = Math.sqrt(dx * dx + dy * dy);

    if (dist < 80) {

      // ONLY NEON CYAN
      const color = "rgba(0, 255, 255, ALPHA)";

      // BRIGHTNESS BOOST (same as before)
      const alpha = Math.min(4.5 - dist / 80, 3.5);

      ctx.beginPath();
      ctx.moveTo(dots[i].x, dots[i].y);
      ctx.lineTo(dots[j].x, dots[j].y);

      ctx.strokeStyle = color.replace("ALPHA", alpha);

      // MAXIMUM GLOW SETTINGS
      ctx.lineWidth = 3.5;
      ctx.shadowBlur = 260;
      ctx.shadowColor = ctx.strokeStyle;

      // Makes neon glow brighter by color blending
      ctx.globalCompositeOperation = "lighter";

      ctx.stroke();

      ctx.globalCompositeOperation = "source-over";
    }
  }
}



      requestAnimationFrame(animate);
    };

    animate();

    return () => window.removeEventListener("resize", resize);
  }, []);

  // File upload handler
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.pdf') && !file.name.endsWith('.txt')) {
      setError('Please upload a PDF or TXT file');
      return;
    }

    setResumeFile(file);
    setError('');
  };

  // Resume analyzing handler
  const handleAnalyzeResume = async () => {
    if (!resumeFile || !formData.role) {
      setError('Please upload a resume and enter job role');
      return;
    }

    setLoading(true);
    const formPayload = new FormData();
    formPayload.append('file', resumeFile);
    formPayload.append('role', formData.role);

    try {
      const response = await fetch(API_ENDPOINTS.uploadResume, {
        method: 'POST',
        body: formPayload,
      });

      if (!response.ok) throw new Error('Failed to analyze resume');

      const data = await response.json();
      setResumeResults(data);
    } catch (err) {
      setError('Error analyzing resume');
    } finally {
      setLoading(false);
    }
  };

  const handleProceed = () => {
    navigate('/interview', {
      state: {
        company: formData.company,
        role: formData.role,
        numQuestions: formData.numQuestions,
        resumeSummary: resumeResults?.resume_summary,
      },
    });
  };

  return (
    <div className="min-h-screen bg-[#0b0f17] relative overflow-hidden">

      {/* 🔥 ELECTRIC BACKGROUND */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full opacity-60"
        style={{ zIndex: 0 }}
      ></canvas>

      {/* Slight Brightness Overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#0b1522]/60 to-black/80 z-0"></div>

      {/* MAIN CONTENT */}
      <div className="relative z-10 container mx-auto px-6 py-16 max-w-4xl">
        <h1 className="text-6xl font-extrabold text-white drop-shadow-[0_0_25px_#00ffd5] text-center">
          Resume Analyzer
        </h1>
        <p className="text-teal-300 text-xl mt-2 text-center font-semibold">
          Upload your resume and let AI evaluate your profile
        </p>

        {/* CARD */}
        <div className="mt-14 bg-black/40 border border-teal-400/20 shadow-[0_0_40px_#00ffd52f] rounded-3xl p-10 backdrop-blur-lg">

          {/* Company */}
          <label className="text-white font-medium">Company Name</label>
          <input
            type="text"
            className="mt-2 w-full bg-black/50 border border-teal-300/30 text-white px-4 py-3 rounded-lg"
            placeholder="Enter company name"
            value={formData.company}
            onChange={(e) => setFormData({ ...formData, company: e.target.value })}
          />

          {/* Role */}
          <label className="text-white font-medium mt-6 block">Job Role</label>
          <input
            type="text"
            className="mt-2 w-full bg-black/50 border border-teal-300/30 text-white px-4 py-3 rounded-lg"
            placeholder="Enter job role"
            value={formData.role}
            onChange={(e) => setFormData({ ...formData, role: e.target.value })}
          />

          {/* Slider */}
          <label className="text-white font-medium mt-6 block">
            Number of Questions: {formData.numQuestions}
          </label>
          <input
            type="range"
            min="1"
            max="15"
            value={formData.numQuestions}
            onChange={(e) =>
              setFormData({ ...formData, numQuestions: parseInt(e.target.value) })
            }
            className="w-full mt-2 accent-teal-300"
          />

          {/* Upload */}
          <label className="text-white font-medium mt-8 block">Resume Upload</label>
          <div className="mt-3">
            <input type="file" id="upload" className="hidden" onChange={handleFileChange} />
            <label
              htmlFor="upload"
              className="flex flex-col items-center justify-center border-dashed border-2 border-teal-300/40 bg-black/40 p-10 rounded-xl cursor-pointer hover:border-teal-300 transition"
            >
              {resumeFile ? (
                <>
                  <FileText className="text-teal-300 w-10 h-10" />
                  <p className="text-white mt-2">{resumeFile.name}</p>
                </>
              ) : (
                <>
                  <Upload className="text-teal-300 w-10 h-10" />
                  <p className="text-white mt-2">Click to upload resume (PDF/TXT)</p>
                </>
              )}
            </label>
          </div>

          {/* Error */}
          {error && <p className="mt-4 text-red-400">{error}</p>}

          {/* Analyze Button */}
          <button
            onClick={handleAnalyzeResume}
            className="mt-8 w-full py-4 bg-teal-300 text-black font-bold rounded-xl hover:bg-teal-200 transition flex items-center justify-center gap-2"
          >
            {loading ? <Loader2 className="animate-spin" /> : "Analyze Resume"}
          </button>

          {/* Results */}
          {resumeResults && (
            <div className="mt-10 space-y-6">
              <div className="bg-black/50 p-6 rounded-xl border border-teal-300/30">
                <h3 className="text-teal-300 text-xl font-semibold">Resume Summary</h3>
                <p className="text-white mt-2">{resumeResults.resume_summary}</p>
              </div>

              <div className="bg-black/50 p-6 rounded-xl border border-teal-300/30">
                <h3 className="text-teal-300 text-xl font-semibold">Evaluation</h3>
                <p className="text-white mt-2 whitespace-pre-line">{resumeResults.evaluation}</p>
              </div>

              <button
                onClick={handleProceed}
                className="w-full py-4 bg-gradient-to-r from-teal-300 to-cyan-400 text-black font-bold rounded-xl"
              >
                Proceed to Interview
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ResumeAnalyzer;
