import asyncio
import os
import sys
from google import genai
from google.genai import types
from mcp import ClientSession
from mcp.client.stdio import (stdio_client, StdioServerParameters)

# Evita que model_copy falle al intentar clonar las tareas asíncronas de la sesión MCP
ClientSession.__deepcopy__ = lambda self, memo: self

# Carpeta del proyecto y carpeta donde el agente crea y lee sus archivos
CARPETA_PROYECTO = os.path.dirname(os.path.abspath(__file__))
CARPETA_PRUEBAS = os.path.join(CARPETA_PROYECTO, "archivos_prueba")
os.makedirs(CARPETA_PRUEBAS, exist_ok=True)


# FUNCIÓN PRINCIPAL
async def generate():

    client = genai.Client(api_key="Aqui su llave",  # Reemplaza con tu API Key de Google Gemini
        # Reintenta automáticamente si Gemini está saturado (503) o se supera el límite (429)
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(attempts=6, initial_delay=2, http_status_codes=[429, 500, 503])
        ),
    )

    # Un StdioServerParameters por cada servidor MCP
    params_archivos = StdioServerParameters(
        command=sys.executable,
        args=[os.path.join(CARPETA_PROYECTO, "mi_servidor_mcp.py")],
        cwd=CARPETA_PRUEBAS,  # ambos servidores trabajan dentro de archivos_prueba
    )
    params_excel = StdioServerParameters(
        command=sys.executable,
        args=[os.path.join(CARPETA_PROYECTO, "servidor_excel_mcp.py")],
        cwd=CARPETA_PRUEBAS,
    )

    # CONEXIÓN MCP: se abre una conexión y una sesión por servidor
    async with stdio_client(params_archivos) as (read_a, write_a), \
               stdio_client(params_excel) as (read_e, write_e):

        async with ClientSession(read_a, write_a) as session_archivos, \
                   ClientSession(read_e, write_e) as session_excel:

            await session_archivos.initialize()  # Inicializar servidor de archivos
            await session_excel.initialize()     # Inicializar servidor de Excel

            # instrucciones del sistema
            instruciones_sistema = (
                "Eres un asistente técnico experto con acceso a dos grupos de herramientas MCP:\n"
                "1) Herramientas de ARCHIVOS y DIRECTORIOS (listar_archivos, leer_archivo, "
                "crear_archivo_txt, agregar_contenido, directorio_actual, obtener_ruta, "
                "cambiar_directorio) para trabajar con archivos de texto .txt y carpetas.\n"
                "2) Herramientas de EXCEL (crear_excel, leer_excel, escribir_celda, "
                "agregar_filas, listar_hojas, crear_hoja, listar_excels) para trabajar "
                "con archivos .xlsx.\n"
                "Usa estas herramientas siempre que el usuario quiera trabajar con archivos, "
                "directorios u hojas de cálculo. Puedes combinarlas en una misma tarea: por "
                "ejemplo, leer archivos de texto con las herramientas de archivos y luego "
                "guardar esa información en una tabla de Excel con encabezados en la primera fila. "
                "Recuerda los nombres de los archivos creados durante la conversación."
            )

            # configuración del chat, se le indica que use las herramientas de ambos servidores
            configuracion = types.GenerateContentConfig(
                system_instruction=instruciones_sistema,
                tools=[session_archivos, session_excel],
                thinking_config=types.ThinkingConfig(
                    thinking_level="low",
                    include_thoughts=False
                ),
                temperature=0.8,
                # Permite más llamadas a herramientas por mensaje (por defecto son 10)
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    maximum_remote_calls=30
                ),
            )
            # modelo a usar
            modelo = "gemini-3.1-flash-lite"
            chat = client.aio.chats.create(model=modelo, config=configuracion)

            print("===================================")
            print("  CHAT MCP + GEMINI (2 SERVIDORES)")
            print("     Archivos  +  Excel")
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
