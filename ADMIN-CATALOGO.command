#!/bin/bash
cd "$(dirname "$0")/admin"
echo "Abriendo el panel de Locas del Aseo…"
echo "No cierres esta ventana mientras lo estés usando."
python3 servidor_admin.py
