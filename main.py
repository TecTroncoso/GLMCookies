# get_qwen_cookies_sin_captcha.py

import os
import json
import time
import uuid
import shutil
import zipfile
from selenium import webdriver

from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys

# --- CONFIGURACIÓN ---
AUTH_URL = "https://chat.z.ai/auth"
GITHUB_LOGIN_URL = "https://github.com/login"
# Cambiamos la ruta a una ubicación accesible en el Codespace
CHROME_PROFILE_PATH = os.path.join(os.getcwd(), "chrome_profile_qwen")  # Ruta relativa al directorio actual
ZIP_FILE_PATH = os.path.join(os.getcwd(), "chrome_profile_qwen.zip")  # Ruta para el archivo ZIP
COOKIES_FILE = "cookies.json"  # Definimos la ruta del archivo de cookies

# --- CREDENCIALES (desde variables de entorno) ---
USERNAME = os.environ.get("GLM_USERNAME", "")
PASSWORD = os.environ.get("GLM_PASSWORD", "")

if not USERNAME or not PASSWORD:
    raise RuntimeError("Faltan las variables de entorno GLM_USERNAME y GLM_PASSWORD")

# --- FUNCIÓN PARA GUARDAR COOKIES ---
def save_cookies(cookies):
    """Guarda las cookies en el archivo cookies.json, sobrescribiendo si existe"""
    print(f"🍪 Guardando {len(cookies)} cookies en {COOKIES_FILE}...")
    with open(COOKIES_FILE, "w") as f:
        json.dump(cookies, f, indent=4)
    print(f"✅ Cookies guardadas exitosamente en '{COOKIES_FILE}' (sobrescribiendo si existía).")

# --- FUNCIÓN PARA VERIFICAR SESIÓN PERSISTENTE ---
def check_existing_session():
    """Verifica si existe una sesión persistente válida"""
    global driver
    
    print("✅ Perfil de Chrome existente encontrado. Intentando reutilizar sesión...")
    
    # Primero intentamos cargar la página principal directamente
    print("Inicializando el driver de Chrome con perfil existente...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 15)
    
    print("Navegando a la página principal para verificar sesión...")
    driver.get("https://chat.z.ai/")
    time.sleep(3)
    
    # Verificar si ya estamos logueados
    try:
        chat_textarea = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[placeholder*='How can I help you today?']"))
        )
        print("✅ ¡Sesión persistente encontrada! Ya estamos logueados.")
        
        # Guardar cookies (esto sobrescribirá el archivo si existe)
        cookies = driver.get_cookies()
        save_cookies(cookies)
        
        # Tomar captura de confirmación
        driver.save_screenshot("session_persisted.png")
        print("📸 Captura de sesión persistente guardada.")
        
        # Cerrar el driver y terminar la ejecución exitosamente
        driver.quit()
        print("✅ Sesión persistente verificada y cookies guardadas. Proceso finalizado.")
        return True
        
    except Exception as e:
        print(f"❌ Error al verificar sesión persistente: {e}")
        driver.save_screenshot("session_check_error.png")
        driver.quit()
        return False

# --- OPCIONES DE CHROME ---
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Comentado para ver el proceso
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-gpu")

# Crear el directorio del perfil si no existe
os.makedirs(CHROME_PROFILE_PATH, exist_ok=True)

# Usar perfil persistente de Chrome
options.add_argument(f"--user-data-dir={CHROME_PROFILE_PATH}")

print("Configuración de Selenium lista.")
print(f"Perfil de Chrome persistente en: {CHROME_PROFILE_PATH}")

