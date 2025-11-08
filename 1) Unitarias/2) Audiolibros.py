import unittest
import requests
from bs4 import BeautifulSoup
import time

BASE_URL = "http://127.0.0.1:8000"  # URL base de la aplicación
LOGIN_URL = f"{BASE_URL}/user/loginUser"  # URL para iniciar sesión
AUDIO_URL = f"{BASE_URL}/admin/gestion/libros/audiolibros"  # URL para gestionar los audiolibros

EMAIL = "martelldennis259@gmail.com"  # Correo de inicio de sesión
PASSWORD = "682725"  # Contraseña de inicio de sesión

class TestUnitAudiolibros(unittest.TestCase):
    resultados = []  # Lista para almacenar los resultados de las pruebas

    def setUp(self):
        # Configura una nueva sesión para las pruebas
        self.session = requests.Session()
        self.token = self._get_csrf_token(LOGIN_URL)  # Obtiene el token CSRF para autenticar
        self._login()  # Realiza el login con las credenciales

    def _get_csrf_token(self, url):
        # Obtiene el token CSRF necesario para la autenticación de la sesión
        r = self.session.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        tag = soup.find("input", {"name": "_token"})
        return tag["value"] if tag else None  # Devuelve el valor del token CSRF o None si no lo encuentra

    def _login(self):
        # Realiza el login enviando el correo y la contraseña junto con el token CSRF
        data = {"_token": self.token, "email": EMAIL, "password": PASSWORD}
        r = self.session.post(LOGIN_URL, data=data, allow_redirects=True)
        if r.status_code == 302:  # Si la respuesta es una redirección, indica que el login fue exitoso
            self.session.get(r.headers.get("Location", f"{BASE_URL}/admin"))  # Redirige al panel de administración

    def _registrar_resultado(self, nombre, esperado, obtenido, estado):
        # Registra el resultado de cada prueba
        self.resultados.append({
            "Caso": nombre,
            "Esperado": esperado,
            "Obtenido": obtenido,
            "Estado": estado
        })

    def _get_ultimo_audio_id(self, search="Audiolibro Unittest"):
        # Obtiene el ID del último audiolibro de la lista, buscando por un nombre específico
        r = self.session.get(AUDIO_URL)
        soup = BeautifulSoup(r.text, "html.parser")
        filas = soup.find_all("tr")
        for fila in filas:
            if search.lower() in fila.text.lower():  # Busca el audiolibro por nombre
                btn = fila.find("button", {"class": "btn-edit"})
                if btn and btn.has_attr("data-id"):  # Si el botón de editar tiene el atributo "data-id", devuelve el ID
                    return btn["data-id"]
        return None  # Si no encuentra el audiolibro, devuelve None

    # Prueba para crear un audiolibro
    def test_crear_audiolibro(self):
        token = self._get_csrf_token(AUDIO_URL)  # Obtiene el token CSRF para crear un audiolibro
        codigo = f"AU{int(time.time())}"  # Genera un código único basado en el timestamp
        data = {
            "_token": token,
            "titulo": "Audiolibro Unittest",
            "codigo": codigo,
            "autor": "Autor Test",
            "narrador": "Narrador Test",
            "duracion": "100",
            "categoria_id": 1,
            "estado": "habilitado",
            "portada_url": "https://ejemplo.com/portada.jpg",
            "audio_url": "https://ejemplo.com/audio.mp3"
        }
        # Envía una solicitud POST para crear el audiolibro
        r = self.session.post(AUDIO_URL, data=data, allow_redirects=True)
        estado = "Correcto" if r.status_code in [200, 302] else "Incorrecto"  # Verifica si la respuesta es 200 o 302
        self._registrar_resultado(
            "Creación de audiolibro",
            "Registrar audiolibro correctamente (HTTP 200/302)",
            f"HTTP {r.status_code}",
            estado
        )
        self.assertIn(r.status_code, [200, 302])  # Asegura que la respuesta sea 200 o 302

    # Prueba para editar un audiolibro
    def test_editar_audiolibro(self):
        # Obtiene el ID del último audiolibro creado
        audio_id = self._get_ultimo_audio_id("Audiolibro Unittest")
        self.assertIsNotNone(audio_id, "No se encontró el audiolibro a editar.")  # Verifica que el audiolibro existe

        token = self._get_csrf_token(AUDIO_URL)
        data = {
            "_token": token,
            "titulo": "Audiolibro Editado",
            "codigo": f"AU{int(time.time())}",
            "autor": "Autor Modificado",
            "narrador": "Narrador Modificado",
            "duracion": "120",
            "categoria_id": 1,
            "estado": "deshabilitado",
            "portada_url": "https://ejemplo.com/portada_editada.jpg",
            "audio_url": "https://ejemplo.com/audio_editado.mp3"
        }
        # Envía una solicitud PUT para editar el audiolibro
        r = self.session.put(f"{AUDIO_URL}/{audio_id}", data=data, allow_redirects=True)
        estado = "Correcto" if r.status_code in [200, 302] else "Incorrecto"
        self._registrar_resultado(
            "Edición de audiolibro",
            "Actualizar información correctamente (HTTP 200/302)",
            f"HTTP {r.status_code}",
            estado
        )
        self.assertIn(r.status_code, [200, 302])

    # Prueba para eliminar un audiolibro
    def test_eliminar_audiolibro(self):
        # Obtiene el ID del último audiolibro editado
        audio_id = self._get_ultimo_audio_id("Editado")
        self.assertIsNotNone(audio_id, "No se encontró el audiolibro a eliminar.")  # Verifica que el audiolibro exista

        token = self._get_csrf_token(AUDIO_URL)
        data = {"_token": token, "_method": "DELETE"}  # Se prepara para eliminar el audiolibro
        # Envía una solicitud POST para eliminar el audiolibro
        r = self.session.post(f"{AUDIO_URL}/{audio_id}", data=data, allow_redirects=True)
        estado = "Correcto" if r.status_code in [200, 302] else "Incorrecto"
        self._registrar_resultado(
            "Eliminación de audiolibro",
            "Eliminar registro existente correctamente (HTTP 200/302)",
            f"HTTP {r.status_code}",
            estado
        )
        self.assertIn(r.status_code, [200, 302])

    @classmethod
    def tearDownClass(cls):
        # Muestra un resumen final de los resultados de las pruebas
        print("\n========== RESUMEN FINAL DE PRUEBAS UNITARIAS ==========")
        for r in cls.resultados:
            print(f"{r['Estado']} | {r['Caso']}")
            print(f"   Esperado: {r['Esperado']}")
            print(f"   Obtenido: {r['Obtenido']}")
            print("----------------------------------------------------")
        print("========================================================\n")

if __name__ == "__main__":
    unittest.main(verbosity=0)  # Ejecuta las pruebas sin mostrar detalles adicionales
