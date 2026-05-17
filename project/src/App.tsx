import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import ResumeAnalyzer from './pages/ResumeAnalyzer';
import InterviewScreen from './pages/InterviewScreen';
import ResultsPage from './pages/ResultsPage';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/resume-analyzer" element={<ResumeAnalyzer />} />
        <Route path="/interview" element={<InterviewScreen />} />
        <Route path="/results" element={<ResultsPage />} />
      </Routes>
    </Router>
  );
}

export default App;
