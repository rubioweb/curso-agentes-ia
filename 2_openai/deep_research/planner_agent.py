from pydantic import BaseModel, Field
from agents import Agent

# Número de búsquedas web que el agente debe planificar de forma obligatoria
HOW_MANY_SEARCHES = 3

# Instrucciones del sistema (System Prompt) que definen el rol y comportamiento del agente
INSTRUCTIONS = f"Eres un asistente de investigación útil. Dado un término de búsqueda, \
produce un conjunto de búsquedas web para realizar para responder la consulta. \
Salida: {HOW_MANY_SEARCHES} términos para consultar."

# Estructura de datos para cada una de las búsquedas individuales
class WebSearchItem(BaseModel):
    # Obliga al agente a justificar en castellano el porqué de esta búsqueda
    reason: str = Field(description="Tu razonamiento de por qué esta búsqueda es importante para la consulta.")
    # El término o frase exacta que se enviará al motor de búsqueda
    query: str = Field(description="El término de búsqueda a usar para la búsqueda web.")

# Estructura global que agrupa la lista completa de búsquedas planificadas
class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="Una lista de búsquedas web a realizar para responder la consulta.")
    
# Inicialización y configuración del agente de planificación
planner_agent = Agent(
    name="Agente de Planificación",      # Nombre identificativo del agente en castellano
    instructions=INSTRUCTIONS,          # Asignación de las instrucciones en castellano creadas arriba
    model="gemini/gemini-2.5-flash",    # CAMBIADO: Reemplazamos "gpt-4o-mini" por el modelo de Gemini 
    output_type=WebSearchPlan,          # Forzamos al agente a devolver el formato estructurado de Pydantic
)

