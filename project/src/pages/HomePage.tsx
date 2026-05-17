import { useNavigate } from "react-router-dom";
import Lottie from "lottie-react";
import animationData from "../assets/animations/LandingPageAnim.json"; // your exact path

const HomePage = () => {
  const navigate = useNavigate();

  return (
    <div className="relative w-full h-screen overflow-hidden bg-[#05060a] text-white flex items-center justify-center">

      {/* 🔥 FULLSCREEN BACKGROUND ANIMATION */}
      <Lottie
        animationData={animationData}
        loop
        autoplay
        className="absolute inset-0 w-full h-full object-cover opacity-100 pointer-events-none"
      />

      {/* 🔥 OVERLAY CONTENT */}
      <div className="relative z-10 flex flex-col items-center text-center px-4">
        {/* TITLE */}
        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-4">
          HireMate AI
        </h1>

        {/* TAGLINE */}
        <p className="text-lg md:text-2xl text-teal-300 mb-10 font-bold">
           From Candidacy to Career
        </p>


        {/* START INTERVIEW BUTTON */}
        <button
          onClick={() => navigate("/resume-analyzer")}
          className="px-10 py-4 bg-teal-400 hover:bg-teal-300 text-black font-semibold text-lg rounded-full shadow-xl transition-all duration-200"
        >
          Start Interview
        </button>
      </div>

      {/* DARK GRADIENT OVERLAY FOR BETTER VISIBILITY */}
      <div className="absolute inset-0 bg-gradient-to-b from-black/10 to-black/40 pointer-events-none"></div>
    </div>
  );
};

export default HomePage;
