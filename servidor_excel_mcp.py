from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from openpyxl import Workbook, load_workbook
from openpyxl.utils.cell import coordinate_from_string
import os

mcp = MCPServer("ExcelServer")


# Los errores se lanzan como ToolError para que el mensaje claro llegue al modelo
# (otras excepciones se ocultan y el modelo solo ve 'Error executing tool').

# ---------------------------------------------------------------
# Funciones auxiliares (no son herramientas MCP)
# ---------------------------------------------------------------

def _normalizar_nombre(ruta: str) -> str:
    """Agrega la extensión .xlsx si no la tiene."""
    if not ruta.lower().endswith(".xlsx"):
        ruta += ".xlsx"
    return ruta


def _abrir_libro(ruta: str):
    """Abre un libro de Excel existente o lanza un error claro."""
    ruta = _normalizar_nombre(ruta)
    if not os.path.exists(ruta):
        raise ToolError(
            f"El archivo '{ruta}' no existe en {os.getcwd()}. "
            "Usa crear_excel para crearlo primero."
        )
    try:
        return load_workbook(ruta), ruta
    except Exception as e:
        raise ToolError(f"No se pudo abrir '{ruta}' como archivo de Excel: {e}")


def _obtener_hoja(libro, hoja: str):
    """Devuelve la hoja indicada, o la hoja activa si 'hoja' está vacío."""
    if not hoja:
        return libro.active
    if hoja not in libro.sheetnames:
        raise ToolError(
            f"La hoja '{hoja}' no existe. Hojas disponibles: {', '.join(libro.sheetnames)}"
        )
    return libro[hoja]


def _validar_celda(celda: str) -> str:
    """Comprueba que la celda tenga formato válido, por ejemplo A1 o C15."""
    celda = celda.strip().upper()
    try:
        coordinate_from_string(celda)
    except Exception:
        raise ToolError(
            f"La celda '{celda}' no es válida. Usa el formato columna+fila, por ejemplo A1 o C15."
        )
    return celda


def _convertir_valor(valor: str):
    """Convierte texto numérico a número para que Excel lo trate como tal."""
    texto = valor.strip()
    try:
        return int(texto)
    except ValueError:
        pass
    try:
        return float(texto)
    except ValueError:
        return valor


# ---------------------------------------------------------------
# Herramientas MCP
# ---------------------------------------------------------------

@mcp.tool()
def crear_excel(nombre: str, encabezados: list[str] = [], hoja: str = "Hoja1") -> str:
    """Crea un nuevo archivo de Excel (.xlsx).
    Opcionalmente escribe una fila de encabezados en la primera fila
    y permite nombrar la hoja inicial. Si el archivo ya existe, lo reemplaza."""

    nombre = _normalizar_nombre(nombre)
    libro = Workbook()
    hoja_activa = libro.active
    hoja_activa.title = hoja or "Hoja1"
    if encabezados:
        hoja_activa.append(encabezados)
    libro.save(nombre)
    return f"Archivo de Excel creado correctamente en: {os.path.abspath(nombre)}"


@mcp.tool()
def leer_excel(ruta: str, hoja: str = "") -> list[list[str]]:
    """Lee todo el contenido de una hoja de un archivo de Excel.
    Devuelve una lista de filas, donde cada fila es una lista de valores como texto.
    Si no se indica la hoja, se lee la hoja activa."""

    libro, _ = _abrir_libro(ruta)
    hoja_obj = _obtener_hoja(libro, hoja)
    filas = []
    for fila in hoja_obj.iter_rows(values_only=True):
        filas.append(["" if v is None else str(v) for v in fila])
    return filas


@mcp.tool()
def escribir_celda(ruta: str, celda: str, valor: str, hoja: str = "") -> str:
    """Escribe un valor en una celda específica (por ejemplo 'B3') de un archivo de Excel existente.
    Si no se indica la hoja, se usa la hoja activa."""

    libro, ruta = _abrir_libro(ruta)
    hoja_obj = _obtener_hoja(libro, hoja)
    celda = _validar_celda(celda)
    hoja_obj[celda] = _convertir_valor(valor)
    libro.save(ruta)
    return f"Valor '{valor}' escrito en la celda {celda} de la hoja '{hoja_obj.title}'."


@mcp.tool()
def agregar_filas(ruta: str, filas: list[list[str]], hoja: str = "") -> str:
    """Agrega una o varias filas al final de una hoja de un archivo de Excel existente.
    Cada fila es una lista de valores, por ejemplo [["Ana", "25", "Bogotá"], ["Luis", "30", "Cali"]].
    Si no se indica la hoja, se usa la hoja activa."""

    libro, ruta = _abrir_libro(ruta)
    hoja_obj = _obtener_hoja(libro, hoja)
    for fila in filas:
        hoja_obj.append([_convertir_valor(v) for v in fila])
    libro.save(ruta)
    return f"Se agregaron {len(filas)} fila(s) a la hoja '{hoja_obj.title}'."


@mcp.tool()
def listar_hojas(ruta: str) -> list[str]:
    """Lista los nombres de todas las hojas de un archivo de Excel."""

    libro, _ = _abrir_libro(ruta)
    return libro.sheetnames


@mcp.tool()
def crear_hoja(ruta: str, nombre_hoja: str) -> str:
    """Crea una nueva hoja dentro de un archivo de Excel existente."""

    libro, ruta = _abrir_libro(ruta)
    if nombre_hoja in libro.sheetnames:
        raise ToolError(f"La hoja '{nombre_hoja}' ya existe en '{ruta}'.")
    libro.create_sheet(nombre_hoja)
    libro.save(ruta)
    return f"Hoja '{nombre_hoja}' creada en '{ruta}'."


@mcp.tool()
def listar_excels(ruta: str = ".") -> list[str]:
    """Lista los archivos de Excel (.xlsx) que hay en una carpeta."""

    if not os.path.isdir(ruta):
        raise ToolError(f"La carpeta '{ruta}' no existe.")
    return [f for f in os.listdir(ruta) if f.lower().endswith(".xlsx")]


if __name__ == "__main__":
    mcp.run()