driver = None
try:
    # Verificar si ya existe una sesión guardada
    profile_exists = os.path.exists(CHROME_PROFILE_PATH) and os.listdir(CHROME_PROFILE_PATH)
    if profile_exists:
        # Si la sesión persistente es válida, terminamos aquí
        if check_existing_session():
            sys.exit(0)
    
    # Si no hay perfil o la sesión no es válida, hacemos login completo
    print("❌ No hay sesión activa en el perfil. Procediendo con login completo...")
    print("Inicializando el driver de Chrome para login completo...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 30)

    # PASO 1: Navegar directamente a la página de autenticación
    print(f"Navegando directamente a {AUTH_URL}...")
    driver.get(AUTH_URL)
    print("Página de autenticación cargada.")
    print(f"URL actual: {driver.current_url}")
    
    # PASO 2: Hacer clic en el botón de GitHub
    print("Buscando el botón de GitHub...")
    github_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/div/div[1]/div[3]/div/div/div[1]/form/div[3]/button[3]"))
    )
    github_button.click()
    print("Botón de GitHub presionado.")
    
    # PASO 3: Verificar que estamos en la página de login de GitHub
    print("Verificando redirección a GitHub...")
    wait.until(EC.url_contains("github.com/login"))
    print("Página de login de GitHub cargada.")
    print(f"URL actual: {driver.current_url}")
    
    # PASO 4: Rellenar el campo de usuario de GitHub
    print("Buscando el campo de usuario de GitHub...")
    user_field = wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='login_field']")))
    user_field.send_keys(USERNAME)
    print("Usuario de GitHub introducido.")
    
    # PASO 5: Rellenar el campo de contraseña de GitHub
    print("Buscando el campo de contraseña de GitHub...")
    pass_field = wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='password']")))
    pass_field.send_keys(PASSWORD)
    print("Contraseña de GitHub introducida.")
    
    # PASO 6: Hacer clic en el botón de inicio de sesión de GitHub
    print("Buscando el botón de inicio de sesión de GitHub...")
    github_login_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div[3]/main/div/div[2]/form/div[3]/input"))
    )
    github_login_button.click()
    print("Botón de inicio de sesión de GitHub presionado.")
    
    # PASO 7: Verificar si aparece la página de verificación de dispositivo
    print("Esperando posible verificación de dispositivo...")
    time.sleep(5)
    
    print(f"URL después del login: {driver.current_url}")
    
    # Verificar si estamos en la página de verificación de dispositivo
    verification_attempts = 0
    max_attempts = 5
    
    while ("verify" in driver.current_url or any(keyword in driver.current_url for keyword in ["device", "otp", "verification"])) and verification_attempts < max_attempts:
        verification_attempts += 1
        print(f"\n🔐 Intento de verificación #{verification_attempts}")
        print(f"URL de verificación: {driver.current_url}")
        
        try:
            # Buscar el campo de código de verificación
            print("Buscando campo de código de verificación...")
            verification_field = wait.until(
                EC.presence_of_element_located((By.NAME, "otp"))
            )
            
            # TOMAR CAPTURA DE PANTALLA ANTES DE PEDIR EL CÓDIGO
            driver.save_screenshot(f"verification_attempt_{verification_attempts}_before.png")
            print(f"📸 Captura de pantalla guardada en 'verification_attempt_{verification_attempts}_before.png'")
            
            # Pedir al usuario que ingrese el código manualmente
            if verification_attempts == 1:
                print("\n📧 GitHub ha enviado un código de verificación a tu email.")
                print("   Revisa tu bandeja de entrada y busca el código de 6 dígitos.")
            else:
                print("\n🔁 Código incorrecto o expirado. Por favor ingresa un nuevo código.")
            
            verification_code = input("   Por favor, ingresa el código de verificación: ").strip()
            
            # Limpiar el campo y ingresar el código
            verification_field.clear()
            verification_field.send_keys(verification_code)
            print("✅ Código de verificación ingresado.")
            
            # TOMAR CAPTURA DE PANTALLA DESPUÉS DE INGRESAR EL CÓDIGO
            driver.save_screenshot(f"verification_attempt_{verification_attempts}_after_input.png")
            print(f"📸 Captura con código ingresado guardada en 'verification_attempt_{verification_attempts}_after_input.png'")
            
            # Esperar a ver si se redirige automáticamente (código correcto)
            print("⏳ Esperando redirección automática (5 segundos)...")
            time.sleep(5)
            
            # Verificar si todavía estamos en la página de verificación
            current_url = driver.current_url
            print(f"URL actual después de esperar: {current_url}")
            
            if "verify" not in current_url and all(keyword not in current_url for keyword in ["device", "otp", "verification"]):
                print("✅ ¡Redirección automática detectada! Código correcto.")
                break
            
            # Si todavía estamos en la página de verificación, el código fue incorrecto
            print("❌ El código parece ser incorrecto o ha expirado.")
            
            # Verificar si hay mensaje de error
            try:
                error_message = driver.find_element(By.CSS_SELECTOR, ".flash-error, .error, .text-red")
                print(f"⚠️  Mensaje de error: {error_message.text}")
            except:
                print("ℹ️  No se detectó mensaje de error específico.")
            
            # Tomar captura del error
            driver.save_screenshot(f"verification_attempt_{verification_attempts}_failed.png")
            print(f"📸 Captura del error guardada en 'verification_attempt_{verification_attempts}_failed.png'")
            
            if verification_attempts >= max_attempts:
                print(f"🚫 Límite de {max_attempts} intentos alcanzado.")
                raise Exception("Demasiados intentos fallidos de verificación")
                
        except Exception as e:
            print(f"❌ Error en el intento de verificación: {e}")
            driver.save_screenshot(f"verification_attempt_{verification_attempts}_error.png")
            
            if verification_attempts >= max_attempts:
                raise Exception(f"Demasiados errores en verificación: {e}")
    
    # PASO 8: Esperar a que se complete el login y redirija de vuelta
    print("Esperando confirmación de login final...")
    try:
        wait.until(EC.url_contains("chat.z.ai"))
        print(f"✅ URL final: {driver.current_url}")
        # Tomar captura de la página final
        driver.save_screenshot("login_success.png")
        print("📸 Captura de login exitoso guardada en 'login_success.png'")
    except:
        print("⚠️  No se pudo redirigir a chat.z.ai, continuando...")
        driver.save_screenshot("login_redirect_issue.png")
        print("📸 Captura del problema de redirección guardada.")
    
    # Verificar que el login fue exitoso
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[placeholder*='How can I help you today?']")))
        print("✅ ¡Login exitoso! Se ha cargado la página principal del chat.")
        driver.save_screenshot("chat_loaded.png")
        print("📸 Captura del chat cargado guardada.")
        
        # Guardar información adicional sobre la sesión persistente
        print(f"💾 Guardando sesión persistente en: {CHROME_PROFILE_PATH}")
        
        # Crear un archivo de marca para indicar que la sesión es válida
        with open(os.path.join(CHROME_PROFILE_PATH, "session_info.txt"), "w") as f:
            f.write(f"Session created: {time.ctime()}\n")
            f.write(f"Username: {USERNAME}\n")
            f.write(f"URL: {driver.current_url}\n")
        
        print("✅ Sesión persistente guardada correctamente.")
        
    except:
        print("⚠️  No se encontró el textarea del chat, pero continuando...")
        driver.save_screenshot("chat_not_loaded.png")
        print("📸 Captura del chat no cargado guardada.")
    
    # PASO 9: Obtener y guardar las cookies
    cookies = driver.get_cookies()
    save_cookies(cookies)  # Usamos nuestra función para guardar las cookies

