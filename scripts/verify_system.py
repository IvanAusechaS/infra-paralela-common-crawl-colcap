#!/usr/bin/env python3
"""
Script de verificación completa del sistema News2Market
Verifica que todos los servicios estén funcionando correctamente
"""

import requests
import time
import sys
from typing import Dict, List, Tuple

# Colores para terminal
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

class SystemVerifier:
    def __init__(self):
        self.services = {
            'API Gateway': 'http://localhost:8000',
            'Data Acquisition': 'http://localhost:8001',
            'Text Processor': 'http://localhost:8002',
            'Correlation Service': 'http://localhost:8003',
        }
        self.results = []
    
    def print_header(self, text: str):
        print(f"\n{BLUE}{'='*60}")
        print(f"{text:^60}")
        print(f"{'='*60}{RESET}\n")
    
    def print_success(self, text: str):
        print(f"{GREEN}✓ {text}{RESET}")
    
    def print_error(self, text: str):
        print(f"{RED}✗ {text}{RESET}")
    
    def print_warning(self, text: str):
        print(f"{YELLOW}⚠ {text}{RESET}")
    
    def print_info(self, text: str):
        print(f"{BLUE}ℹ {text}{RESET}")
    
    def check_service_health(self, name: str, url: str) -> Tuple[bool, str]:
        """Verifica el health endpoint de un servicio"""
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                return True, f"{name} está saludable"
            else:
                return False, f"{name} respondió con código {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, f"{name} no está accesible (conexión rechazada)"
        except requests.exceptions.Timeout:
            return False, f"{name} no respondió a tiempo"
        except Exception as e:
            return False, f"{name} error: {str(e)}"
    
    def check_root_endpoint(self, name: str, url: str) -> Tuple[bool, str]:
        """Verifica el endpoint raíz de un servicio"""
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return True, f"{name} root endpoint: {data}"
            else:
                return False, f"{name} root respondió con código {response.status_code}"
        except Exception as e:
            return False, f"{name} root error: {str(e)}"
    
    def test_text_processor_process(self) -> Tuple[bool, str]:
        """Prueba el endpoint de procesamiento de texto"""
        url = f"{self.services['Text Processor']}/process"
        test_article = {
            "article_id": 1,
            "content": "La bolsa de Colombia registró un incremento del 2% con el índice COLCAP alcanzando nuevos máximos. El mercado económico muestra señales positivas."
        }
        
        try:
            response = requests.post(url, json=test_article, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'cleaned_content' in data and 'sentiment_score' in data:
                    sentiment = data.get('sentiment_score', 0)
                    keywords = len(data.get('economic_keywords', {}))
                    return True, f"Procesamiento exitoso: {keywords} keywords, sentimiento={sentiment:.2f}"
                return False, "Respuesta sin datos esperados"
            return False, f"Error HTTP {response.status_code}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def test_correlation_service(self) -> Tuple[bool, str]:
        """Prueba el servicio de correlación"""
        url = f"{self.services['Correlation Service']}/colcap/2024-01-01/2024-01-10"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    return True, f"COLCAP data obtenida: {len(data)} registros"
                return False, "Respuesta vacía o formato incorrecto"
            return False, f"Error HTTP {response.status_code}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def test_worker_status(self) -> Tuple[bool, str]:
        """Verifica el estado de los workers del text processor"""
        url = f"{self.services['Text Processor']}/worker/status"
        
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                is_running = data.get('is_running', False)
                status = "✓ activo" if is_running else "⚠ detenido"
                return True, f"Worker {status}"
            return False, f"Error HTTP {response.status_code}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def run_all_checks(self):
        """Ejecuta todas las verificaciones"""
        self.print_header("VERIFICACIÓN DEL SISTEMA NEWS2MARKET")
        
        # 1. Health checks básicos
        self.print_info("1. Verificando health endpoints...")
        time.sleep(1)
        
        for name, url in self.services.items():
            success, message = self.check_service_health(name, url)
            if success:
                self.print_success(message)
            else:
                self.print_error(message)
            self.results.append((name + " Health", success))
        
        # 2. Endpoints raíz
        self.print_info("\n2. Verificando endpoints raíz...")
        time.sleep(1)
        
        for name, url in self.services.items():
            success, message = self.check_root_endpoint(name, url)
            if success:
                self.print_success(message)
            else:
                self.print_warning(message)
            self.results.append((name + " Root", success))
        
        # 3. Test funcional - Text Processor
        self.print_info("\n3. Probando procesamiento de texto...")
        time.sleep(1)
        
        success, message = self.test_text_processor_process()
        if success:
            self.print_success(f"Text Processor: {message}")
        else:
            self.print_error(f"Text Processor: {message}")
        self.results.append(("Text Processor Functional", success))
        
        # 4. Test funcional - Correlation Service
        self.print_info("\n4. Probando servicio de correlación...")
        time.sleep(1)
        
        success, message = self.test_correlation_service()
        if success:
            self.print_success(f"Correlation Service: {message}")
        else:
            self.print_error(f"Correlation Service: {message}")
        self.results.append(("Correlation Service Functional", success))
        
        # 5. Verificar workers
        self.print_info("\n5. Verificando workers distribuidos...")
        time.sleep(1)
        
        success, message = self.test_worker_status()
        if success:
            self.print_success(f"Workers: {message}")
        else:
            self.print_warning(f"Workers: {message}")
        self.results.append(("Workers Status", success))
        
        # Resumen final
        self.print_summary()
    
    def print_summary(self):
        """Imprime resumen de resultados"""
        self.print_header("RESUMEN DE VERIFICACIÓN")
        
        total = len(self.results)
        passed = sum(1 for _, success in self.results if success)
        failed = total - passed
        
        print(f"Total de pruebas: {total}")
        print(f"{GREEN}Exitosas: {passed}{RESET}")
        print(f"{RED}Fallidas: {failed}{RESET}")
        print(f"\nTasa de éxito: {(passed/total)*100:.1f}%")
        
        if failed == 0:
            self.print_success("\n✓ TODOS LOS SERVICIOS FUNCIONANDO CORRECTAMENTE")
            return 0
        else:
            self.print_error(f"\n✗ {failed} SERVICIOS CON PROBLEMAS")
            print("\nServicios con problemas:")
            for name, success in self.results:
                if not success:
                    print(f"  - {name}")
            return 1

def main():
    print(f"{BLUE}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║         NEWS2MARKET - SYSTEM VERIFICATION SCRIPT          ║")
    print("║              Universidad del Valle - 2024                 ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{RESET}")
    
    print("\nEsperando 5 segundos para que los servicios se estabilicen...")
    time.sleep(5)
    
    verifier = SystemVerifier()
    exit_code = verifier.run_all_checks()
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
