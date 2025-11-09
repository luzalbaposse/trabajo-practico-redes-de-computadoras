from socket import *
import sys
import os
import mimetypes
from urllib.parse import parse_qs, urlparse
import qrcode


#FUNCIONES AUXILIARES

def imprimir_qr_en_terminal(url):
    """Dada una URL la imprime por terminal como un QR"""
    #podria necesitar ajuastar el boxsize o border para que se vea bien en terminal
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
    try:
        #Verifica si el archivo existe en el disco
        if not os.path.exists(archivo) or not os.path.isfile(archivo):
            # 404 Not Found
            response_line = b"HTTP/1.1 404 Not Found\r\n"
            headers = b"Content-Type: text/html\r\n\r\n"
            body = b"<html><body><h1>404 Not Found</h1><p>El archivo solicitado no se encuentra.</p></body></html>"
            return response_line + headers + body
        
        with open(archivo, 'rb') as f:
            contenido_archivo = f.read()
        
        # 200 OK
        response_line = b"HTTP/1.1 200 OK\r\n"
        
        # Obtener Content-Type
        content_type, _ = mimetypes.guess_type(archivo)
        headers = (
            "Content-Type: {content_type}\r\n"
            "Content-Length: {len(contenido_archivo)}\r\n"
            # Content-Disposition fuerza la descarga y sugiere el nombre
            "Content-Disposition: attachment; filename=\"{os.path.basename(archivo)}\"\r\n"
            "\r\n"
        )
        headers_bytes = headers.encode('utf-8')
        
        return response_line + headers_bytes + contenido_archivo

    except Exception as e:
        print(f"Error al manejar la descarga: {e}")
        # 500 Internal Server Error en caso de otros errores (permiso, lectura, etc.)
        response_line = b"HTTP/1.1 500 Internal Server Error\r\n"
        headers = b"Content-Type: text/html\r\n\r\n"
        body = b"<html><body><h1>500 Internal Server Error</h1><p>Ocurrio un error en el servidor al intentar descargar el archivo.</p></body></html>"
        return response_line + headers + body


def manejar_carga(body, boundary, directorio_destino="."):
    """
    Procesa un POST con multipart/form-data, guarda el archivo y devuelve una página de confirmación.
    """
    filename, file_content = parsear_multipart(body, boundary) 
    
    if filename and file_content:
        # Asegurarse de que el directorio de destino exista
        os.makedirs(directorio_destino, exist_ok=True)
        ruta_completa = os.path.join(directorio_destino, filename)
        
        try:
            # Guardar el contenido binario del archivo
            with open(ruta_completa, 'wb') as f:
                f.write(file_content)
            
            # 200 OK de éxito
            response_line = b"HTTP/1.1 200 OK\r\n"
            headers = b"Content-Type: text/html\r\n\r\n"
            body_html = f"""
<html>
  <head><title>Carga Exitosa</title></head>
  <body>
    <h1>Archivo Guardado Exitosamente!</h1>
    <p>El archivo <strong>{filename}</strong> ha sido guardado en el servidor.</p>
  </body>
</html>
""".encode('utf-8')
            return response_line + headers + body_html
            
        except Exception as e:
            print(f"Error al guardar el archivo: {e}")
            # 500 Internal Server Error
            response_line = b"HTTP/1.1 500 Internal Server Error\r\n"
            headers = b"Content-Type: text/html\r\n\r\n"
            body_html = b"<html><body><h1>500 Internal Server Error</h1><p>Error al guardar el archivo en el servidor.</p></body></html>"
            return response_line + headers + body_html
    else:
        # Error si no se pudo parsear el archivo
        response_line = b"HTTP/1.1 400 Bad Request\r\n"
        headers = b"Content-Type: text/html\r\n\r\n"
        body_html = b"<html><body><h1>400 Bad Request</h1><p>Error al recibir los datos del archivo.</p></body></html>"
        return response_line + headers + body_html


