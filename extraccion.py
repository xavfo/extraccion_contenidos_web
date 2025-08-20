import asyncio
from crawl4ai import *
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import random
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración avanzada
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9",
    "Referer": "https://www.google.com/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0"
}

COOKIES = {
    "country": "ec",
    "language": "es",
    "cookie_consent": "true"
}

# Lista de User-Agents alternativos
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
]

async def get_random_delay():
    """Retorna un delay aleatorio entre 2 y 5 segundos"""
    return random.uniform(2, 5)

async def rotate_user_agent():
    """Rota el User-Agent aleatoriamente"""
    HEADERS["User-Agent"] = random.choice(USER_AGENTS)

async def fetch_with_retry(crawler, url, strategy, max_retries=3):
    for attempt in range(max_retries):
        try:
            await rotate_user_agent()
            delay = await get_random_delay()
            logger.info(f"Intento {attempt + 1} con estrategia {strategy['name']} - Esperando {delay:.1f}s")
            await asyncio.sleep(delay)
            
            result = await crawler.arun(
                url=url,
                extraction_strategy=strategy['strategy'],
                extraction_config=strategy.get('config'),
                render_js=strategy.get('render_js', True),
                headers=HEADERS,
                cookies=COOKIES,
                timeout=strategy.get('timeout', 45),
                wait_for_selectors=[".specialty-profile-card"],
                wait_time=5000
            )
            
            if result and result.extracted_content:
                logger.info(f"Éxito con {strategy['name']}")
                return result
                
        except Exception as e:
            logger.error(f"Error en intento {attempt + 1}: {str(e)}")
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(5)  # Espera más antes de reintentar
    
    return None

async def extract_content(url):
    strategies = [
        {
            "name": "Dynamic Rendering",
            "strategy": "DynamicRenderer",
            "render_js": True,
            "timeout": 60,
            "config": {
                "wait_until": "networkidle2",
                "viewport": {"width": 1920, "height": 1080}
            }
        },
        {
            "name": "DOM Extraction",
            "strategy": "DOMExtraction",
            "render_js": True,
            "timeout": 45
        },
        {
            "name": "Raw HTML",
            "strategy": "RawHtmlExtraction",
            "render_js": False,
            "timeout": 30
        }
    ]
    
    async with AsyncWebCrawler() as crawler:
        for strategy in strategies:
            try:
                result = await fetch_with_retry(crawler, url, strategy)
                if result:
                    return result.extracted_content
            except Exception as e:
                logger.error(f"Fallo con estrategia {strategy['name']}: {str(e)}")
                continue
    
    logger.error("Todas las estrategias fallaron")
    return None

def parse_doctor_data(html_content):
    """Extrae datos de médicos del HTML usando BeautifulSoup"""
    if not html_content:
        raise ValueError("No hay contenido HTML para analizar")
        
    soup = BeautifulSoup(html_content, 'html.parser')
    doctors = []
    
    doctor_cards = soup.find_all('a', class_='specialty-profile-card')
    logger.info(f"Encontradas {len(doctor_cards)} tarjetas de médicos")
    
    for card in doctor_cards:
        try:
            # Extraer datos básicos
            name = card.find('div', class_='specialty-profile-card__title').get_text(strip=True)
            specialty = card.find('div', class_='specialty-profile-card__job').get_text(strip=True)
            location = card.find('div', class_='specialty-profile-card__location').get_text(strip=True)
            
            # Construir URL completa
            profile_path = card.get('href', '')
            profile_url = f"https://www.doctoranytime.ec{profile_path}" if profile_path.startswith('/') else profile_path
            
            doctors.append({
                "Nombre": name,
                "Especialidad": specialty,
                "Ubicación": location,
                "Perfil": profile_url,
                "Extraído el": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
        except Exception as e:
            logger.warning(f"Error procesando tarjeta: {str(e)}")
            continue
    
    return doctors

async def main():
    url = "https://www.doctoranytime.ec/lp/ambato"
    
    logger.info(f"Iniciando extracción de: {url}")
    start_time = time.time()
    
    try:
        content = await extract_content(url)
        
        if not content:
            logger.error("No se pudo obtener el contenido de la página")
            return
        
        # Procesar los datos
        doctors = parse_doctor_data(content)
        
        if not doctors:
            logger.error("No se encontraron médicos en la página")
            return
            
        # Crear DataFrame y guardar
        df = pd.DataFrame(doctors)
        output_file = f"doctors_ambato_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(output_file, index=False)
        
        logger.info(f"\n✅ Extracción completada con éxito en {time.time()-start_time:.1f} segundos")
        logger.info(f"Total de médicos extraídos: {len(df)}")
        logger.info(f"Datos guardados en: {output_file}")
        
        # Mostrar muestra de datos
        print("\nMuestra de datos extraídos:")
        print(df.head())
        
    except Exception as e:
        logger.error(f"Error en el proceso principal: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
