/**
 * Navbar Component - News2Market
 * Navigation bar with custom logo
 */

import { Link, useLocation } from 'react-router-dom';
import './Navbar.scss';

const Navbar = () => {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-logo">
          <svg className="logo-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" fill="none">
            <circle cx="100" cy="100" r="95" fill="#1e40af" opacity="0.1"/>
            <g id="newspaper-base">
              <rect x="50" y="55" width="100" height="90" rx="4" fill="#1e40af" stroke="#1e40af" strokeWidth="2"/>
              <rect x="55" y="60" width="90" height="80" rx="2" fill="white"/>
              <line x1="62" y1="70" x2="105" y2="70" stroke="#1e40af" strokeWidth="2" strokeLinecap="round"/>
              <line x1="62" y1="78" x2="95" y2="78" stroke="#1e40af" strokeWidth="1.5" strokeLinecap="round" opacity="0.6"/>
              <line x1="62" y1="85" x2="100" y2="85" stroke="#1e40af" strokeWidth="1.5" strokeLinecap="round" opacity="0.6"/>
            </g>
            <g id="graph-line">
              <polyline points="65,120 80,110 95,115 110,100 125,105 135,90" stroke="#059669" strokeWidth="3" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
              <circle cx="65" cy="120" r="3" fill="#059669"/>
              <circle cx="80" cy="110" r="3" fill="#059669"/>
              <circle cx="95" cy="115" r="3" fill="#059669"/>
              <circle cx="110" cy="100" r="3" fill="#059669"/>
              <circle cx="125" cy="105" r="3" fill="#059669"/>
              <circle cx="135" cy="90" r="4" fill="#059669"/>
            </g>
            <g id="decorative">
              <circle cx="115" cy="70" r="2" fill="#059669" opacity="0.8"/>
              <circle cx="125" cy="73" r="2" fill="#059669" opacity="0.6"/>
              <circle cx="135" cy="68" r="2" fill="#059669" opacity="0.8"/>
            </g>
          </svg>
          <span className="logo-text">News2Market</span>
        </Link>

        <ul className="navbar-menu">
          <li>
            <Link
              to="/"
              className={`navbar-link ${isActive('/') ? 'active' : ''}`}
            >
              Inicio
            </Link>
          </li>
          <li>
            <Link
              to="/analysis"
              className={`navbar-link ${isActive('/analysis') ? 'active' : ''}`}
            >
              Análisis
            </Link>
          </li>
          <li>
            <Link
              to="/results"
              className={`navbar-link ${isActive('/results') ? 'active' : ''}`}
            >
              Resultados
            </Link>
          </li>
        </ul>
      </div>
    </nav>
  );
};

export default Navbar;
