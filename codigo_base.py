from socket import *
import sys
import os
from urllib.parse import parse_qs, urlparse, unquote
import qrcode
import mimetypes
import gzip
import time

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

def generar_html_interfaz(modo, directorio_archivos="archivos_servidor"):
    """
    Genera el HTML de la interfaz principal:
    - Si modo == 'download': incluye un enlace o botón para descargar el archivo.
    - Si modo == 'upload': incluye un formulario para subir un archivo.
    - Si modo == 'both': incluye ambas funcionalidades.
    """
    # Obtener lista de archivos disponibles si el directorio existe
    archivos_disponibles = []
    if os.path.exists(directorio_archivos):
        try:
            archivos_disponibles = [f for f in os.listdir(directorio_archivos) 
                                   if os.path.isfile(os.path.join(directorio_archivos, f))]
        except:
            archivos_disponibles = []
    
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
    
    elif modo == 'upload':
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
    
    else:  # modo == 'both' o cualquier otro
        lista_archivos_html = ""
        if archivos_disponibles:
            lista_archivos_html = "<h2>Archivos disponibles para descargar:</h2><ul>"
            for archivo in archivos_disponibles:
                lista_archivos_html += f'<li><a href="/download?archivo={archivo}">{archivo}</a></li>'
            lista_archivos_html += "</ul>"
        else:
            lista_archivos_html = "<p>No hay archivos disponibles para descargar.</p>"
        
        return f"""
<html>
  <head>
    <meta charset="utf-8">
    <title>Transferencia de archivos</title>
    <style>
      body {{ font-family: sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
      h1 {{ color: #333; }}
      h2 {{ color: #555; margin-top: 30px; }}
      form {{ border: 2px dashed #ccc; padding: 20px; border-radius: 5px; margin: 20px 0; }}
      input[type="file"] {{ margin: 10px 0; }}
      input[type="submit"] {{ padding: 10px 20px; background: #28a745; color: white; border: none; border-radius: 5px; cursor: pointer; }}
      ul {{ list-style-type: none; padding: 0; }}
      li {{ margin: 10px 0; }}
      a {{ display: inline-block; padding: 8px 16px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
      a:hover {{ background: #0056b3; }}
    </style>
  </head>
  <body>
    <h1>Transferencia de archivos</h1>
    
    <h2>Subir archivo</h2>
    <form method="POST" enctype="multipart/form-data">
      <input type="file" name="file" required>
      <br>
      <input type="submit" value="Subir archivo">
    </form>
    
    {lista_archivos_html}
  </body>
</html>
"""


#CODIGO A COMPLETAR

def manejar_descarga(archivo, request_line, headers=None, comprimir_gzip=False):
    """
    Genera una respuesta HTTP con el archivo solicitado. 
    Si el archivo no existe debe devolver un error.
    Debe incluir los headers: Content-Type, Content-Length y Content-Disposition.
    Si comprimir_gzip=True y el cliente acepta gzip, comprime el contenido.
    """
    # Verificar si el archivo existe
    if archivo is None or not os.path.exists(archivo):
        # Archivo no encontrado - devolver 404
        response = b"HTTP/1.1 404 Not Found\r\n"
        response += b"Content-Type: text/html\r\n"
        response += b"Content-Length: 0\r\n"
        response += b"\r\n"
        return response
    
    try:
        # Leer el archivo en modo binario
        with open(archivo, 'rb') as f:
            file_content = f.read()
        
        # Obtener el nombre del archivo para Content-Disposition
        filename = os.path.basename(archivo)
        
        # Determinar el Content-Type usando mimetypes
        content_type, _ = mimetypes.guess_type(archivo)
        if content_type is None:
            content_type = 'application/octet-stream'  # Tipo por defecto para archivos desconocidos
        
        # Verificar si el cliente acepta compresión gzip
        acepta_gzip = False
        if comprimir_gzip and headers:
            accept_encoding = headers.get('accept-encoding', '')
            if 'gzip' in accept_encoding.lower():
                acepta_gzip = True
        
        # Comprimir el contenido si está habilitado y el cliente lo acepta
        usar_gzip = comprimir_gzip and acepta_gzip
        if usar_gzip:
            file_content = gzip.compress(file_content)
        
        # Obtener el tamaño del archivo (Content-Length) después de comprimir
        content_length = len(file_content)
        
        # Construir la respuesta HTTP
        response = b"HTTP/1.1 200 OK\r\n"
        response += f"Content-Type: {content_type}\r\n".encode('utf-8')
        if usar_gzip:
            response += b"Content-Encoding: gzip\r\n"
        response += f"Content-Length: {content_length}\r\n".encode('utf-8')
        response += f'Content-Disposition: attachment; filename="{filename}"\r\n'.encode('utf-8')
        response += b"\r\n"  # Línea vacía que separa headers del body
        response += file_content  # Contenido del archivo (comprimido o no)
        
        return response
    
    except Exception as e:
        # Error al leer el archivo - devolver 500
        print(f"Error al leer el archivo: {e}")
        response = b"HTTP/1.1 500 Internal Server Error\r\n"
        response += b"Content-Type: text/html\r\n"
        response += b"Content-Length: 0\r\n"
        response += b"\r\n"
        return response


