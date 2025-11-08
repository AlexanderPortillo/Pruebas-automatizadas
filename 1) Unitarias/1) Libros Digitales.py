import unittest
import requests
from bs4 import BeautifulSoup
import time

BASE_URL = "http://127.0.0.1:8000"  # URL base de la aplicación
LOGIN_URL = f"{BASE_URL}/user/loginUser"  # URL para iniciar sesión
LIBROS_URL = f"{BASE_URL}/admin/gestion/libros/digitales"  # URL para gestionar los libros digitales

EMAIL = "martelldennis259@gmail.com"  # Correo de inicio de sesión
PASSWORD = "682725"  # Contraseña de inicio de sesión

class TestUnitLibros(unittest.TestCase):
    resultados = []  # Lista para almacenar los resultados de las pruebas

    def setUp(self):
        # Configura una nueva sesión para las pruebas
        self.session = requests.Session()
        self.token = self._get_csrf_token(LOGIN_URL)  # Obtiene el token CSRF
        self._login()  # Realiza el login con las credenciales

    def _get_csrf_token(self, url):
        # Obtiene el token CSRF desde la página de login
        r = self.session.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        tag = soup.find("input", {"name": "_token"})
        return tag["value"] if tag else None  # Devuelve el token o None si no lo encuentra

    def _login(self):
        # Realiza el login enviando el email y contraseña junto con el token CSRF
        data = {"_token": self.token, "email": EMAIL, "password": PASSWORD}
        r = self.session.post(LOGIN_URL, data=data, allow_redirects=True)
        if r.status_code == 302:
            self.session.get(r.headers.get("Location", f"{BASE_URL}/admin"))  # Redirige al panel de admin

    def _registrar_resultado(self, nombre, esperado, obtenido, estado):
        # Registra el resultado de cada prueba
        self.resultados.append({
            "Caso": nombre,
            "Esperado": esperado,
            "Obtenido": obtenido,
            "Estado": estado
        })

    def _get_ultimo_libro_id(self):
        # Obtiene el ID del último libro listado en la página de libros
        r = self.session.get(LIBROS_URL)
        soup = BeautifulSoup(r.text, "html.parser")
        boton = soup.find("button", {"class": "btn-edit"})
        return boton["data-id"] if boton else None  # Devuelve el ID del libro o None si no lo encuentra

    # Prueba para crear un libro
    def test_crear_libro(self):
        token = self._get_csrf_token(LIBROS_URL)  # Obtiene el token CSRF para crear libro
        codigo = f"LD{int(time.time())}"  # Genera un código único para el libro basado en el tiempo
        data = {
            "_token": token,
            "titulo": "Libro de Prueba",
            "codigo": codigo,
            "autor": "Autor Unitario",
            "categoria_id": 1,
            "permiso_acceso": "publico",
            "estado": "habilitado",
            "portada_url": "https://ejemplo.com/portada.jpg",
            "archivo_url": "https://ejemplo.com/libro.pdf"
        }
        r = self.session.post(LIBROS_URL, data=data, allow_redirects=True)  # Envía la solicitud para crear el libro
        estado = "Correcto" if r.status_code in [200, 302] else "Incorrecto"  # Verifica si la creación fue exitosa
        self._registrar_resultado(
            "Creación de libro digital",
            "Registro exitoso (HTTP 200/302)",
            f"HTTP {r.status_code}",
            estado
        )
        self.assertIn(r.status_code, [200, 302])  # Asegura que la respuesta sea 200 o 302

    # Prueba para editar un libro
    def test_editar_libro(self):
        libro_id = self._get_ultimo_libro_id()  # Obtiene el ID del último libro
        self.assertIsNotNone(libro_id, "No se encontró el libro a editar.")  # Verifica que se haya encontrado un libro
        token = self._get_csrf_token(LIBROS_URL)
        data = {
            "_token": token,
            "titulo": "Libro Editado Unitario",
            "codigo": "LD999",
            "autor": "Autor Editado",
            "categoria_id": 1,
            "permiso_acceso": "privado",
            "estado": "deshabilitado",
            "portada_url": "https://ejemplo.com/nueva.jpg",
            "archivo_url": "https://ejemplo.com/nuevo.pdf"
        }
        r = self.session.put(f"{LIBROS_URL}/{libro_id}", data=data, allow_redirects=True)  # Envía la solicitud para editar el libro
        estado = "Correcto" if r.status_code in [200, 302] else "Incorrecto"
        self._registrar_resultado(
            "Edición de libro digital",
            "Actualización exitosa (HTTP 200/302)",
            f"HTTP {r.status_code}",
            estado
        )
        self.assertIn(r.status_code, [200, 302])

    # Prueba para eliminar un libro
    def test_eliminar_libro(self):
        libro_id = self._get_ultimo_libro_id()  # Obtiene el ID del último libro
        self.assertIsNotNone(libro_id, "No se encontró libro para eliminar.")  # Verifica que el libro exista
        token = self._get_csrf_token(LIBROS_URL)
        data = {"_token": token, "_method": "DELETE"}  # Prepara la solicitud de eliminación
        r = self.session.post(f"{LIBROS_URL}/{libro_id}", data=data, allow_redirects=True)  # Envía la solicitud para eliminar el libro
        estado = "Correcto" if r.status_code in [200, 302] else "Incorrecto"
        self._registrar_resultado(
            "Eliminación de libro digital",
            "Borrado exitoso (HTTP 200/302)",
            f"HTTP {r.status_code}",
            estado
        )
        self.assertIn(r.status_code, [200, 302])

    @classmethod
    def tearDownClass(cls):
        # Muestra un resumen de todos los resultados después de ejecutar todas las pruebas
        print("\n========== RESUMEN FINAL DE PRUEBAS UNITARIAS ==========")
        for r in cls.resultados:
            print(f"{r['Estado']} | {r['Caso']}")
            print(f"   Esperado: {r['Esperado']}")
            print(f"   Obtenido: {r['Obtenido']}")
            print("----------------------------------------------------")
        print("========================================================\n")

if __name__ == "__main__":
    unittest.main(verbosity=0)  # Ejecuta las pruebas sin mostrar detalles adicionales
