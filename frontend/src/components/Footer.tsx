/**
 * Footer Component - News2Market
 */

import { Link } from "react-router-dom";
import "./Footer.scss";

const Footer = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="footer">
      <div className="footer-container">
        <div className="footer-content">
          <div className="footer-section">
            <h3>News2Market</h3>
            <p>
              Sistema distribuido para análisis de correlación entre noticias
              económicas y el índice COLCAP
            </p>
          </div>

          <div className="footer-section">
            <h4>Navegación</h4>
            <ul>
              <li>
                <Link to="/">Inicio</Link>
              </li>
              <li>
                <Link to="/analysis">Análisis</Link>
              </li>
              <li>
                <Link to="/results">Resultados</Link>
              </li>
            </ul>
          </div>

          <div className="footer-section">
            <h4>Recursos</h4>
            <ul>
              <li>
                <a
                  href="/docs/ARCHITECTURE.md"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Arquitectura
                </a>
              </li>
              <li>
                <a
                  href="/docs/FRONTEND_DESIGN.md"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Diseño
                </a>
              </li>
              <li>
                <a
                  href="/docs/INSTALLATION.md"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Instalación
                </a>
              </li>
            </ul>
          </div>

          <div className="footer-section">
            <h4>Servicios Backend</h4>
            <ul>
              <li>API Gateway: :8000</li>
              <li>Data Acquisition: :8001</li>
              <li>Text Processor: :8002</li>
              <li>Correlation: :8003</li>
            </ul>
          </div>
        </div>

        <div className="footer-bottom">
          <p>
            &copy; {currentYear} News2Market. Infraestructuras Paralelas y
            Distribuidas.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