def manejar_carga(body, boundary, directorio_destino="."):
    """
    Procesa un POST con multipart/form-data, guarda el archivo y devuelve una página de confirmación.
    """
    try:
        # Parsear el multipart para extraer el nombre del archivo y su contenido
        filename, file_content = parsear_multipart(body, boundary)
        
        # Verificar que se pudo extraer el archivo correctamente
        if filename is None or file_content is None:
            # No se pudo parsear el archivo - devolver 400 Bad Request
            error_html = """
            <html>
              <head><title>Error</title></head>
              <body><h1>400 Bad Request</h1><p>No se pudo procesar el archivo.</p></body>
            </html>
            """
            error_html_bytes = error_html.encode('utf-8')
            response = b"HTTP/1.1 400 Bad Request\r\n"
            response += b"Content-Type: text/html\r\n"
            response += f"Content-Length: {len(error_html_bytes)}\r\n".encode('utf-8')
            response += b"\r\n"
            response += error_html_bytes
            return response
        
        # Asegurar que el directorio destino existe
        if not os.path.exists(directorio_destino):
            os.makedirs(directorio_destino, exist_ok=True)
        
        # Construir la ruta completa del archivo
        ruta_archivo = os.path.join(directorio_destino, filename)
        
        # Guardar el archivo en el directorio destino
        with open(ruta_archivo, 'wb') as f:
            f.write(file_content)
        
        # Generar página de confirmación HTML
        confirmacion_html = f"""
        <html>
          <head>
            <meta charset="utf-8">
            <title>Archivo subido</title>
            <style>
              body {{ font-family: sans-serif; max-width: 500px; margin: 50px auto; }}
              .success {{ color: #28a745; font-size: 24px; }}
            </style>
          </head>
          <body>
            <h1 class="success">✓ Archivo subido exitosamente</h1>
            <p><strong>Nombre del archivo:</strong> {filename}</p>
            <p><strong>Tamaño:</strong> {len(file_content)} bytes</p>
            <p><strong>Guardado en:</strong> {ruta_archivo}</p>
          </body>
        </html>
        """
        confirmacion_html_bytes = confirmacion_html.encode('utf-8')
        
        # Construir la respuesta HTTP 200 OK
        response = b"HTTP/1.1 200 OK\r\n"
        response += b"Content-Type: text/html\r\n"
        response += f"Content-Length: {len(confirmacion_html_bytes)}\r\n".encode('utf-8')
        response += b"\r\n"
        response += confirmacion_html_bytes
        
        return response
    
    except Exception as e:
        # Error al procesar o guardar el archivo - devolver 500 Internal Server Error
        print(f"Error al procesar la carga del archivo: {e}")
        error_html = f"""
        <html>
          <head><title>Error</title></head>
          <body>
            <h1>500 Internal Server Error</h1>
            <p>Error al guardar el archivo: {str(e)}</p>
          </body>
        </html>
        """
        error_html_bytes = error_html.encode('utf-8')
        response = b"HTTP/1.1 500 Internal Server Error\r\n"
        response += b"Content-Type: text/html\r\n"
        response += f"Content-Length: {len(error_html_bytes)}\r\n".encode('utf-8')
        response += b"\r\n"
        response += error_html_bytes
        return response


