import asyncio
from crawl4ai import *
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración avanzada
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9",
    "Referer": "https://www.doctoranytime.ec/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
}

COOKIES = {
    "country": "ec",
    "language": "es"
}

PROXY = None  # Puedes configurar un proxy aquí si es necesario

async def fetch_with_retry(crawler, url, strategy, max_retries=3):
    for attempt in range(max_retries):
        try:
            logger.info(f"Intento {attempt + 1} con estrategia {strategy['name']}")
            
            result = await crawler.arun(
                url=url,
                extraction_strategy=strategy['strategy'],
                extraction_config=strategy.get('config'),
                render_js=strategy.get('render_js', False),
                headers=HEADERS,
                cookies=COOKIES,
                proxy=PROXY,
                timeout=strategy.get('timeout', 30)
            )
            
            if result and result.extracted_content:
                logger.info(f"Éxito con {strategy['name']}")
                return result
                
        except Exception as e:
            logger.error(f"Error en intento {attempt + 1} con {strategy['name']}: {str(e)}")
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2)  # Espera antes de reintentar
    
    return None

async def extract_content(url):
    strategies = [
        {
            "name": "Full Browser Simulation",
            "strategy": "DynamicRenderer",
            "render_js": True,
            "timeout": 60,
            "config": {
                "wait_for_selectors": [".specialty-profile-card"],
                "wait_time": 5000
            }
        },
        {
            "name": "DOM Extraction",
            "strategy": "DOMExtraction",
            "render_js": True,
            "timeout": 40
        },
        {
            "name": "Raw HTML Fallback",
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
    soup = BeautifulSoup(html_content, 'html.parser')
    doctors = []
    
    doctor_cards = soup.find_all('a', class_='specialty-profile-card')
    logger.info(f"Encontradas {len(doctor_cards)} tarjetas de médicos")
    
    for card in doctor_cards:
        try:
            # Extraer datos
            name = card.find('div', class_='specialty-profile-card__title').get_text(strip=True)
            specialty = card.find('div', class_='specialty-profile-card__job').get_text(strip=True)
            location = card.find('div', class_='specialty-profile-card__location').get_text(strip=True)
            
            # Extraer imagen si existe
            img_div = card.find('div', class_='specialty-profile-card__image')
            image_url = img_div.find('img')['src'] if img_div and img_div.find('img') else None
            
            # Extraer rating si existe
            rating_div = card.find('div', class_='detailed-rating')
            rating = None
            if rating_div:
                rating_value = rating_div.find('div', class_='detailed-rating__value')
                rating = rating_value.get_text(strip=True) if rating_value else None
            
            doctors.append({
                "nombre": name,
                "especialidad": specialty,
                "ubicacion": location,
                "imagen": image_url,
                "rating": rating,
                "enlace": card.get('href', '').split('?')[0]  # Limpiar URL
            })
            
        except Exception as e:
            logger.error(f"Error procesando tarjeta: {str(e)}")
            continue
    
    return doctors

async def main():
    #url = "https://www.doctoranytime.ec/lp/ambato"
    url = "https://masquemedicos.ec/medicos-generales_ambato/"
    logger.info(f"Iniciando extracción de {url}")
    content = await extract_content(url)
    
    if not content:
        logger.error("No se pudo obtener contenido de la página")
        return
    
    # Guardar HTML para depuración
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"doctoranytime_{timestamp}.html", "w", encoding="utf-8") as f:
        f.write(content)
    
    # Procesar datos
    try:
        doctors = parse_doctor_data(content)
        if not doctors:
            raise ValueError("No se encontraron médicos en el contenido")
        
        df = pd.DataFrame(doctors)
        
        # Limpiar datos
        df['enlace'] = 'https://www.doctoranytime.ec' + df['enlace']
        
        # Guardar resultados
        excel_file = f"doctors_ambato_{timestamp}.xlsx"
        df.to_excel(excel_file, index=False)
        logger.info(f"Datos guardados en {excel_file}")
        logger.info(f"Total de médicos extraídos: {len(df)}")
        
    except Exception as e:
        logger.error(f"Error procesando datos: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
