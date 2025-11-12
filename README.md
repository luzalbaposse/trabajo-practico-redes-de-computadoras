# Servidor de Transferencia de Archivos HTTP

Servidor web minimalista en Python para transferir archivos entre dispositivos en una red local mediante HTTP sobre TCP.

## Características

- Modo **Upload**: Subir archivos al servidor
- Modo **Download**: Descargar archivos desde el servidor
- Modo **Combinado**: Subir y descargar archivos
- Compresión **gzip**: Reduce el tamaño de las transferencias
- Autenticación básica: Protege el servidor con contraseña (opcional)
- Código QR: Genera automáticamente un código QR con la URL

## Instalación

```bash
pip install qrcode
```

## Uso

### Comandos básicos

```bash
# Modo upload (subir archivos)
python3 codigo_base.py upload

# Modo download (servir archivo específico)
python3 codigo_base.py download archivo.txt
```

### Flags disponibles

| Flag | Descripción | Ejemplo |
|------|-------------|---------|
| `--gzip` o `-g` | Habilita compresión gzip | `python3 codigo_base.py upload --gzip` |
| `--password CONTRASEÑA` | Protege el servidor con contraseña | `python3 codigo_base.py upload --password redes2025` |
| `--measure` o `--timing` | Activa mediciones de tiempo para experimentos | `python3 codigo_base.py upload --measure` |
| `PUERTO=N` | Especifica el puerto (variable de entorno) | `PUERTO=8080 python3 codigo_base.py upload` |

### Combinar opciones

```bash
python3 codigo_base.py upload --gzip --password redes2025 --measure
python3 codigo_base.py download archivo.txt --gzip --password redes2025
```

## Ejemplos

### Servidor básico

```bash
python3 codigo_base.py upload
```

El servidor mostrará la URL y un código QR para escanear.

### Servidor con todas las opciones

```bash
python3 codigo_base.py upload --gzip --password redes2025 --measure
```

### Servir archivo específico

```bash
mkdir -p archivos_servidor
echo "Contenido" > archivos_servidor/test.txt
python3 codigo_base.py download test.txt
```

## Notas importantes

- El servidor acepta **una conexión a la vez**
- Los archivos se guardan en `archivos_servidor/` (se crea automáticamente)
- Presiona `Ctrl+C` para detener el servidor
- La IP mostrada es la IP local de tu red Wi-Fi/Ethernet