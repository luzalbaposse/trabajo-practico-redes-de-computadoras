from socket import *
import sys
import os
from urllib.parse import parse_qs, urlparse
import qrcode
import socket

#FUNCIONES AUXILIARES

def imprimir_qr_en_terminal(url):
    """
    Requiere: url: str, la URL a imprimir como QR
    Ejecuta: imprime el QR de la URL en el terminal
    Devuelve: None
    """

    qr = qrcode.QRCode(border=1)
    qr.add_data(url)
    qr.make(fit=True)
    mat = qr.get_matrix()
    black = "██"
    white = "  "
    print()
    for row in mat:
        line = "".join(black if cell else white for cell in row)
        print(line)
    print()
    print(url)


def get_wifi_ip():
    """Obtiene la IP local asociada a la interfaz de red (por ejemplo, Wi-Fi)."""
    s = socket(AF_INET, SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip #Devuelve la IP como string

def parsear_headers_y_body(data):
    """
    Separa los headers del body en un request HTTP.
    Requiere: data: bytes, los datos completos del request HTTP
    Devuelve: tuple (headers: dict, body: bytes), diccionario de headers y body en bytes
    """
    # Decodificar para buscar el separador de headers/body
    request_text = data.decode("utf-8", errors="ignore")
    
    # Buscar el separador entre headers y body (\r\n\r\n o \n\n)
    header_end = request_text.find("\r\n\r\n")
    if header_end == -1:
        header_end = request_text.find("\n\n")
        header_text = request_text[:header_end]
        body = data[header_end + 2:]
    else:
        header_text = request_text[:header_end]
        body = data[header_end + 4:]  # +4 para saltar \r\n\r\n
    
    # Parsear los headers en un diccionario
    headers = {}
    for line in header_text.split("\r\n")[1:]:  # [1:] para saltar la request line
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip().lower()] = value.strip()
    
    return headers, body

def extraer_boundary(headers):
    """
    Extrae el boundary del header Content-Type.
    Requiere: headers: dict, diccionario con los headers HTTP (claves en minúsculas)
    Devuelve: str o None, el boundary si existe, None si no se encuentra
    """
    if "content-type" not in headers:
        return None
    
    content_type = headers["content-type"]
    if "boundary=" not in content_type:
        return None
    
    # El formato es: multipart/form-data; boundary=VALOR
    boundary = content_type.split("boundary=")[1].strip()
    # Limpiar comillas o espacios extra
    boundary = boundary.strip('"').strip()
    return boundary

def parsear_multipart(body, boundary):
    """Función auxiliar (ya implementada) para parsear multipart/form-data."""
    try:
        # Se divide el cuerpo por el boundary para luego poder extraer el nombre y contenido del archivo
        parts = body.split(f'--{boundary}'.encode())
        for part in parts:
            if b'filename=' in part:
                # Se extrae el nombre del archivo
                filename_start = part.find(b'filename="') + len(b'filename="')
                filename_end = part.find(b'"', filename_start)
                filename = part[filename_start:filename_end].decode()

                # Se extrae el contenido del archivo que arranca después de los headers
                header_end = part.find(b'\r\n\r\n')
                if header_end == -1:
                    header_end = part.find(b'\n\n')
                    content_start = header_end + 2
                else:
                    content_start = header_end + 4

                # El contenido va hasta el último CRLF antes del boundary
                content_end = part.rfind(b'\r\n')
                if content_end <= content_start:
                    content_end = part.rfind(b'\n')

                file_content = part[content_start:content_end]
                if filename and file_content:
                    return filename, file_content
        return None, None
    except Exception as e:
        print(f"Error al parsear multipart: {e}")
        return None, None

def generar_html_interfaz(modo):
    """
    Genera el HTML de la interfaz principal:
    - Si modo == 'download': incluye un enlace o botón para descargar el archivo.
    - Si modo == 'upload': incluye un formulario para subir un archivo.
    """
    if modo == 'download':
        return """
<html>
  <head>
    <meta charset="utf-8">
    <title>Descargar archivo</title>
    <style>
      body { font-family: sans-serif; max-width: 500px; margin: 50px auto; }
      a { display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
    </style>
  </head>
  <body>
    <h1>Descargar archivo</h1>
    <p>Haz click en el botón para descargar:</p>
    <a href="/download">Descargar archivo</a>
  </body>
</html>
"""
    
    else:  # upload
        return """
<html>
  <head>
    <meta charset="utf-8">
    <title>Subir archivo</title>
    <style>
      body { font-family: sans-serif; max-width: 500px; margin: 50px auto; }
      form { border: 2px dashed #ccc; padding: 20px; border-radius: 5px; }
      input[type="submit"] { padding: 10px 20px; background: #28a745; color: white; border: none; border-radius: 5px; cursor: pointer; }
    </style>
  </head>
  <body>
    <h1>Subir archivo</h1>
    <form method="POST" enctype="multipart/form-data">
      <input type="file" name="file" required>
      <input type="submit" value="Subir">
    </form>
  </body>
</html>
"""



