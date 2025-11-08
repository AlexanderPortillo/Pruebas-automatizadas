import unittest
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# URLs de la aplicación para las pruebas
BASE_URL   = "http://127.0.0.1:8000"  # URL base de la aplicación
LOGIN_URL  = f"{BASE_URL}/user/loginUser"  # URL para iniciar sesión
AUDIO_URL  = f"{BASE_URL}/admin/gestion/libros/audiolibros"  # URL para gestionar audiolibros

# Credenciales para el login
EMAIL    = "martelldennis259@gmail.com"
PASSWORD = "682725"

class TestUsabilidadAudiolibros(unittest.TestCase):
    resultados = []  # Lista que almacena los resultados de las pruebas
    session = None   # Sesión para las peticiones HTTP
    auth_ok = False  # Estado de autenticación

    @classmethod
    def setUpClass(cls):
        """Inicia sesión antes de ejecutar las pruebas."""
        cls.session = requests.Session()  # Crea una nueva sesión HTTP
        # Obtiene el token CSRF necesario para realizar peticiones POST seguras
        token = cls._csrf(LOGIN_URL, cls.session)
        
        if not token:
            cls._log("Inicio de sesión",
                     "Poder autenticar para evaluar la interfaz",
                     "Login y obtención de CSRF correctos",
                     "No se obtuvo token CSRF",
                     "Fallido")
            return

        # Realiza el POST para iniciar sesión
        r = cls.session.post(LOGIN_URL, data={
            "_token": token, "email": EMAIL, "password": PASSWORD
        }, allow_redirects=True)

        # Si la respuesta es una redirección, se redirige al panel de administración
        if r.status_code == 302:
            cls.session.get(r.headers.get("Location", f"{BASE_URL}/admin"))
        
        # Verifica que la autenticación fue exitosa
        cls.auth_ok = r.status_code in (200, 302)

    # ----------------- Helpers -----------------
    @staticmethod
    def _csrf(url, session):
        """Obtiene el token CSRF necesario para enviar formularios."""
        try:
            r = session.get(url)  # Solicita la página de login
            soup = BeautifulSoup(r.text, "html.parser")  # Parseo del HTML de la página
            tag = soup.find("input", {"name": "_token"})  # Busca el token CSRF
            return tag["value"] if tag else None  # Devuelve el token o None si no lo encuentra
        except Exception:
            return None  # Si hay un error, devuelve None

    @classmethod
    def _log(cls, nombre, objetivo, esperado, obtenido, estado):
        """Registra el resultado de cada caso de prueba."""
        cls.resultados.append({
            "nombre": nombre,
            "objetivo": objetivo,
            "esperado": esperado,
            "obtenido": obtenido,
            "estado": estado
        })

    # ============ CASOS DE USABILIDAD ============

    def test_01_textos_claros_y_jerarquia(self):
        """Verifica que los textos sean claros, con jerarquía y fácil navegación."""
        # Si no está autenticado, registra el fallo y termina la prueba
        if not self.auth_ok:
            self._log("Textos y jerarquía", "Verificar textos visibles",
                      "Acceso al módulo para leer encabezados",
                      "Fallo de autenticación", "Fallido")
            return

        # Accede a la página de audiolibros
        r = self.session.get(AUDIO_URL)
        soup = BeautifulSoup(r.text, "html.parser")

        # Verifica que los encabezados y subtítulos estén presentes
        h1 = soup.find(["h1", "h2"], string=lambda t: t and "audiolibros" in t.lower())
        subtitulo = soup.find(["p", "div"], class_=lambda c: c and "subtitle" in c.lower()) or \
                    soup.find(["p", "small"], string=True)

        # Verifica que los botones principales estén presentes y sean comprensibles
        btn_nuevo = soup.find(["a", "button"], string=lambda t: t and ("nuevo" in t.lower() or "publicar" in t.lower()))
        btn_filtros = soup.find(["a", "button"], string=lambda t: t and ("habilitado" in t.lower() or "deshabilitado" in t.lower()))

        faltantes = []
        if not h1:         faltantes.append("encabezado principal")
        if not subtitulo:  faltantes.append("subtítulo/ayuda")
        if not btn_nuevo:  faltantes.append("botón de alta (Nuevo/Publicar)")
        if not btn_filtros: faltantes.append("filtros rápidos (Habilitado/Deshabilitado)")

        # Si faltan elementos, el estado será "Incompleto"
        estado = "Correcto" if not faltantes else "Incompleto"
        obtenido = "Estructura clara" if not faltantes else f"Faltan: {', '.join(faltantes)}"
        self._log("Textos y jerarquía visual",
                  "Asegurar que el usuario entienda la pantalla rápidamente",
                  "Encabezado claro, subtítulo de apoyo y acciones principales visibles",
                  obtenido, estado)

        self.assertTrue(h1)  # Verifica que el encabezado esté presente
        self.assertTrue(btn_nuevo)  # Verifica que el botón de nuevo/audición esté presente

    def test_02_formulario_accesible_y_guiado(self):
        """Revisa que el formulario tenga etiquetas, campos obligatorios y mensajes de error/ayuda."""
        # Si no está autenticado, registra el fallo y termina la prueba
        if not self.auth_ok:
            self._log("Formulario accesible", "Evaluar campos y etiquetas",
                      "Formulario accesible", "Fallo de autenticación", "Fallido")
            return

        r = self.session.get(AUDIO_URL)
        soup = BeautifulSoup(r.text, "html.parser")

        # Secciones de creación/edición de audiolibros
        campos_clave = ["titulo", "codigo", "autor", "narrador", "duracion", "categoria_id", "estado", "portada_url", "audio_url"]
        labels_ok, required_ok = True, True
        faltantes = []

        for name in campos_clave:
            inp = soup.find(["input", "select", "textarea"], {"name": name})
            if not inp:
                faltantes.append(f"campo:{name}")
                continue
            # Verifica que el campo tenga una etiqueta asociada
            label = None
            if inp.has_attr("id"):
                label = soup.find("label", {"for": inp["id"]})
            if label is None:
                # Si no tiene un label asociado, busca el label cercano
                label = inp.find_parent().find("label") if inp.find_parent() else None
            if not label:
                labels_ok = False

            # Verifica que los campos obligatorios estén marcados
            if name in ("titulo", "codigo", "autor", "narrador", "duracion", "categoria_id", "estado"):
                if not inp.has_attr("required"):
                    required_ok = False

        # Verifica si hay mensajes de error o ayuda
        feedback = soup.find(class_=lambda c: c and ("alert-danger" in c or "invalid-feedback" in c))

        estado = "Correcto" if labels_ok and required_ok else "Incompleto"
        obtenido = f"Etiquetas={'ok' if labels_ok else 'faltan'} | Requeridos={'ok' if required_ok else 'faltan'}"
        if faltantes:
            obtenido += f" | No encontrados: {', '.join(faltantes)}"
        if feedback:
            obtenido += " | Soporte de mensajes: sí"

        self._log("Formulario accesible y guiado",
                  "Facilitar el llenado correcto y minimizar errores",
                  "Campos con etiqueta asociada, obligatorios marcados y mensajes de ayuda/error",
                  obtenido, estado)

        self.assertTrue(labels_ok)  # Verifica que todas las etiquetas estén presentes
        self.assertTrue(required_ok)  # Verifica que todos los campos obligatorios estén marcados

    def test_03_tabla_legible_y_controles(self):
        """Verifica que el listado sea entendible: encabezados, búsqueda, estado y paginación."""
        # Si no está autenticado, registra el fallo y termina la prueba
        if not self.auth_ok:
            self._log("Lista legible y controles",
                      "Validar lectura del catálogo",
                      "Listado accesible y con controles",
                      "Fallo de autenticación", "Fallido")
            return

        r = self.session.get(AUDIO_URL)
        soup = BeautifulSoup(r.text, "html.parser")

        tabla = soup.find("table")  # Verifica que haya una tabla
        ths = tabla.find_all("th") if tabla else []
        headers_ok = any("audiolibro" in th.get_text(strip=True).lower() for th in ths) and \
                     any("autor" in th.get_text(strip=True).lower() for th in ths) and \
                     any("estado" in th.get_text(strip=True).lower() for th in ths)

        # Verifica que haya un campo de búsqueda
        buscador = soup.find("input", {"name": "search"}) or \
                   soup.find("input", {"id": "buscarAudiolibro"}) or \
                   soup.find("input", {"placeholder": lambda t: t and "buscar" in t.lower()})

        # Verifica que haya un indicador visual de estado
        badge_estado = soup.find(class_=lambda c: c and ("status-badge" in c or "badge" in c))

        # Verifica que haya paginación
        paginacion = soup.find("nav", class_=lambda c: c and "pagination" in c.lower()) or \
                     soup.find("ul", class_=lambda c: c and "pagination" in c.lower())

        faltantes = []
        if not tabla:         faltantes.append("tabla de resultados")
        if tabla and not headers_ok: faltantes.append("encabezados informativos")
        if not buscador:      faltantes.append("campo de búsqueda")
        if not badge_estado:  faltantes.append("indicador visual de estado")
        if not paginacion:    faltantes.append("paginación")

        estado = "Correcto" if not faltantes else "Incompleto"
        obtenido = "Listado claro" if not faltantes else f"Faltan: {', '.join(faltantes)}"

        self._log("Lista legible y controles",
                  "Facilitar encontrar y distinguir registros",
                  "Tabla con encabezados claros, buscador, estados visibles y paginación",
                  obtenido, estado)

        self.assertTrue(tabla is not None)  # Verifica que la tabla esté presente
        self.assertTrue(buscador is not None)  # Verifica que el campo de búsqueda esté presente

    @classmethod
    def tearDownClass(cls):
        """Imprime el reporte final de todas las pruebas de usabilidad."""
        print("\n========== RESUMEN FINAL: PRUEBAS DE USABILIDAD (Audiolibros) ==========")
        for r in cls.resultados:
            print(f"\n{r['estado']} | {r['nombre']}")
            print(f"  Objetivo : {r['objetivo']}")
            print(f"  Esperado : {r['esperado']}")
            print(f"  Obtenido : {r['obtenido']}")

if __name__ == "__main__":
    unittest.main(verbosity=0)  # Ejecuta las pruebas
