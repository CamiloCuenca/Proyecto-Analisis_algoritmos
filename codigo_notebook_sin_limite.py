# Código para reemplazar en tu notebook Jupyter
# Copia y pega este código en una nueva celda

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import re


def esperar_descarga(download_path, timeout=30):
    """Espera a que aparezca un archivo .bib en la carpeta de descargas"""
    for _ in range(timeout):
        archivos = [f for f in os.listdir(download_path) if f.endswith(".bib")]
        if archivos:
            return os.path.join(download_path, archivos[0])
        time.sleep(1)
    return None


def obtener_total_paginas(driver):
    """
    Detecta automáticamente el número total de páginas disponibles
    """
    try:
        # Buscar el texto que indica el total de resultados
        # Ejemplo: "1-100 of 1,234 results"
        results_info = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".results-info"))
        )
        
        texto_resultados = results_info.text
        print(f"📊 Información de resultados: {texto_resultados}")
        
        # Extraer el número total de resultados usando regex
        # Buscar patrones como "of 1,234 results" o "of 1234 results"
        match = re.search(r'of\s+([\d,]+)\s+results', texto_resultados)
        if match:
            total_resultados = int(match.group(1).replace(',', ''))
            print(f"📈 Total de resultados encontrados: {total_resultados}")
            
            # Calcular número de páginas (asumiendo 100 resultados por página)
            resultados_por_pagina = 100
            total_paginas = (total_resultados + resultados_por_pagina - 1) // resultados_por_pagina
            
            print(f"📄 Total de páginas calculadas: {total_paginas}")
            return total_paginas
        
        # Método alternativo: buscar directamente en la paginación
        try:
            pagination_links = driver.find_elements(By.CSS_SELECTOR, ".pagination a")
            if pagination_links:
                # Buscar el número más alto en los enlaces de paginación
                numeros_pagina = []
                for link in pagination_links:
                    texto = link.text.strip()
                    if texto.isdigit():
                        numeros_pagina.append(int(texto))
                
                if numeros_pagina:
                    max_pagina = max(numeros_pagina)
                    print(f"📄 Páginas detectadas por paginación: {max_pagina}")
                    return max_pagina
        except:
            pass
            
    except Exception as e:
        print(f"⚠️ No se pudo detectar el total de páginas automáticamente: {e}")
    
    # Si no se puede detectar, usar un valor por defecto alto
    print("🔄 Usando detección dinámica página por página...")
    return None


def verificar_pagina_siguiente_existe(driver):
    """
    Verifica si existe un botón de 'siguiente página'
    """
    try:
        boton_siguiente = driver.find_element(By.XPATH, "//a[@data-aa-name='srp-next-page']")
        # Verificar si el botón está habilitado (no deshabilitado)
        clases = boton_siguiente.get_attribute("class") or ""
        aria_disabled = boton_siguiente.get_attribute("aria-disabled")
        
        # Si tiene clase 'disabled' o aria-disabled='true', no hay más páginas
        if "disabled" in clases.lower() or aria_disabled == "true":
            return False
        return True
    except:
        return False


# ============================================================================
# CÓDIGO PRINCIPAL SIN LIMITADOR DE PÁGINAS
# ============================================================================

# Detectar automáticamente el total de páginas
print("🔍 Detectando número total de páginas...")
total_pages = obtener_total_paginas(driver)

# Si no se pudo detectar, usar detección dinámica
if total_pages is None:
    print("📋 Modo dinámico activado: se procesarán todas las páginas disponibles")
    usar_deteccion_dinamica = True
    max_pages = float('inf')  # Sin límite
else:
    print(f"📊 Se procesarán {total_pages} páginas en total")
    usar_deteccion_dinamica = False
    max_pages = total_pages

page_numScience = 1
paginas_procesadas = 0

while True:
    print(f"\n{'='*50}")
    if usar_deteccion_dinamica:
        print(f"Procesando página {page_numScience}...")
    else:
        print(f"Procesando página {page_numScience} de {max_pages}...")

    try:
        # Seleccionar checkbox real (input, no span)
        checkbox_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#srp-toolbar input[type='checkbox']"))
        )

        # Marcarlo si no está marcado
        if not checkbox_input.is_selected():
            driver.execute_script("arguments[0].click();", checkbox_input)
            time.sleep(1)

        # Confirmar que quedó marcado
        if checkbox_input.is_selected():
            print("✅ Checkbox de 'todos los artículos' marcado correctamente")
        else:
            print("⚠️ No se pudo marcar el checkbox, reintentando...")
            driver.execute_script("arguments[0].click();", checkbox_input)
            time.sleep(1)

        # Botón de exportar
        export_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "span.export-all-link-text"))
        )
        driver.execute_script("arguments[0].click();", export_button)
        time.sleep(1)

        # Botón BibTeX
        bibtex_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-aa-button='srp-export-multi-bibtex']"))
        )

        intentos_descarga = 0
        descarga_exitosa = False
        
        while intentos_descarga < 3 and not descarga_exitosa:
            try:
                bibtex_button.click()
                print(f"Intento de descarga #{intentos_descarga+1} para página {page_numScience}")
                
                nuevo_archivo = esperar_descarga(download_path, 20)
                
                if nuevo_archivo:
                    print(f"✅ Archivo descargado: {os.path.basename(nuevo_archivo)}")
                    descarga_exitosa = True
                else:
                    print("No se pudo detectar el archivo descargado")
                    
            except Exception as e:
                print(f"Error en el intento {intentos_descarga + 1}: {e}")
            
            intentos_descarga += 1
            if not descarga_exitosa and intentos_descarga < 3:
                time.sleep(2)

        if not descarga_exitosa:
            print(f"❌ No se pudo completar la descarga para la página {page_numScience}")

        # Cerrar menú exportar
        try:
            close_button = driver.find_element(By.CSS_SELECTOR, "button.export-close-button")
            close_button.click()
            time.sleep(1)
        except:
            pass

        paginas_procesadas += 1

        # Verificar si hay más páginas disponibles
        if usar_deteccion_dinamica:
            if not verificar_pagina_siguiente_existe(driver):
                print(f"🏁 No hay más páginas disponibles. Proceso completado.")
                break
        else:
            if page_numScience >= max_pages:
                print(f"🏁 Se han procesado todas las {max_pages} páginas.")
                break

        # Pasar a la siguiente página
        try:
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            botonSiguientePag = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//a[@data-aa-name='srp-next-page']"))
            )
            driver.execute_script("arguments[0].click();", botonSiguientePag)
            print(f"🔄 Avanzando a la página {page_numScience + 1}...")
            time.sleep(5)
            page_numScience += 1
        except Exception as e:
            print(f"⚠️ No se pudo avanzar de página: {e}")
            print("🏁 Posiblemente se han procesado todas las páginas disponibles.")
            break

    except Exception as e:
        print(f"⚠️ Error en la página {page_numScience}: {e}")
        # Intentar continuar con la siguiente página
        page_numScience += 1
        continue

print(f"\n🎉 ¡Proceso completado! Se procesaron {paginas_procesadas} páginas en total.")
