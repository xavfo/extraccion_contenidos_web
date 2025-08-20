# Extracción de Datos de Médicos desde Directorios Médicos con crawl4ai

Esta aplicación utiliza [crawl4ai](https://github.com/crawl4ai/crawl4ai) para automatizar la extracción de información de médicos desde diferentes directorios médicos en la web.

## Características

- Extracción automatizada de datos relevantes (nombre, especialidad, dirección, teléfono, etc.).
- Configuración flexible para distintos sitios web de directorios médicos.
- Exportación de resultados en formatos CSV y JSON.
- Manejo de paginación y protección contra bloqueos básicos.

## Requisitos

- Python 3.8+
- crawl4ai
- Otros paquetes especificados en `requirements.txt`

## Instalación

1. Clona el repositorio:
   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd extraccion_contenidos_web
   ```

2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Uso

1. Configura los parámetros de extracción en el archivo de configuración (por ejemplo, `config.yaml`).
2. Ejecuta el crawler:
   ```bash
   python main.py
   ```
3. Los datos extraídos se guardarán en la carpeta `output/`.

## Personalización

- Puedes adaptar los selectores y reglas de extracción en el archivo de configuración para nuevos sitios.
- Consulta la documentación de crawl4ai para más opciones avanzadas.

## Licencia

Este proyecto se distribuye bajo la licencia MIT.

## Créditos

- Basado en [crawl4ai](https://github.com/crawl4ai/crawl4ai)