except Exception as e:
    print("\n--- ❌ OCURRIÓ UN ERROR DURANTE LA EJECUCIÓN ---")
    print(type(e).__name__, ":", e)
    print(f"URL en el momento del error: {driver.current_url if driver else 'N/A'}")
    
    if driver:
        driver.save_screenshot("final_error.png")
        with open("final_error.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("📸 Captura de pantalla final guardada en 'final_error.png'")
        print("📄 HTML de la página guardado en 'final_error.html'")

finally:
    if driver:
        print("Cerrando el driver de Selenium para guardar el perfil...")
        driver.quit()
        print("Driver cerrado. Perfil guardado persistentemente.")
        print(f"📍 Perfil de Chrome guardado en: {CHROME_PROFILE_PATH}")
        
        # Comprimir el perfil para descargarlo fácilmente
        print("🗜️ Comprimiendo el perfil para descargar...")
        with zipfile.ZipFile(ZIP_FILE_PATH, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(CHROME_PROFILE_PATH):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, CHROME_PROFILE_PATH)
                    zipf.write(file_path, arcname)
        
        print(f"✅ Perfil comprimido en: {ZIP_FILE_PATH}")
        print("\n" + "="*60)
        print("📥 INSTRUCCIONES PARA DESCARGAR Y USAR EL PERFIL:")
        print("="*60)
        print("1. En tu Codespace, haz clic en el icono de Explorador (panel izquierdo)")
        print("2. Busca el archivo 'chrome_profile_qwen.zip' en la raíz del workspace")
        print("3. Haz clic derecho sobre él y selecciona 'Download'")
        print("4. Descomprime el archivo en una carpeta en tu computadora")
        print("5. En tu otro código, modifica la ruta del perfil para que apunte a esta carpeta")
        print("6. Ejemplo de cómo usarlo en otro código:")
        print("   ```python")
        print("   options = webdriver.ChromeOptions()")
        print("   options.add_argument('--user-data-dir=/ruta/a/tu/carpeta/descomprimida')")
        print("   driver = webdriver.Chrome(options=options)")
        print("   ```")
        print("="*60)
