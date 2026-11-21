# Agente MCP con Gemini (Google AI Studio)

Agente conversacional que usa **Gemini** y el protocolo **MCP** (Model Context Protocol) para ejecutar
acciones reales mediante *Tool Calling*: gestionar archivos de texto y directorios, y trabajar con
archivos de Excel. Gracias al sistema de chat de la SDK, el agente mantiene memoria durante la conversación.

## Estructura

| Archivo | Descripción |
|---|---|
| `mi_servidor_mcp.py` | Servidor MCP de archivos: listar, leer, crear `.txt`, agregar contenido, directorio actual, ruta absoluta y cambiar directorio. |
| `servidor_excel_mcp.py` | Servidor MCP de Excel (openpyxl): crear libro, leer hoja, escribir celda, agregar filas, listar hojas, crear hoja y listar `.xlsx`. Los errores (archivo u hoja inexistente, celda inválida) se devuelven con mensajes claros. |
| `chat_ia.py` | Chat con Gemini conectado al servidor de archivos (Partes 1–4). |
| `chat_dos_servidores.py` | Chat con Gemini conectado a los dos servidores a la vez (Parte 5, reto). |
| `archivos_prueba/` | Carpeta de trabajo del agente: aquí se crean y leen los `.txt` y `.xlsx`. Contiene los archivos generados durante las pruebas. |

## Instalación

```powershell
python -m venv env_mcp
.\env_mcp\Scripts\activate
pip install --upgrade google-genai mcp openpyxl
```

## Configuración

Obtén una API key en [Google AI Studio](https://aistudio.google.com/apikey) y reemplaza
`"Aqui su llave"` en `chat_ia.py` y `chat_dos_servidores.py`. **No subas tu llave al repositorio.**

## Uso

Ejecuta los scripts (funcionan desde cualquier carpeta; los servidores MCP se inician con
`archivos_prueba/` como directorio de trabajo):

```powershell
python chat_ia.py              # Partes 1–4: servidor de archivos
python chat_dos_servidores.py  # Parte 5: archivos + Excel
```

### Pruebas (Parte 4)
1. "Crea un archivo y escribe algo en él."
2. "Agrégale otra línea a ese archivo."
3. "Muéstrame qué archivos hay en la carpeta y lee el que acabamos de crear."
4. "¿En qué carpeta estás y cuál es la ruta de ese archivo?"

### Prueba final del reto (Parte 5)
1. "Crea al menos 3 archivos de texto, cada uno con información de una persona o un tema distinto…"
2. "Ahora lee los archivos de texto que acabas de crear y organiza su contenido en una tabla dentro de un nuevo archivo de Excel."

## Notas técnicas
- Con `mcp` 2.x, las herramientas lanzan `ToolError` para que el mensaje de error llegue al modelo
  (otras excepciones se ocultan como "Error executing tool").
- El cliente de Gemini reintenta automáticamente ante errores 429/500/503 (modelo saturado).
- `chat_dos_servidores.py` permite hasta 30 llamadas a herramientas por mensaje, porque el reto encadena varias.
