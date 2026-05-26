"""Módulo para abrir la tabla periódica interactiva en el navegador."""

import os
import webbrowser
from pathlib import Path


def open_explorer():
    """Abre la tabla periódica semiconductores en el navegador por defecto."""
    # Obtener la ruta del archivo HTML
    current_dir = Path(__file__).parent
    html_path = current_dir / "periodic_table_semiconductors.html"
    
    if not html_path.exists():
        print(f"⚠️  Archivo no encontrado: {html_path}")
        print("   La tabla periódica no puede ser abierta.")
        return False
    
    try:
        # Convertir la ruta a URL para que funcione en Windows y otros SO
        file_url = html_path.as_uri()
        webbrowser.open(file_url)
        print(f"✓ Tabla periódica abierta en navegador: {html_path.name}")
        return True
    except Exception as e:
        print(f"✗ Error al abrir la tabla periódica: {e}")
        return False


if __name__ == "__main__":
    open_explorer()
