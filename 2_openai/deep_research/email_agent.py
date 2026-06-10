import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict

# CÓDIGO ORIGINAL COMENTADO (SENDGRID)
# import sendgrid
# from sendgrid.helpers.mail import Email, Mail, Content, To
from agents import Agent, function_tool


@function_tool
def send_email(subject: str, html_body: str) -> Dict[str, str]:
    """Envía un correo electrónico con el asunto y el cuerpo HTML proporcionados"""
    
    # --- CÓDIGO DE SENDGRID COMENTADO POR PETICIÓN ---
    # sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
    # from_email = Email("ed@edwarddonner.com")  # pon tu remitente verificado aquí
    # to_email = To("ed.donner@gmail.com")      # pon tu destinatario aquí
    # content = Content("text/html", html_body)
    # mail = Mail(from_email, to_email, subject, content).get()
    # response = sg.client.mail.send.post(request_body=mail)
    # print("Email response", response.status_code)
    # return "success"
    # --------------------------------------------------

    # --- NUEVA ALTERNATIVA: ENVÍO MEDIANTE GMAIL / SMTP ---
    try:
        # Recuperamos las credenciales desde las variables de entorno para mayor seguridad
        remitente = os.environ.get("GMAIL_USER", "tu_correo@gmail.com")
        # Nota: Para Gmail necesitas generar una "Contraseña de aplicación" en tu cuenta de Google
        password = os.environ.get("GMAIL_PASSWORD", "tu_contraseña_de_aplicacion")
        destinatario = "tu_correo_destino@gmail.com"

        # Creamos el contenedor del mensaje de correo electrónico
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = remitente
        msg["To"] = destinatario

        # Adjuntamos el cuerpo del correo interpretado como código HTML
        parte_html = MIMEText(html_body, "html")
        msg.attach(parte_html)

        # Establecemos la conexión segura con el servidor SMTP de Gmail (Puerto 587)
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Ciframos la conexión de forma segura
            server.login(remitente, password)  # Autenticación en el servidor
            server.sendmail(remitente, destinatario, msg.as_string())  # Envío físico del correo
            
        print("Correo enviado con éxito a través de SMTP.")
        return "success"
        
    except Exception as e:
        print(f"Error al enviar el correo: {e}")
        return f"failed: {str(e)}"


# Instrucciones del sistema en castellano para guiar la estética del correo HTML
INSTRUCTIONS = """Eres capaz de enviar un correo electrónico en formato HTML elegantemente diseñado basándote en un informe detallado.
Se te proporcionará un informe detallado. Debes usar tu herramienta para enviar un correo electrónico, convirtiendo el
informe en un HTML limpio y bien presentado, con un asunto adecuado."""

# Inicialización y configuración del agente de correo electrónico
email_agent = Agent(
    name="Agente de Correo",         # Nombre del agente en castellano
    instructions=INSTRUCTIONS,      # Asignación de instrucciones traducidas
    tools=[send_email],             # Vinculamos la función modificada como una herramienta ejecutable
    model="gemini/gemini-2.5-flash", # CAMBIADO: Ajustado a tu modelo Gemini
)
