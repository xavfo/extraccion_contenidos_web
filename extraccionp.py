import asyncio
from crawl4ai import *
from bs4 import BeautifulSoup
import csv
from datetime import datetime
from urllib.parse import urljoin

async def extract_doctor_data(url, crawler):
    result = await crawler.arun(url=url)
    soup = BeautifulSoup(result.html, 'html.parser')
    
    doctors = []
    
    # Los médicos están en divs con clase 'negocio' dentro de 'block rounded'
    doctor_blocks = soup.find_all('div', class_='block rounded')
    
    for block in doctor_blocks:
        # Verificamos que sea un bloque de médico (tiene la clase 'negocio' dentro)
        negocio = block.find('div', class_='negocio')
        if not negocio:
            continue
            
        doctor = {}
        
        # Extraer nombre
        name_tag = block.find('h3')
        if name_tag:
            doctor['Nombre'] = name_tag.get_text(strip=True)
        
        # Extraer dirección
        address_tag = block.find('span', class_='street-address')
        locality_tag = block.find('span', class_='locality')
        if address_tag and locality_tag:
            doctor['Dirección'] = f"{address_tag.get_text(strip=True)}, {locality_tag.get_text(strip=True)}"
        
        # Extraer teléfono
        phone_tag = block.find('span', class_='telefono')
        if phone_tag and 'content' in phone_tag.attrs:
            doctor['Teléfono'] = phone_tag['content']
        else:
            # Buscar en la versión móvil
            mobile_phone = block.find('a', class_='tel')
            if mobile_phone:
                doctor['Teléfono'] = mobile_phone.get_text(strip=True)
        
        # Extraer cédula profesional (no está visible en el HTML proporcionado)
        # Podría estar en el perfil individual
        doctor['Cédula'] = 'No disponible en lista'
        
        if doctor.get('Nombre'):  # Solo añadir si tenemos al menos el nombre
            doctors.append(doctor)
    
    # Encontrar la próxima página
    next_page = None
    pagination = soup.find('div', id='buscador_paginador')
    if pagination:
        next_link = pagination.find('a', class_='pagination-next')
        if next_link:
            next_page = urljoin(url, next_link['href'])
    
    return doctors, next_page

async def main():
    # Solicitar URL inicial al usuario
    base_url = input("Ingresa la URL inicial (ej: https://masquemedicos.ec/medicos-generales_ambato/): ").strip()
    if not base_url.startswith('http'):
        print("URL inválida. Debe comenzar con http:// o https://")
        return
    
    print("\nIniciando extracción de datos...")
    
    try:
        all_doctors = []
        current_url = base_url
        page_count = 0
        
        async with AsyncWebCrawler() as crawler:
            while current_url:
                page_count += 1
                print(f"\nProcesando página {page_count}: {current_url}")
                
                doctors_data, next_page = await extract_doctor_data(current_url, crawler)
                all_doctors.extend(doctors_data)
                
                print(f"Encontrados {len(doctors_data)} médicos en esta página")
                print(f"Total acumulado: {len(all_doctors)} médicos")
                
                current_url = next_page
                
                # Pequeña pausa para no saturar el servidor
                await asyncio.sleep(2)
        
        if not all_doctors:
            print("\nNo se encontraron datos. Verifica que la URL sea correcta.")
            return
        
        # Generar nombre de archivo con fecha
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"medicos_ambato_{timestamp}.csv"
        
        # Guardar en CSV
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Nombre', 'Dirección', 'Teléfono', 'Cédula']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for doctor in all_doctors:
                writer.writerow(doctor)
        
        print(f"\nExtracción completada:")
        print(f"- Páginas procesadas: {page_count}")
        print(f"- Total de médicos extraídos: {len(all_doctors)}")
        print(f"- Datos guardados en: {filename}")
        
        # Mostrar muestra de datos
        print("\nMuestra de datos (primeros 5 registros):")
        for i, doc in enumerate(all_doctors[:5], 1):
            print(f"\n{i}. Nombre: {doc.get('Nombre', '')}")
            print(f"   Dirección: {doc.get('Dirección', '')}")
            print(f"   Teléfono: {doc.get('Teléfono', '')}")
            print(f"   Cédula: {doc.get('Cédula', '')}")
            
    except Exception as e:
        print(f"\nError durante la extracción: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
