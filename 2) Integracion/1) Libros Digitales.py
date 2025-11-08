import unittest
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime

# URL base y rutas de la aplicación
BASE_URL   = "http://127.0.0.1:8000"
LOGIN_URL  = f"{BASE_URL}/user/loginUser"
LIBROS_URL = f"{BASE_URL}/admin/gestion/libros/digitales"

# Credenciales de inicio de sesión
EMAIL = "martelldennis259@gmail.com"
PASSWORD = "682725"

class TestIntegracionLibrosDigitales(unittest.TestCase):
    resultados = []  # Almacena los resultados de las pruebas
    session = None   # Sesión para las peticiones HTTP

    # Variables para los libros
    codigo_inicial = f"LDINT{int(time.time())}"
    titulo_inicial = "Libro INT Creación"
    codigo_editado = None
    titulo_editado = "Libro INT Editado"
    libro_id = None

    @classmethod
    def setUpClass(cls):
        """Configura la sesión y realiza login antes de ejecutar las pruebas."""
        cls.session = requests.Session()
        token = cls._get_csrf_token(LOGIN_URL)  # Obtiene el token CSRF
        assert token, "No se obtuvo token CSRF"  # Verifica que se haya obtenido el token CSRF

        # Realiza el login
        r = cls.session.post(LOGIN_URL, data={
            "_token": token,
            "email": EMAIL,
            "password": PASSWORD
        }, allow_redirects=True)
        
        if r.status_code == 302:  # Redirección tras login exitoso
            cls.session.get(r.headers.get("Location", f"{BASE_URL}/admin"))  # Redirige al panel de administración
        assert r.status_code in (200, 302), "Fallo en inicio de sesión"  # Verifica que el login fue exitoso

    @classmethod
    def _get_csrf_token(cls, url):
        """Obtiene el token CSRF necesario para realizar operaciones seguras."""
        r = cls.session.get(url)  # Realiza una petición GET
        soup = BeautifulSoup(r.text, "html.parser")  # Parseo del HTML de la página
        tag = soup.find("input", {"name": "_token"})  # Busca el token CSRF
        return tag["value"] if tag else None  # Devuelve el token o None si no lo encuentra

    @classmethod
    def _get_libro_id_por_codigo(cls, codigo):
        """Obtiene el ID del libro a partir de su código."""
        r = cls.session.get(LIBROS_URL)
        soup = BeautifulSoup(r.text, "html.parser")
        for tr in soup.find_all("tr"):
            if codigo in tr.text:
                btn = tr.find("button", {"class": "btn-edit"})
                if btn and btn.has_attr("data-id"):
                    return btn["data-id"]
        return None  # Devuelve None si no encuentra el libro con ese código

    def test_01_crear_y_listar_y_buscar(self):
        """Crea un libro y verifica que aparezca correctamente en el sistema."""
        token = self._get_csrf_token(LIBROS_URL)
        data = {
            "_token": token,
            "titulo": self.titulo_inicial,
            "codigo": self.codigo_inicial,
            "autor": "Autor Integración",
            "categoria_id": 1,
            "permiso_acceso": "publico",
            "estado": "habilitado",
            "portada_url": "https://ejemplo.com/portada.jpg",
            "archivo_url": "https://ejemplo.com/libro.pdf",
        }

        # Crea el libro
        r_create = self.session.post(LIBROS_URL, data=data, allow_redirects=True)
        ok_create = r_create.status_code in (200, 302)  # Verifica que la creación fue exitosa

        # Verifica que el libro esté en la lista
        r_list = self.session.get(LIBROS_URL)
        en_lista = (self.codigo_inicial in r_list.text) and (self.titulo_inicial in r_list.text)

        # Verifica que el libro aparezca en los resultados de búsqueda
        r_search = self.session.get(f"{LIBROS_URL}?search=INT")
        en_busqueda = self.codigo_inicial in r_search.text

        # Almacena el resultado de la prueba
        estado = "Correcto" if (ok_create and en_lista and en_busqueda) else "Incorrecto"
        obtenido = f"HTTP={r_create.status_code}, Código='{self.codigo_inicial}', En lista={en_lista}, En búsqueda={en_busqueda}"
        self.resultados.append({
            "nombre": "Creación y verificación del libro",
            "esperado": "El sistema debe permitir registrar un nuevo libro y mostrarlo en el listado y en los resultados de búsqueda.",
            "obtenido": obtenido,
            "estado": estado
        })

        self.assertTrue(ok_create)  # Verifica que la creación fue exitosa
        self.assertTrue(en_lista)  # Verifica que el libro esté en la lista
        self.assertTrue(en_busqueda)  # Verifica que el libro aparezca en la búsqueda

        # Obtiene el ID del libro recién creado
        self.__class__.libro_id = self._get_libro_id_por_codigo(self.codigo_inicial)
        self.assertIsNotNone(self.libro_id, "No se pudo obtener el ID del libro recién creado.")

    def test_02_editar_y_verificar(self):
        """Edita el libro y verifica que los cambios se reflejen correctamente."""
        self.assertIsNotNone(self.libro_id, "Falta libro_id de la prueba anterior.")  # Verifica que el ID del libro esté disponible

        token = self._get_csrf_token(LIBROS_URL)
        self.__class__.codigo_editado = f"{self.codigo_inicial}-ED{datetime.now().strftime('%H%M%S')}"  # Genera un código único para la edición

        data = {
            "_token": token,
            "titulo": self.titulo_editado,
            "codigo": self.codigo_editado,
            "autor": "Autor Editado",
            "categoria_id": 1,
            "permiso_acceso": "privado",
            "estado": "deshabilitado",
            "portada_url": "https://ejemplo.com/portada.jpg",
            "archivo_url": "https://ejemplo.com/libro.pdf",
        }

        # Edita el libro
        r_put = self.session.put(f"{LIBROS_URL}/{self.libro_id}", data=data, files={}, allow_redirects=True)
        ok_put = r_put.status_code in (200, 302)

        # Verifica que los cambios se reflejen en el listado
        r_check = self.session.get(LIBROS_URL)
        actualizado = (self.titulo_editado.lower() in r_check.text.lower()) and (self.codigo_editado in r_check.text)

        # Almacena el resultado de la prueba
        estado = "Correcto" if (ok_put and actualizado) else "Incorrecto"
        obtenido = f"HTTP={r_put.status_code}, Nuevo título='{self.titulo_editado}', Actualizado={actualizado}"
        self.resultados.append({
            "nombre": "Edición del libro y confirmación de cambios",
            "esperado": "El libro debe poder editarse y sus nuevos datos deben verse reflejados en el panel de gestión.",
            "obtenido": obtenido,
            "estado": estado
        })

        self.assertTrue(ok_put)  # Verifica que la edición fue exitosa
        self.assertTrue(actualizado)  # Verifica que los cambios estén reflejados

    def test_03_eliminar_y_confirmar_ausencia(self):
        """Elimina el libro y confirma que ya no aparezca en el sistema."""
        self.assertIsNotNone(self.libro_id, "Falta libro_id de pruebas previas.")  # Verifica que el ID del libro esté disponible

        token = self._get_csrf_token(LIBROS_URL)
        r_del = self.session.post(
            f"{LIBROS_URL}/{self.libro_id}",
            data={"_token": token, "_method": "DELETE"},
            allow_redirects=True
        )
        ok_del = r_del.status_code in (200, 302)

        # Verifica que el libro haya sido eliminado
        r_after = self.session.get(LIBROS_URL)
        ya_no_esta = (self.codigo_editado not in r_after.text) and (self.titulo_editado not in r_after.text)

        # Almacena el resultado de la prueba
        estado = "Correcto" if (ok_del and ya_no_esta) else "Incorrecto"
        obtenido = f"HTTP={r_del.status_code}, Eliminado={ya_no_esta}"
        self.resultados.append({
            "nombre": "Eliminación del libro y comprobación final",
            "esperado": "El sistema debe eliminar el libro de forma permanente y no mostrarlo en el listado tras la acción.",
            "obtenido": obtenido,
            "estado": estado
        })

        self.assertTrue(ok_del)  # Verifica que la eliminación fue exitosa
        self.assertTrue(ya_no_esta)  # Verifica que el libro ya no esté en el sistema

    @classmethod
    def tearDownClass(cls):
        """Imprime el resumen final de todas las pruebas."""
        time.sleep(0.4)  # Pausa para asegurar que los resultados se registren
        print("\n========== REPORTE FINAL: PRUEBAS DE INTEGRACIÓN (Libros Digitales) ==========")
        for r in cls.resultados:
            print(f"\nCaso: {r['nombre']}")
            print(f"Resultado esperado: {r['esperado']}")
            print(f"Resultado obtenido: {r['obtenido']}")
            print(f"Estado final: {r['estado']}")

if __name__ == "__main__":
    unittest.main(verbosity=0)  # Ejecuta las pruebas sin mostrar detalles adicionales