def start_server(archivo_descarga=None, modo_upload=False):
    """
    Inicia el servidor TCP.
    - Si se especifica archivo_descarga, se inicia en modo 'download'.
    - Si modo_upload=True, se inicia en modo 'upload'.
    """

    # Determinar el modo de operación
    if(archivo_descarga is None):
        modo = 'upload'
    else:
        modo = 'download'

    # 1. Obtener IP local y poner al servidor a escuchar en un puerto aleatorio ---
    try:
        #Crea el socket TCP
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.bind(('', 0)) 
        
        #Pone el servidor a escuchar conexiones
        server_socket.listen(1)
        
        #Obtiene la IP local (asumiendo que get_wifi_ip() funciona)
        ip_server = get_wifi_ip()
        
        #Obtiene el puerto asignado por el sistema operativo
        puerto = server_socket.getsockname()[1]
        
    except Exception as e:
        print(f"Error al iniciar el socket: {e}")
        sys.exit(1)

    #2. Mostrar información del servidor y el código QR
    url_base = f"http://{ip_server}:{puerto}"
    
    print(f"\nServidor iniciado en modo: **{modo.upper()}**")
    print("-" * 30)
    # Genera e imprime el QR de la URL (usando la función auxiliar)
    imprimir_qr_en_terminal(url_base)
    print("-" * 30)
    print("Esperando conexión...")


    # --- 3. Esperar conexiones y atender un cliente ---
    
    # 3.1 Aceptar la conexión (esto es bloqueante)
    connection_socket, addr = server_socket.accept()
    print(f"Conexión establecida desde: {addr[0]}:{addr[1]}")
    
    try:
        #3.2 Recibir los datos (solicitud HTTP)
        request = connection_socket.recv(65536) 
        
        #3.3 Decodificar la solicitud HTTP para procesarla
        #Divido el request en líneas y el cuerpo (body)

        request_decoded = request.decode('iso-8859-1')
        
        headers_end = request_decoded.find('\r\n\r\n')
        headers = request_decoded[:headers_end]
        body = request[headers_end + 4:] # Body en bytes
        
        #Obtener la primera línea
        request_line = headers.split('\n')[0].strip()
        
        if not request_line:
            raise ValueError("Solicitud vacía o mal formada.")
            
        # Determinar el método y la ruta
        metodo, ruta, _ = request_line.split()

        #Manejo de Solicitudes

        respuesta = b""
        
        if metodo == 'GET':
            if ruta == '/':
                # Petición de la página principal (interfaz)
                html_contenido = generar_html_interfaz(modo)
                
                # Respuesta 200 OK con HTML
                response_line = b"HTTP/1.1 200 OK\r\n"
                headers_response = (
                    "Content-Type: text/html; charset=utf-8\r\n"
                    "Content-Length: {len(html_contenido)}\r\n"
                    "\r\n"
                )
                headers_response_bytes = headers_response.encode('utf-8')
                respuesta = response_line + headers_response_bytes + html_contenido.encode('utf-8')
                
            elif modo == 'download' and ruta == '/download':
                # Petición del archivo a descargar
                # Manejar_descarga genera 200 OK o 404 Not Found
                respuesta = manejar_descarga(archivo_descarga, request_line)
            
            else:
                # Cualquier otra ruta GET (404)
                response_line = b"HTTP/1.1 404 Not Found\r\n"
                headers_response = b"Content-Type: text/html\r\n\r\n"
                body_404 = b"<html><body><h1>404 Not Found</h1></body></html>"
                respuesta = response_line + headers_response + body_404
        
        elif metodo == 'POST' and modo == 'upload':
            # Petición de carga de archivo (upload)
            
            # Buscar el boundary en los headers (ej: Content-Type: multipart/form-data; boundary=----WebKitFormBoundary...)
            boundary = None
            for header_line in headers.split('\n'):
                if header_line.lower().startswith('content-type:') and 'multipart/form-data' in header_line.lower():
                    # Extraer el valor del boundary
                    try:
                        # Buscar 'boundary=' y extraer el valor (quitando espacios y comillas si las hay)
                        boundary = header_line.split('boundary=')[1].strip().strip('"')
                        if boundary:
                            boundary = boundary.encode('iso-8859-1') # Codificar el boundary
                        break
                    except IndexError:
                        pass # No se encontró el boundary correctamente

            if boundary:
                # Manejar_carga genera 200 OK (guardado) o 500 Internal Error (al guardar)
                respuesta = manejar_carga(body, boundary)
            else:
                # 400 Bad Request si es un POST mal formado (sin boundary)
                response_line = b"HTTP/1.1 400 Bad Request\r\n"
                headers_response = b"Content-Type: text/html\r\n\r\n"
                body_400 = b"<html><body><h1>400 Bad Request</h1><p>POST mal formado.</p></body></html>"
                respuesta = response_line + headers_response + body_400

        else:
            # Método o modo no soportado
            response_line = b"HTTP/1.1 405 Method Not Allowed\r\n\r\n"
            respuesta = response_line
        
        # 3.4 Enviar la respuesta al cliente
        if respuesta:
            connection_socket.sendall(respuesta)
            print(f"Respuesta enviada para {metodo} {ruta}")
            
    except Exception as e:
        print(f"Error al procesar la conexión: {e}")
        
    finally:
        # 3.5 Cerrar la conexión
        connection_socket.close()
        server_socket.close()
        print("Conexión y servidor cerrados.")

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
