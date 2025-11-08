import unittest
import requests
from bs4 import BeautifulSoup
import time

BASE_URL = "https://biblioteca-cubo.com"  # URL base de la aplicación
LOGIN_URL = f"{BASE_URL}/user/loginUser"  # URL para iniciar sesión
CATALOGO_URL = f"{BASE_URL}/libros"  # URL para acceder al catálogo de libros
AUDIOBOOK_URL = f"{BASE_URL}/libros/DQM0001/listen"  # URL para escuchar el audiolibro

EMAIL = "admin@cubo.com"  # Correo del usuario administrador
PASSWORD = "admin2025"  # Contraseña del usuario administrador

class TestAudiolibroEscuchar(unittest.TestCase):
    resultados = []  # Almacena los resultados de cada prueba

    def setUp(self):
        """Crea sesión persistente y realiza login"""
        self.session = requests.Session()  # Crea una nueva sesión de requests
        self.token = self.get_csrf_token(LOGIN_URL)  # Obtiene el token CSRF para la autenticación
        self.assertIsNotNone(self.token, "No se obtuvo el token CSRF.")  # Asegura que el token se obtuvo correctamente
        self.login()  # Realiza el login con las credenciales

    def get_csrf_token(self, url):
        """Obtiene el token CSRF necesario para realizar operaciones seguras"""
        r = self.session.get(url)  # Solicita la página de login
        soup = BeautifulSoup(r.text, "html.parser")  # Parseo de la respuesta HTML
        tag = soup.find("input", {"name": "_token"})  # Busca el token CSRF en el formulario
        return tag["value"] if tag else None  # Devuelve el valor del token o None si no se encuentra

    def login(self):
        """Inicia sesión con las credenciales del usuario"""
        data = {"_token": self.token, "email": EMAIL, "password": PASSWORD}  # Datos de login
        r = self.session.post(LOGIN_URL, data=data, allow_redirects=True)  # Realiza el POST para hacer login
        if r.status_code == 302:  # Si la respuesta es una redirección, significa que el login fue exitoso
            self.session.get(r.headers.get("Location", f"{BASE_URL}/libros"))  # Redirige a la página de libros
        self.assertIn(r.status_code, [200, 302], "Fallo en el inicio de sesión.")  # Verifica que el login fue exitoso

    # ----------------------------------------------------------------
    def test_1_acceso_pagina_escucha(self):
        """Verifica acceso al reproductor del audiolibro"""
        r = self.session.get(AUDIOBOOK_URL)  # Accede a la página del audiolibro
        soup = BeautifulSoup(r.text, "html.parser")  # Parseo del HTML de la página
        titulo = soup.find("h2") or soup.find("div", {"class": "audiobook-title"})  # Busca el título del audiolibro
        titulo_texto = titulo.text.strip() if titulo else "No encontrado"  # Extrae el texto del título o indica que no se encontró

        # Verifica que el acceso haya sido correcto y que el título se haya encontrado
        estado = "Correcto" if (r.status_code == 200 and titulo_texto != "No encontrado") else "Incorrecto"
        self.resultados.append({
            "nombre": "Acceso a la página de reproducción",
            "esperado": "Cargar el título del audiolibro correctamente (HTTP 200)",
            "obtenido": f"HTTP {r.status_code} | Título: {titulo_texto}",
            "estado": estado
        })

        self.assertEqual(r.status_code, 200)  # Verifica que el código de respuesta sea 200 (OK)
        self.assertNotEqual(titulo_texto, "No encontrado")  # Verifica que se haya encontrado el título del audiolibro

    # ----------------------------------------------------------------
    def test_2_elementos_reproductor(self):
        """Verifica que todos los elementos del reproductor estén presentes"""
        r = self.session.get(AUDIOBOOK_URL)  # Accede a la página del audiolibro
        soup = BeautifulSoup(r.text, "html.parser")  # Parseo del HTML de la página
        elementos = {
            "play/pause": soup.find("button", {"id": "playPause"}),  # Busca el botón de play/pause
            "retroceder": soup.find("button", {"id": "back10"}),  # Busca el botón de retroceder
            "adelantar": soup.find("button", {"id": "forward10"}),  # Busca el botón de adelantar
            "onda de audio": soup.find("div", {"id": "waveform"})  # Busca el contenedor de la onda de audio
        }

        faltantes = [k for k, v in elementos.items() if v is None]  # Lista los elementos faltantes
        estado = "Correcto" if not faltantes else "Incompleto"  # Si no hay elementos faltantes, el estado es correcto
        obtenido = "Todos presentes" if not faltantes else f"Faltan: {', '.join(faltantes)}"  # Indica qué elementos faltan

        self.resultados.append({
            "nombre": "Verificación de componentes del reproductor",
            "esperado": "Todos los elementos deben estar presentes",
            "obtenido": obtenido,
            "estado": estado
        })

        self.assertFalse(faltantes)  # Asegura que no falten elementos en el reproductor

    def test_3_redireccion_desde_catalogo(self):
        """Verifica que el enlace 'Escuchar' redirija correctamente al reproductor del audiolibro"""
        r = self.session.get(f"{BASE_URL}/libros")  # Accede a la página del catálogo de libros
        soup = BeautifulSoup(r.text, "html.parser")  # Parseo del HTML de la página
        boton_escuchar = soup.find("a", {"class": "btn-listen"})  # Busca el botón de "Escuchar"
        self.assertIsNotNone(boton_escuchar, "No se encontró el botón 'Escuchar'.")  # Verifica que el botón exista
        link = boton_escuchar["href"]  # Extrae el enlace del botón
        r2 = self.session.get(link)  # Realiza una nueva solicitud GET al enlace del reproductor

        estado = "Correcto" if r2.status_code == 200 else "Incorrecto"  # Verifica que la redirección fue exitosa
        self.resultados.append({
            "nombre": "Redirección desde catálogo al reproductor",
            "esperado": "El enlace 'Escuchar' debe llevar correctamente al audiolibro",
            "obtenido": f"HTTP {r2.status_code} → {link}",
            "estado": estado
        })

        self.assertEqual(r2.status_code, 200)  # Verifica que la redirección al reproductor sea exitosa

    @classmethod
    def tearDownClass(cls):
        """Imprime el resumen final de todas las pruebas"""
        time.sleep(0.5)  # Pausa breve para asegurar que todos los resultados se registren
        print("\n========== RESUMEN FINAL DE PRUEBAS UNITARIAS ==========")
        for r in cls.resultados:
            print(f"{r['estado']} | {r['nombre']}")
            print(f"  Esperado: {r['esperado']}")
            print(f"  Obtenido: {r['obtenido']}")
            print("--------------------------------------------------------")
        print("========================================================\n")

if __name__ == "__main__":
    unittest.main(verbosity=0)  # Ejecuta las pruebas sin mostrar detalles adicionales
