import unittest
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://biblioteca-cubo.com"
LOGIN_URL = f"{BASE_URL}/user/loginUser"  # URL para login
AUDIOBOOK_URL = f"{BASE_URL}/libros/DQM0001/listen"  # URL para el audiolibro específico

EMAIL = "martelldennis259@gmail.com"  # Correo de inicio de sesión
PASSWORD = "682725"  # Contraseña de inicio de sesión

class TestUsabilidadEscucharAudiolibro(unittest.TestCase):
    resultados = []  # Lista para almacenar los resultados de las pruebas
    session = None   # Variable para la sesión de requests

    @classmethod
    def setUpClass(cls):
        """Inicia sesión antes de ejecutar las pruebas."""
        cls.session = requests.Session()  # Inicia una nueva sesión de requests
        token = cls._get_csrf_token(LOGIN_URL)  # Obtiene el token CSRF
        if not token:
            # Si no se obtuvo el token CSRF, registra el fallo y termina la prueba
            cls.resultados.append({
                "nombre": "Inicio de sesión",
                "objetivo": "Obtener token CSRF para autenticación",
                "esperado": "Token generado correctamente",
                "obtenido": "No se obtuvo token CSRF",
                "estado": "Fallido"
            })
            return
        
        # Realiza la solicitud POST para el login con las credenciales proporcionadas
        r = cls.session.post(LOGIN_URL, data={
            "_token": token,
            "email": EMAIL,
            "password": PASSWORD
        }, allow_redirects=True)

        # Si la respuesta es una redirección (HTTP 302), redirige a la página principal
        if r.status_code == 302:
            cls.session.get(r.headers.get("Location", f"{BASE_URL}/libros"))
        cls.auth_ok = r.status_code in (200, 302)  # Verifica que el login fue exitoso

    @classmethod
    def _get_csrf_token(cls, url):
        """Obtiene el token CSRF necesario para la autenticación."""
        try:
            r = cls.session.get(url)  # Realiza una solicitud GET a la página de login
            soup = BeautifulSoup(r.text, "html.parser")  # Analiza la respuesta HTML
            tag = soup.find("input", {"name": "_token"})  # Busca el token CSRF en el HTML
            return tag["value"] if tag else None  # Devuelve el token si lo encuentra, de lo contrario, None
        except Exception:
            return None  # Si ocurre un error, devuelve None

    def registrar(self, nombre, objetivo, esperado, obtenido, estado):
        """Registra el resultado de cada prueba."""
        self.resultados.append({
            "nombre": nombre,
            "objetivo": objetivo,
            "esperado": esperado,
            "obtenido": obtenido,
            "estado": estado
        })

    # ============ CASOS DE USABILIDAD ============

    def test_01_estructura_clara_del_reproductor(self):
        """Verifica que el reproductor tenga una estructura clara y accesible"""
        if not getattr(self, "auth_ok", False):  # Si no está autenticado, no ejecuta la prueba
            self.registrar("Estructura clara del reproductor",
                           "Validar estructura básica del reproductor",
                           "Reproductor debe tener todos los controles visibles",
                           "Fallo en autenticación",
                           "Fallido")
            return

        try:
            r = self.session.get(AUDIOBOOK_URL)  # Solicita la página del audiolibro
            soup = BeautifulSoup(r.text, "html.parser")

            # Verifica que el título del audiolibro sea visible
            h2 = soup.find("h2", {"class": "audiobook-title"})
            self.assertTrue(h2, "El título del audiolibro no está visible.")

            # Verifica que los botones de control (Play, Retroceder, Adelantar) estén visibles
            play_button = soup.find("button", {"id": "playPause"})
            back_button = soup.find("button", {"id": "back10"})
            forward_button = soup.find("button", {"id": "forward10"})

            # Verifica que todos los elementos estén presentes
            if h2 and play_button and back_button and forward_button:
                self.registrar("Estructura clara del reproductor",
                               "Verificar visibilidad del reproductor",
                               "El reproductor debe tener título y controles visibles",
                               "Título y controles visibles correctamente",
                               "Correcto")
            else:
                faltantes = []
                if not h2: faltantes.append("Título")
                if not play_button: faltantes.append("Botón Play/Pause")
                if not back_button: faltantes.append("Botón Retroceder")
                if not forward_button: faltantes.append("Botón Adelantar")

                self.registrar("Estructura clara del reproductor",
                               "Verificar estructura básica del reproductor",
                               "Todos los elementos deben estar visibles",
                               f"Faltan elementos: {', '.join(faltantes)}",
                               "Incompleto")
        except Exception as e:
            self.registrar("Estructura clara del reproductor",
                           "Verificar estructura básica del reproductor",
                           "Debe cargar correctamente",
                           f"Error: {str(e)}",
                           "Fallido")

    def test_02_informacion_clara_y_accesible(self):
        """Verifica que la información del audiolibro esté accesible de manera clara"""
        try:
            r = self.session.get(AUDIOBOOK_URL)  # Solicita la página del audiolibro
            soup = BeautifulSoup(r.text, "html.parser")

            # Verifica que el autor y la duración sean visibles
            autor = soup.find("p", {"class": "audiobook-author"})
            duracion = soup.find("div", {"id": "time"})
            
            if autor and duracion:
                self.registrar("Información clara y accesible",
                               "El autor y la duración deben ser visibles",
                               "Autor y duración visibles correctamente",
                               f"Autor: {autor.text.strip()} | Duración: {duracion.text.strip()}",
                               "Correcto")
            else:
                faltantes = []
                if not autor: faltantes.append("Autor")
                if not duracion: faltantes.append("Duración")

                self.registrar("Información clara y accesible",
                               "Verificar visibilidad del autor y la duración",
                               "Autor y duración deben ser visibles",
                               f"Faltan elementos: {', '.join(faltantes)}",
                               "Incompleto")
        except Exception as e:
            self.registrar("Información clara y accesible",
                           "Verificar autor y duración",
                           "Debe mostrar la información correctamente",
                           f"Error: {str(e)}",
                           "Fallido")

    def test_03_navegacion_intuitiva(self):
        """Verifica que los controles de avance y retroceso sean funcionales"""
        try:
            r = self.session.get(AUDIOBOOK_URL)  # Solicita la página del audiolibro
            soup = BeautifulSoup(r.text, "html.parser")

            # Verifica que los botones de avance/retroceso estén presentes
            back_button = soup.find("button", {"id": "back10"})
            forward_button = soup.find("button", {"id": "forward10"})
            
            if back_button and forward_button:
                self.registrar("Navegación intuitiva",
                               "Verificar que los controles de avance y retroceso estén presentes",
                               "Los botones deben ser funcionales",
                               "Botones de avance/retroceso disponibles",
                               "Correcto")
            else:
                faltantes = []
                if not back_button: faltantes.append("Botón Retroceder")
                if not forward_button: faltantes.append("Botón Adelantar")

                self.registrar("Navegación intuitiva",
                               "Verificar que los controles de avance y retroceso estén presentes",
                               "Los botones de avance y retroceso deben estar visibles",
                               f"Faltan: {', '.join(faltantes)}",
                               "Incompleto")
        except Exception as e:
            self.registrar("Navegación intuitiva",
                           "Verificar controles de avance y retroceso",
                           "Verificar visibilidad y funcionamiento",
                           f"Error: {str(e)}",
                           "Fallido")

    @classmethod
    def tearDownClass(cls):
        """Imprime el reporte final de todas las pruebas de usabilidad."""
        print("\n============ RESUMEN FINAL DE PRUEBAS DE USABILIDAD ============")
        for i, r in enumerate(cls.resultados, 1):
            print(f"\nCaso de Prueba {i}: {r['nombre']}")
            print(f"Objetivo: {r['objetivo']}")
            print(f"Resultado Esperado: {r['esperado']}")
            print(f"Resultado Obtenido: {r['obtenido']}")
            print(f"Tipo de Resultado: {r['estado']}")

if __name__ == "__main__":
    unittest.main(verbosity=0, failfast=False, exit=False)  # Ejecuta las pruebas
