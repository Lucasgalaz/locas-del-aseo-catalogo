#!/bin/bash
cd "$(dirname "$0")"
echo "=========================================="
echo " Subiendo cambios de Locas del Aseo a Internet"
echo "=========================================="

# Agregar todos los archivos nuevos y modificados
git add .

# Hacer el commit con la fecha actual
fecha=$(date '+%Y-%m-%d %H:%M:%S')
git commit -m "Actualizacion del catalogo - $fecha"

# Subir a GitHub
echo "Enviando a GitHub..."
git push origin main

echo "=========================================="
echo " ¡Listo! Vercel actualizará la página en unos segundos."
echo " Puedes cerrar esta ventana."
echo "=========================================="
read -p "Presiona Enter para cerrar esta ventana..."
