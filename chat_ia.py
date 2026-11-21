import asyncio
import sys
from google import genai
from google.genai import types
from mcp import ClientSession
from mcp.client.stdio import (stdio_client, StdioServerParameters)

# Evita que model_copy falle al intentar clonar las tareas asíncronas de la sesión MCP
ClientSession.__deepcopy__ = lambda self, memo: self


# FUNCIÓN PRINCIPAL
async def generate():

    client = genai.Client(api_key="Aqui su llave",  # Reemplaza con tu API Key de Google Gemini
        # Reintenta automáticamente si Gemini está saturado (503) o se supera el límite (429)
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(attempts=6, initial_delay=2, http_status_codes=[429, 500, 503])
        ),
    )

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["mi_servidor_mcp.py"],
    )

    # CONEXIÓN MCP
    async with stdio_client(server_params) as (read, write):

        async with ClientSession(read, write) as session:
            await session.initialize()  # Inicializar MCP

            # instrucciones del sistema
            instruciones_sistema = (
                "Eres un asistente técnico experto. Usa las herramientas MCP siempre que "
                "el usuario quiera trabajar con archivos o directorios."
            )

            # configuración del chat, se le indica que use las herramientas MCP
            configuracion = types.GenerateContentConfig(
                system_instruction=instruciones_sistema,
                tools=[session],
                thinking_config=types.ThinkingConfig(
                    thinking_level="low",
                    include_thoughts=False
                ),
                temperature=0.8,
            )
            # modelo a usar
            modelo = "gemini-3.1-flash-lite"
            chat = client.aio.chats.create(model=modelo, config=configuracion)

            print("===================================")
            print("      CHAT MCP + GEMINI")
            print("===================================")
            print("Escribe 'salir' para terminar")

            while True:

                pregunta = input(" Tú: ")
                if pregunta.lower() in ["salir", "exit"]:
                    break
                print("\n Pensando...\n")

                try:
                    response = await chat.send_message(
                        pregunta
                    )
                    print(response.text)

                except Exception as e:

                    print("\n Error:")
                    print(str(e))


if __name__ == "__main__":
    asyncio.run(generate())
