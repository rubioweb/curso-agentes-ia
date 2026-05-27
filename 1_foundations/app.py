from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr 

# Cargamos las variables de entorno desde el archivo .env
load_dotenv(override=True)

def push(text):
    """Envía notificaciones push en tiempo real a tu móvil mediante Pushover con control de errores."""
    token = os.getenv("PUSHOVER_TOKEN")
    user = os.getenv("PUSHOVER_USER")
    
    # Imprime en los logs de Hugging Face si las claves están vacías
    if not token or not user:
        print("ERROR: PUSHOVER_TOKEN o PUSHOVER_USER no están configurados en el entorno.", flush=True)
        return

    try:
        response = requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": token,
                "user": user,
                "message": text,
            },
            timeout=5
        )
        print(f"Resultado Pushover API: {response.status_code} - {response.text}", flush=True)
    except Exception as e:
        print(f"Error crítico al enviar Pushover: {e}", flush=True)


def record_user_details(email, name="Name not provided", notes="not provided"):
    """Función que se ejecuta cuando el usuario proporciona sus datos de contacto."""
    push(f"Registrando interés de {name} con email {email} y notas {notes}")
    return {"recorded": "ok"}

def record_unknown_question(question):
    """Función que se ejecuta cuando la IA no conoce la respuesta."""
    push(f"Pregunta no respondida registrada: {question}")
    return {"recorded": "ok"}

# JSON para que Llama entienda mejor el contexto de las herramientas
record_user_details_json = {
    "name": "record_user_details",
    "description": "Utiliza esta herramienta única y exclusivamente cuando el usuario te proporcione explícitamente su correo electrónico.",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "La dirección de correo electrónico del usuario"
            },
            "name": {
                "type": "string",
                "description": "El nombre del usuario, si lo proporciona"
            },
            "notes": {
                "type": "string",
                "description": "Breve resumen del motivo del contacto"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Utiliza esta herramienta para registrar cualquier pregunta técnica o personal sobre Jose Manuel que no puedas responder con la información disponible.",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "La pregunta exacta que no se pudo responder"
            },
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": record_user_details_json},
        {"type": "function", "function": record_unknown_question_json}]


class Me:

    def __init__(self):
        self.openai = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv("GROQ_API_KEY")
        )
        
        self.name = "Jose Manuel"
        
        # Ingesta de datos de mi perfil de LinkedIn
        reader = PdfReader("me/Profile.pdf")
        self.linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text
                
        # Ingesta de datos de mi resumen profesional personalizado
        with open("me/summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()

    def handle_tool_call(self, tool_calls):
        """Mapeador dinámico encargado de buscar y ejecutar las funciones nativas de Python."""
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Herramienta llamada: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({"role": "tool", "content": json.dumps(result), "tool_call_id": tool_call.id})
        return results
    
    def system_prompt(self):
        """Define las instrucciones de comportamiento, la personalidad y el conocimiento del clon."""
        system_prompt = f"Actúas como {self.name}. Estás respondiendo preguntas en tu sitio web personal. " \
                        f"Respondes de manera profesional, carismática y directa a reclutadores o clientes. " \
                        f"REGLA CRÍTICA DE HERRAMIENTAS:\n" \
                        f"1. NO inventes datos. Si el usuario no te ha dado su email, NO uses 'record_user_details' con valores como 'unknown'. " \
                        f"2. Pide el correo amablemente si quieren contactar contigo. " \
                        f"3. Cuando decidas llamar a una herramienta, hazlo de manera limpia, sin escribir código JSON o formatos extraños como '<function=...>' en tu respuesta de texto."

        system_prompt += f"\n\n## Tu Resumen Profesional:\n{self.summary}\n\n## Tu Perfil de LinkedIn:\n{self.linkedin}\n\n"
        system_prompt += f"Conversa siempre en primera persona del singular, tú eres {self.name}."
        return system_prompt
    
    def chat(self, message, history):
        """Gestiona el flujo conversacional solucionando el bucle infinito de Groq."""
        clean_history = []
        for h in history:
            clean_history.append({
                "role": h["role"],
                "content": h["content"]
            })

        messages = [{"role": "system", "content": self.system_prompt()}] + clean_history + [{"role": "user", "content": message}]
        
        final_text_response = ""
        done = False
        
        while not done:
            response = self.openai.chat.completions.create(
                model="llama-3.3-70b-versatile", 
                messages=messages, 
                tools=tools
            )
            
            message_obj = response.choices[0].message
            
            # Si Llama generó texto junto con la llamada o al final, lo guardamos
            if message_obj.content:
                final_text_response = message_obj.content
            
            # Verificamos si Groq ha solicitado la ejecución de alguna herramienta
            if message_obj.tool_calls:
                tool_calls = message_obj.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(message_obj)
                messages.extend(results)
                # Opcional: Podríamos forzar un break aquí si ya capturamos texto, 
                # pero dejamos que complete el ciclo para actualizar el contexto interno.
            else:
                done = True
                
        # Corrección de formato para limpiar respuestas en caso de residuos de Llama
        if not final_text_response:
            final_text_response = "¡Entendido! He tomado nota de ello."
            
        return final_text_response
    

if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(me.chat, type="messages").launch()