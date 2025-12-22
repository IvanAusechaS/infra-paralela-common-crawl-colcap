/**
 * News2Market - Main Application Component
 *
 * Aplicación React para análisis de correlación noticias-COLCAP
 */

import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import HomePage from "./pages/HomePage";
import AnalysisPage from "./pages/AnalysisPage";
import ResultsPage from "./pages/ResultsPage";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import "./styles/global.scss";

function App() {
  return (
    <Router>
      <div className="app">
        <Navbar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/analysis" element={<AnalysisPage />} />
            <Route path="/results" element={<ResultsPage />} />
          </Routes>
        </main>
        <Footer />
        <ToastContainer />
      </div>
    </Router>
  );
}

export default App;
