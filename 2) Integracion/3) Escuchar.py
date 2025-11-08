import unittest
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# URLs de la aplicación para las pruebas
BASE_URL = "https://biblioteca-cubo.com"
LOGIN_URL = f"{BASE_URL}/user/loginUser"  # URL para iniciar sesión
CATALOGO_URL = f"{BASE_URL}/libros"  # URL para el catálogo de libros
AUDIOBOOK_URL = f"{BASE_URL}/libros/DQM0001/listen"  # URL para escuchar el audiolibro específico

# Credenciales para el login
EMAIL = "admin@cubo.com"
PASSWORD = "admin2025"

class TestIntegracionEscucharAudiolibro(unittest.TestCase):
    resultados = []  # Lista para almacenar los resultados de las pruebas
    session = None   # Variable para la sesión HTTP

    @classmethod
    def setUpClass(cls):
        """Inicia sesión antes de ejecutar las pruebas."""
        cls.session = requests.Session()  # Inicia una nueva sesión de requests
        token = cls._get_csrf_token(LOGIN_URL)  # Obtiene el token CSRF necesario para el login

        # Si no se obtiene el token CSRF, se registra un fallo en los resultados
        if not token:
            cls.resultados.append({
                "nombre": "Inicio de sesión",
                "objetivo": "Autenticar el acceso al sistema",
                "esperado": "Iniciar sesión y obtener token CSRF correctamente",
                "obtenido": "No se obtuvo el token CSRF",
                "estado": "Fallido"
            })
            return

        # Realiza el login con las credenciales proporcionadas
        r = cls.session.post(LOGIN_URL, data={
            "_token": token,
            "email": EMAIL,
            "password": PASSWORD
        }, allow_redirects=True)

        # Si la respuesta es una redirección, sigue a la página de libros
        if r.status_code == 302:
            cls.session.get(r.headers.get("Location", f"{BASE_URL}/libros"))
        cls.auth_ok = r.status_code in (200, 302)  # Verifica que el login fue exitoso

    @classmethod
    def _get_csrf_token(cls, url):
        """Obtiene el token CSRF necesario para enviar formularios."""
        try:
            r = cls.session.get(url)  # Realiza una solicitud GET a la URL de login
            soup = BeautifulSoup(r.text, "html.parser")  # Parseo del HTML de la página
            tag = soup.find("input", {"name": "_token"})  # Busca el token CSRF
            return tag["value"] if tag else None  # Devuelve el token si lo encuentra
        except Exception:
            return None  # Si hay un error, devuelve None

    def registrar(self, nombre, objetivo, esperado, obtenido, estado):
        """Registra el resultado de cada caso de prueba."""
        self.resultados.append({
            "nombre": nombre,
            "objetivo": objetivo,
            "esperado": esperado,
            "obtenido": obtenido,
            "estado": estado
        })

    def test_01_catalogo_a_reproductor(self):
        """Verifica la redirección desde el catálogo hacia el reproductor."""
        # Si el login no fue exitoso, registra el fallo y termina la prueba
        if not getattr(self, "auth_ok", False):
            self.registrar(
                "Flujo catálogo → reproductor",
                "Validar acceso desde el catálogo hacia el audiolibro",
                "El usuario debe estar autenticado antes de acceder al reproductor",
                "No se logró iniciar sesión correctamente",
                "Fallido"
            )
            return

        try:
            # Solicita el catálogo de libros
            r = self.session.get(CATALOGO_URL)
            soup = BeautifulSoup(r.text, "html.parser")
            boton = soup.find("a", {"class": "btn-listen"})  # Busca el botón 'Escuchar'
            link = boton["href"] if boton else None  # Obtiene el enlace del botón 'Escuchar'

            # Si el enlace es encontrado, accede a él y verifica la respuesta
            if link:
                r2 = self.session.get(link)
                estado = "Correcto" if r2.status_code == 200 else "Incorrecto"
                obtenido = f"HTTP={r2.status_code}, Enlace detectado: {link}"
            else:
                estado = "Incorrecto"
                obtenido = "No se encontró el botón 'Escuchar' en el catálogo"

            # Registra el resultado de esta prueba
            self.registrar(
                "Redirección desde el catálogo al reproductor",
                "Comprobar que el botón 'Escuchar' lleve correctamente al reproductor del audiolibro",
                "El enlace 'Escuchar' debe redirigir a la página de reproducción sin errores",
                obtenido,
                estado
            )
        except Exception as e:
            # Si ocurre algún error, registra el fallo
            self.registrar(
                "Redirección desde el catálogo al reproductor",
                "Verificar enlace funcional",
                "Debe abrir la página de reproducción sin errores de conexión",
                f"Error: {str(e)}",
                "Fallido"
            )

    def test_02_estructura_reproductor(self):
        """Verifica que el reproductor cargue correctamente todos sus elementos visuales."""
        try:
            # Solicita la página del reproductor
            r = self.session.get(AUDIOBOOK_URL)
            soup = BeautifulSoup(r.text, "html.parser")

            # Verifica que los elementos del reproductor estén presentes en la página
            elementos = {
                "Título": soup.find("h2") or soup.find("div", {"class": "audiobook-title"}),
                "Play/Pause": soup.find("button", {"id": "playPause"}),
                "Onda de audio": soup.find("div", {"id": "waveform"}),
                "Avance": soup.find("button", {"id": "forward10"}),
                "Retroceso": soup.find("button", {"id": "back10"})
            }
            faltantes = [k for k, v in elementos.items() if v is None]  # Lista de elementos faltantes

            # Si faltan elementos, el estado es 'Incompleto', de lo contrario es 'Correcto'
            estado = "Correcto" if not faltantes else "Incompleto"
            obtenido = (
                f"Elementos detectados correctamente"
                if not faltantes
                else f"Faltan los siguientes: {', '.join(faltantes)}"
            )

            # Registra el resultado de esta prueba
            self.registrar(
                "Verificación de la interfaz del reproductor",
                "Confirmar que la página del audiolibro muestre los controles y la estructura del reproductor",
                "El reproductor debe mostrar el título, los botones de control y la forma de onda del audio",
                obtenido,
                estado
            )
        except Exception as e:
            # Si ocurre un error, registra el fallo
            self.registrar(
                "Verificación de la interfaz del reproductor",
                "Validar estructura HTML del reproductor",
                "Debe cargar todos los elementos visuales del reproductor",
                f"Error: {str(e)}",
                "Fallido"
            )

    def test_03_validar_fuente_audio(self):
        """Comprueba que el reproductor tenga una fuente de audio válida."""
        try:
            # Solicita la página del reproductor
            r = self.session.get(AUDIOBOOK_URL)
            soup = BeautifulSoup(r.text, "html.parser")

            # Busca la onda de audio en el HTML
            waveform_div = soup.find("div", {"id": "waveform"})
            scripts = soup.find_all("script")

            audio_url = None
            for script in scripts:
                if script.string and "wavesurfer.load(" in script.string:  # Busca la función wavesurfer.load
                    start = script.string.find("wavesurfer.load(") + len("wavesurfer.load(")
                    segment = script.string[start:].split(")")[0]
                    audio_url = segment.strip(" '\"")  # Extrae la URL del audio
                    break

            valido = waveform_div is not None and audio_url is not None
            estado = "Correcto" if valido else "Incompleto"
            obtenido = (
                f"Fuente de audio detectada: {audio_url}"
                if valido else
                "No se encontró una fuente de audio válida en el script WaveSurfer.js"
            )

            # Registra el resultado de esta prueba
            self.registrar(
                "Validación de la fuente de audio (WaveSurfer.js)",
                "Confirmar que el reproductor carga correctamente la fuente del audiolibro",
                "Debe existir un contenedor #waveform y un script con wavesurfer.load('URL_DEL_AUDIO')",
                obtenido,
                estado
            )
        except Exception as e:
            # Si ocurre un error, registra el fallo
            self.registrar(
                "Validación de la fuente de audio (WaveSurfer.js)",
                "Comprobar la existencia de la fuente de audio",
                "El HTML debe contener una llamada a wavesurfer.load() con una URL válida",
                f"Error: {str(e)}",
                "Fallido"
            )

    @classmethod
    def tearDownClass(cls):
        """Imprime el reporte final de todas las pruebas de integración."""
        print("\n========== REPORTE FINAL: PRUEBAS DE INTEGRACIÓN (Escuchar Audiolibro) ==========")
        for i, r in enumerate(cls.resultados, 1):
            print(f"\nCaso de Prueba {i}: {r['nombre']}")
            print(f"Objetivo: {r['objetivo']}")
            print(f"Resultado Esperado: {r['esperado']}")
            print(f"Resultado Obtenido: {r['obtenido']}")
            print(f"Estado Final: {r['estado']}")

if __name__ == "__main__":
    unittest.main(verbosity=0, failfast=False, exit=False)  # Ejecuta las pruebas