def start_server(archivo_descarga=None, modo_upload=False, comprimir_gzip=False, password=None, medir_tiempo=False):
    """
    Inicia el servidor TCP.
    - Si se especifica archivo_descarga, se inicia en modo 'download'.
    - Si modo_upload=True, se inicia en modo 'upload'.
    - Si comprimir_gzip=True, comprime las respuestas con gzip si el cliente lo acepta.
    - Si password no es None, requiere autenticación Bearer token.
    - Si medir_tiempo=True, imprime mediciones de tiempo para análisis.
    """

    # 1. Obtener IP local y poner al servidor a escuchar en un puerto aleatorio
    #COMPLETAR

    ip_server = get_wifi_ip()
    # Permitir especificar puerto mediante variable de entorno (opcional)
    puerto = int(os.environ.get("PUERTO", 0))

    method = None

    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind((ip_server, puerto))
    # Obtener el puerto real asignado por el sistema
    puerto = server_socket.getsockname()[1]
    server_socket.listen(1)

    # 2. Mostrar información del servidor y el código QR
    # COMPLETAR: imprimir URL y modo de operación (download/upload)
    url = f"http://{ip_server}:{puerto}"
    print(f"El server está listo! La URL es: {url}")
    imprimir_qr_en_terminal(url)

    if modo_upload:
        print("El server está en modo upload (también permite descargar archivos)")
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

    try:
        while True: 
            client_socket = None
            try:
                # Aceptar la conexión
                client_socket, client_address = server_socket.accept()
                print(f"Se estableció una conexión con {client_address} ✨")

                # Recibir los datos
                data = client_socket.recv(65535)
                
                # Si no se recibieron datos, cerrar la conexión y continuar
                if not data:
                    client_socket.close()
                    continue
                
                # Extraer solo la request line (primera línea) sin decodificar todo el body
                # porque el body puede contener datos binarios
                first_line_end = data.find(b'\r\n')
                if first_line_end == -1:
                    first_line_end = data.find(b'\n')
                if first_line_end == -1:
                    first_line_end = len(data)
                
                # Decodificar solo la request line
                request_line = data[:first_line_end].decode("utf-8", errors="ignore")
                
                # Extraer el método y el path de la request line
                parts = request_line.split(" ", 2)
                if len(parts) < 2:
                    response = b"HTTP/1.1 400 Bad Request\r\n\r\n"
                    client_socket.sendall(response)
                    client_socket.close()
                    continue
                
                method = parts[0]
                path_full = parts[1]
                
                # Parsear path y query string
                path_parts = path_full.split('?', 1)
                path = path_parts[0]
                query_string = path_parts[1] if len(path_parts) > 1 else ""
                
                # Parsear query string para obtener parámetros
                query_params = {}
                if query_string:
                    for param in query_string.split('&'):
                        if '=' in param:
                            key, value = param.split('=', 1)
                            # Decodificar el valor (puede venir URL-encoded)
                            value = unquote(value)
                            query_params[key] = value

                # Parsear headers para todas las solicitudes
                headers = {}
                body_inicial = b""
                try:
                    headers, _ = parsear_headers_y_body(data)
                except:
                    headers, body_inicial = {}, b""
                
                # Verificar autenticación si está habilitada
                if password is not None:
                    auth_header = headers.get('authorization', '')
                    expected_auth = f"Bearer {password}"
                    if auth_header != expected_auth:
                        # No autenticado - devolver 401 Unauthorized
                        response = b"HTTP/1.1 401 Unauthorized\r\n"
                        response += b"WWW-Authenticate: Bearer\r\n"
                        response += b"Content-Type: text/html\r\n"
                        error_html = """
                        <html>
                          <head><title>401 Unauthorized</title></head>
                          <body>
                            <h1>401 Unauthorized</h1>
                            <p>Se requiere autenticación. Use el header: Authorization: Bearer {contraseña}</p>
                          </body>
                        </html>
                        """
                        error_html_bytes = error_html.encode('utf-8')
                        response += f"Content-Length: {len(error_html_bytes)}\r\n".encode('utf-8')
                        response += b"\r\n"
                        response += error_html_bytes
                        client_socket.sendall(response)
                        client_socket.close()
                        continue
                
                if method == "GET":
                    if path == "/":
                        # Generar HTML según el modo del servidor
                        # Si está en modo upload, mostrar ambas opciones
                        modo_actual = 'both' if modo_upload else 'download'
                        html_content = generar_html_interfaz(modo_actual, directorio_archivos="archivos_servidor")
                        html_bytes = html_content.encode('utf-8')
                        
                        # Verificar si el cliente acepta compresión gzip
                        acepta_gzip = False
                        if comprimir_gzip:
                            accept_encoding = headers.get('accept-encoding', '')
                            if 'gzip' in accept_encoding.lower():
                                acepta_gzip = True
                        
                        # Comprimir HTML si está habilitado y el cliente lo acepta
                        if acepta_gzip:
                            html_bytes = gzip.compress(html_bytes)
                        
                        # Construir respuesta HTTP con el HTML
                        response = b"HTTP/1.1 200 OK\r\n"
                        response += b"Content-Type: text/html\r\n"
                        if acepta_gzip:
                            response += b"Content-Encoding: gzip\r\n"
                        response += f"Content-Length: {len(html_bytes)}\r\n".encode('utf-8')
                        response += b"\r\n"
                        response += html_bytes
                    elif path == "/download":
                        # Si hay un parámetro archivo en la query, usarlo; sino usar archivo_descarga
                        archivo_a_descargar = archivo_descarga
                        if 'archivo' in query_params:
                            nombre_archivo = query_params['archivo']
                            archivo_a_descargar = os.path.join("archivos_servidor", nombre_archivo)
                        response = manejar_descarga(archivo_a_descargar, request_line, headers=headers, comprimir_gzip=comprimir_gzip)
                    else:
                        # Ruta no encontrada
                        response = b"HTTP/1.1 404 Not Found\r\n\r\n"
                    body_completo = None

                elif method == "POST":
                    # 1) Asegurar lectura COMPLETA del body según content-length:
                    #    headers y body_inicial ya fueron parseados arriba con parsear_headers_y_body
                    body_completo = body_inicial
                    try:
                        content_length = int(headers.get("content-length", "0"))
                    except ValueError:
                        content_length = 0

                    # Leer lo que falta si el body no llegó todo en el primer recv
                    bytes_faltantes = content_length - len(body_completo)
                    while bytes_faltantes > 0:
                        chunk = client_socket.recv(min(65535, bytes_faltantes))
                        if not chunk:
                            break
                        body_completo += chunk
                        bytes_faltantes -= len(chunk)

                    # 2) Procesar la ruta
                    if path == "/" or path == "":
                        boundary = extraer_boundary(headers)

                        if boundary and body_completo:
                            # Asegurar directorio de destino para guardar archivos
                            if not os.path.exists("archivos_servidor"):
                                os.makedirs("archivos_servidor", exist_ok=True)

                            # Procesar el archivo subido
                            response = manejar_carga(body_completo, boundary, directorio_destino="archivos_servidor")

                            # 3) Si GZIP está habilitado y el cliente lo admite -> comprimir respuesta HTML
                            if comprimir_gzip:
                                accept_encoding = headers.get('accept-encoding', '')
                                if 'gzip' in accept_encoding.lower():
                                    # Sacar headers y body
                                    response_parts = response.split(b'\r\n\r\n', 1)
                                    if len(response_parts) == 2:
                                        headers_resp, body_resp = response_parts
                                        body_comprimido = gzip.compress(body_resp)

                                        # Actualizar Content-Length en los headers
                                        headers_resp = headers_resp.replace(
                                            f'Content-Length: {len(body_resp)}'.encode('utf-8'),
                                            f'Content-Length: {len(body_comprimido)}'.encode('utf-8')
                                        )
                                        # Agregar Content-Encoding si no está
                                        if b'Content-Encoding: gzip' not in headers_resp:
                                            headers_resp = headers_resp.replace(
                                                b'Content-Type: text/html\r\n',
                                                b'Content-Type: text/html\r\nContent-Encoding: gzip\r\n'
                                            )

                                        response = headers_resp + b'\r\n\r\n' + body_comprimido
                        else:
                            # No había boundary o body -> no se pudo procesar el POST
                            response = b"HTTP/1.1 400 Bad Request\r\n\r\n"

                    else:
                        # Si hacen POST a otra ruta, devolvés el HTML normal
                        modo_actual = 'both' if modo_upload else 'download'
                        html_content = generar_html_interfaz(modo_actual, directorio_archivos="archivos_servidor")
                        html_bytes = html_content.encode('utf-8')

                        # Compresión si aplica
                        acepta_gzip = False
                        if comprimir_gzip:
                            accept_encoding = headers.get('accept-encoding', '')
                            if 'gzip' in accept_encoding.lower():
                                acepta_gzip = True
                        if acepta_gzip:
                            html_bytes = gzip.compress(html_bytes)

                        response = b"HTTP/1.1 200 OK\r\n"
                        response += b"Content-Type: text/html\r\n"
                        if acepta_gzip:
                            response += b"Content-Encoding: gzip\r\n"
                        response += f"Content-Length: {len(html_bytes)}\r\n".encode('utf-8')
                        response += b"\r\n"
                        response += html_bytes

                # Enviar la respuesta al cliente
                if medir_tiempo:
                    inicio = time.perf_counter()
                    client_socket.sendall(response)
                    duracion = time.perf_counter() - inicio
                    tamaño_respuesta = len(response)
                    print(f"[MEDICIÓN] Tiempo de envío: {duracion:.20f} s | Tamaño respuesta: {tamaño_respuesta} bytes")
                else:
                    client_socket.sendall(response)
                # Cerrar la conexión
                client_socket.close()
                
            except ConnectionResetError:
                # El cliente cerró la conexión abruptamente
                try:
                    print(f"Conexión cerrada por el cliente")
                    if client_socket:
                        client_socket.close()
                except:
                    pass
                continue
            except Exception as e:
                # Cualquier otro error
                print(f"Error al procesar la solicitud: {e}")
                try:
                    if client_socket:
                        client_socket.close()
                except:
                    pass
                continue
    except KeyboardInterrupt:
        # El usuario interrumpió el servidor con Ctrl+C
        print("\nServidor detenido por el usuario.")
        server_socket.close()
    finally:
        # Asegurar que el socket se cierre correctamente
        try:
            server_socket.close()
        except:
            pass


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python codigo_base.py upload [--gzip] [--password CONTRASEÑA] [--measure]                         # Servidor para subir archivos")
        print("  python codigo_base.py download archivo.txt [--gzip] [--password CONTRASEÑA] [--measure]          # Servidor para descargar un archivo")
        sys.exit(1)

    # Verificar si se solicitó compresión gzip
    comprimir_gzip = '--gzip' in sys.argv or '-g' in sys.argv
    
    # Verificar si se solicitó medición de tiempo
    medir_tiempo = '--measure' in sys.argv or '--timing' in sys.argv
    
    # Verificar si se especificó contraseña
    password = None
    if '--password' in sys.argv:
        try:
            password_index = sys.argv.index('--password')
            if password_index + 1 < len(sys.argv):
                password = sys.argv[password_index + 1]
            else:
                print("Error: --password requiere un valor")
                sys.exit(1)
        except ValueError:
            pass
    
    # Filtrar argumentos de opciones
    opciones_a_filtrar = ['--gzip', '-g', '--password', '--measure', '--timing']
    if password is not None:
        opciones_a_filtrar.append(password)
    args = [arg for arg in sys.argv[1:] if arg not in opciones_a_filtrar]
    
    if len(args) < 1:
        print("Comando no reconocido")
        sys.exit(1)
    
    comando = args[0].lower()

    if comando == "upload":
        start_server(archivo_descarga=None, modo_upload=True, comprimir_gzip=comprimir_gzip, password=password, medir_tiempo=medir_tiempo)

    elif comando == "download" and len(args) > 1:
        archivo = args[1]
        # Crear el directorio si no existe
        if not os.path.exists("archivos_servidor"):
            os.makedirs("archivos_servidor", exist_ok=True)
        ruta_archivo = os.path.join("archivos_servidor", archivo)
        start_server(archivo_descarga=ruta_archivo, modo_upload=False, comprimir_gzip=comprimir_gzip, password=password, medir_tiempo=medir_tiempo)

    else:
        print("Comando no reconocido o archivo faltante")
        sys.exit(1)
