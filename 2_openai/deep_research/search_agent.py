from agents import Agent, WebSearchTool, ModelSettings

# Instrucciones del sistema en castellano: define el rol y el formato estricto del resumen
INSTRUCTIONS = (
    "Eres un asistente de investigación. Dado un término de búsqueda, buscas en la web ese término y "
    "produces un resumen conciso de los resultados. El resumen debe tener entre 2 y 3 párrafos y menos de 300 "
    "palabras. Captura los puntos principales. Escribe de forma sucinta, no es necesario que uses frases completas "
    "ni una buena gramática. Esto será consumido por alguien que está sintetizando un informe, por lo que es vital "
    "que captures la esencia e ignores el contenido de relleno. No incluyas ningún comentario adicional que no sea el resumen en sí."
)

# Inicialización y configuración del agente de búsqueda
search_agent = Agent(
    name="Agente de Búsqueda",                       # Nombre del agente en castellano
    instructions=INSTRUCTIONS,                       # Le asignamos las instrucciones traducidas
    # Herramientas del agente: Le damos acceso a la web con un contexto bajo (para ahorrar tokens/memoria)
    tools=[WebSearchTool(search_context_size="low")],
    model="gemini/gemini-2.5-flash",                 # CAMBIADO: Ajustado a tu modelo de Gemini disponible
    # Configuración del modelo: Forzamos a que el agente use la herramienta de búsqueda obligatoriamente
    model_settings=ModelSettings(tool_choice="required"),
)