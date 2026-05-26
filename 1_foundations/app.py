
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
    """Envía notificaciones push en tiempo real a tu móvil mediante Pushover."""
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        }
    )


def record_user_details(email, name="Name not provided", notes="not provided"):
    """Función que se ejecuta cuando el usuario proporciona sus datos de contacto."""
    push(f"Registrando interés de {name} con email {email} y notas {notes}")
    return {"recorded": "ok"}

def record_unknown_question(question):
    """Función que se ejecuta cuando la IA no conoce la respuesta."""
    push(f"Pregunta no respondida registrada: {question}")
    return {"recorded": "ok"}

# FUNCION DE HERRAMIENTAS  PARA REGISTAR
#  descripciones del JSON para que Llama entienda mejor el contexto 
record_user_details_json = {
    "name": "record_user_details",
    "description": "Utiliza esta herramienta para registrar que un usuario está interesado en estar en contacto y proporcionó una dirección de correo electrónico",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "La dirección de correo electrónico de este usuario"
            },
            "name": {
                "type": "string",
                "description": "El nombre del usuario, si lo proporciona"
            },
            "notes": {
                "type": "string",
                "description": "Cualquier información adicional sobre la conversación que merezca ser registrada para dar contexto"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

# FUNCION PARA PREGUNTAS QUE NO SABE
#   descripciones del JSON 
record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Siempre use esta herramienta para registrar cualquier pregunta que no se pueda responder, ya que no sabía la respuesta",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "La pregunta que no se pudo responder"
            },
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

# Empaquetamos las herramientas en el formato requerido por la API
tools = [{"type": "function", "function": record_user_details_json},
        {"type": "function", "function": record_unknown_question_json}]


class Me:

    def __init__(self):
        #  Configurado el cliente para conectar con Groq usando tu API key del .env
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
        # [CAMBIO JOSÉ] Traducido el prompt del sistema íntegramente al castellano con refuerzo de herramientas
        system_prompt = f"Actúas como {self.name}. Estás respondiendo preguntas en el sitio web de {self.name}, " \
                        f"particularmente preguntas relacionadas con la carrera, antecedentes, habilidades y experiencia de {self.name}. " \
                        f"Tu responsabilidad es representar a {self.name} en las interacciones del sitio web de la manera más fiel posible. " \
                        f"Se te proporciona un resumen de la trayectoria de {self.name} y su perfil de LinkedIn que puedes utilizar para responder preguntas. " \
                        f"Sé profesional y carismático, como si estuvieras hablando con un cliente potencial o un futuro empleador que se topó con el sitio web. " \
                        f"Si no sabes la respuesta a alguna pregunta, utiliza tu herramienta 'record_unknown_question' para registrar la pregunta que no pudiste responder, " \
                        f"incluso si es sobre algo trivial o no relacionado con la carrera. " \
                        f"Si el usuario entabla una conversación, intenta orientarlo para que se ponga en contacto por correo electrónico; " \
                        f"pídele su correo electrónico y regíslalo utilizando tu herramienta 'record_user_details'."

        system_prompt += f"\n\n## Resumen:\n{self.summary}\n\n## Perfil de LinkedIn:\n{self.linkedin}\n\n"
        system_prompt += f"Con este contexto, por favor conversa con el usuario, manteniéndote siempre en el personaje de {self.name}."
        return system_prompt
    
    def chat(self, message, history):
        """Gestiona el flujo conversacional y resuelve el bucle de ejecución de herramientas."""
        # Implementado el filtro estricto anti-error 400 para eliminar los metadatos ocultos de Gradio
        clean_history = []
        for h in history:
            clean_history.append({
                "role": h["role"],
                "content": h["content"]
            })

        # Construimos el payload oficial combinando el prompt de sistema, el historial limpio y el nuevo mensaje
        messages = [{"role": "system", "content": self.system_prompt()}] + clean_history + [{"role": "user", "content": message}]
        
        done = False
        while not done:
            #  Cambiado el modelo de OpenAI por el modelo Llama 3.3 de Groq
            response = self.openai.chat.completions.create(
                model="llama-3.3-70b-versatile", 
                messages=messages, 
                tools=tools
            )
            
            # Verificamos si Groq ha solicitado la ejecución de alguna herramienta
            if response.choices[0].finish_reason == "tool_calls":
                message_obj = response.choices[0].message
                tool_calls = message_obj.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(message_obj)
                messages.extend(results)
            else:
                done = True
                
        return response.choices[0].message.content
    

if __name__ == "__main__":
    # Instanciamos la clase con tus configuraciones e iniciamos la interfaz gráfica
    me = Me()
    gr.ChatInterface(me.chat, type="messages").launch()