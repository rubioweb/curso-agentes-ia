from pydantic import BaseModel, Field
from agents import Agent

# Instrucciones del sistema para definir el rol de investigador sénior y la extensión del informe
INSTRUCTIONS = (
    "Eres un investigador sénior encargado de redactar un informe cohesionado para una consulta de investigación. "
    "Se te proporcionará la consulta original y una investigación inicial realizada por un asistente de investigación.\n"
    "Primero debes proponer un esquema para el informe que describa su estructura y flujo. "
    "Luego, genera el informe y devuélvelo como tu resultado final.\n"
    "El resultado final debe estar en formato markdown, y debe ser extenso y detallado. "
    "Apunta a entre 5 y 10 páginas de contenido, al menos 1000 palabras."
)

# Estructura de datos requerida para la entrega del informe final
class ReportData(BaseModel):
    # Un resumen ejecutivo muy breve de lo que se descubrió
    short_summary: str = Field(description="Un resumen corto de 2-3 frases de los hallazgos.")

    # El cuerpo principal del informe formateado con títulos, negritas y listas en Markdown
    markdown_report: str = Field(description="El informe final.")

    # Ideas o líneas de investigación adicionales que el usuario podría explorar después
    follow_up_questions: list[str] = Field(description="Temas sugeridos para investigar más a fondo.")

# Inicialización y configuración del agente redactor
writer_agent = Agent(
    name="Agente Redactor",              # Nombre del agente 
    instructions=INSTRUCTIONS,          # Asignación de las instrucciones traducidas
    model="gemini/gemini-2.5-flash",    # Mantenemos Gemini para procesar y generar grandes volúmenes de texto
    output_type=ReportData,             # Estructuramos la salida final con el esquema Pydantic
)