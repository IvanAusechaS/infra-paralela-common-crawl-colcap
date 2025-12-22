/**
 * Navbar Component - News2Market
 * 
 * Barra de navegación principal
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
          <span className="logo-icon">📰</span>
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