#CODIGO A COMPLETAR

def manejar_descarga(archivo, request_line):
    """
    Genera una respuesta HTTP con el archivo solicitado. 
    Si el archivo no existe debe devolver un error.
    Debe incluir los headers: Content-Type, Content-Length y Content-Disposition.
    """
    # COMPLETAR
    return b""


def manejar_carga(body, boundary, directorio_destino="."):
    """
    Procesa un POST con multipart/form-data, guarda el archivo y devuelve una página de confirmación.
    """
    # COMPLETAR
    return b""


def start_server(archivo_descarga=None, modo_upload=False):
    """
    Inicia el servidor TCP.
    - Si se especifica archivo_descarga, se inicia en modo 'download'.
    - Si modo_upload=True, se inicia en modo 'upload'.
    """

    # 1. Obtener IP local y poner al servidor a escuchar en un puerto aleatorio
    #COMPLETAR

    ip_server = get_wifi_ip()
    puerto = 0  

    method = None

    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind((ip_server, puerto))
    server_socket.listen(1)

    # 2. Mostrar información del servidor y el código QR
    # COMPLETAR: imprimir URL y modo de operación (download/upload)
    url = f"http://{ip_server}:{puerto}"
    print(f"El server está listo! La URL es: {url}")
    imprimir_qr_en_terminal(url)

    if modo_upload:
        print("El server está en modo upload")
    else:
        print("El server está en modo download")

    # 3. Esperar conexiones y atender un cliente (accept, recv, decode, determine, generate, send, close)
    # COMPLETAR:
    # - aceptar la conexión (accept)
    # - recibir los datos (recv)
    # - decodificar la solicitud HTTP
    # - determinar método (GET/POST) y ruta (/ o /download)
    # - generar la respuesta correspondiente (HTML o archivo)
    # - enviar la respuesta al cliente
    # - cerrar la conexión

    while True: 
        # Aceptar la conexión
        client_socket, client_address = server_socket.accept()
        print(f"Se estableció una conexión con {client_address} ✨")

        # Recibir los datos
        data = client_socket.recv(65535)
        # Decodificar los datos
        request_line = data.decode("utf-8")

        if request_line.startswith("GET"):
            method = "GET"
            path = request_line.split(" ")[1]
            if path == "/":
                response = generar_html_interfaz(method)
            elif path == "/download":
                response = manejar_descarga(archivo_descarga, request_line)
            elif path == "/upload":
                response = manejar_carga(data, boundary)
        
        elif request_line.startswith("POST"):
            method = "POST"
            path = request_line.split(" ")[1]
            if path == "/" or path == "":
                # El cliente quiere enviar un archivo
                # Separar headers del body usando función auxiliar
                headers, body = parsear_headers_y_body(data)
                
                # Extraer el boundary del Content-Type
                boundary = extraer_boundary(headers)
                
                if boundary:
                    # Parsear multipart y procesar el archivo
                    response = manejar_carga(body, boundary, directorio_destino=".")
                else:
                    response = b"HTTP/1.1 400 Bad Request\r\n\r\n"
            else:
                modo_actual = 'upload' if modo_upload else 'download'
                response = generar_html_interfaz(modo_actual)
        else:
            response = b"HTTP/1.1 400 Bad Request\r\n\r\n"

        # Enviar la respuesta al cliente
        client_socket.sendall(response)
        # Cerrar la conexión
        client_socket.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python tp.py upload                    # Servidor para subir archivos")
        print("  python tp.py download archivo.txt      # Servidor para descargar un archivo")
        sys.exit(1)

    comando = sys.argv[1].lower()

    if comando == "upload":
        start_server(archivo_descarga=None, modo_upload=True)

    elif comando == "download" and len(sys.argv) > 2:
        archivo = sys.argv[2]
        ruta_archivo = os.path.join("archivos_servidor", archivo)
        start_server(archivo_descarga=ruta_archivo, modo_upload=False)

    else:
        print("Comando no reconocido o archivo faltante")
        sys.exit(1)
