import unittest
from app import app


class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6InBlcGVAZ21haWwuY29tIiwiZXhwIjoxNzM0MDA1MzMzfQ.2ZBqIlpPNa0dRp_FUfy3MSrI2eFrwt9qrrwx3gGMlH8"

    def mostrar_respuesta(self, response):
        print("\nEstado:", response.status_code)
        print("Respuesta:", response.get_json())

    # Vehículos
    def test_obtener_vehiculos(self):
        response = self.app.get('/vehiculos')
        self.mostrar_respuesta(response)
        self.assertEqual(response.status_code, 200)
        self.assertIn('data', response.get_json())

    def test_obtener_vehiculo_existente(self):
        response = self.app.get('/vehiculos/3456MNO')
        self.mostrar_respuesta(response)
        self.assertEqual(response.status_code, 200)
        self.assertIn('data', response.get_json())

    def test_obtener_vehiculo_no_existente(self):
        response = self.app.get('/vehiculos/12345ABC')
        self.mostrar_respuesta(response)
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.get_json())

    def test_eliminar_vehiculo_no_existente(self):
        response = self.app.delete('/vehiculos/1234ABM', headers={"Authorization": self.token})
        self.mostrar_respuesta(response)
        if response.status_code == 200:
            self.assertIn('mensaje', response.get_json())
        elif response.status_code == 404:
            self.mostrar_respuesta(response)
            self.assertIn('error', response.get_json())

    # Usuarios
    def test_login_usuario_no_existente(self):
        data = {"email": "prueba@test.com", "contrasena": "password123"}
        response = self.app.post('/login', json=data)
        self.mostrar_respuesta(response)
        if response.status_code == 200:
            self.assertIn('token', response.get_json())
        elif response.status_code == 401:
            self.assertIn('error', response.get_json())

    def test_login_usuario(self):
        data = {"email": "pepe@gmail.com", "contrasena": "Pepe1234."}
        response = self.app.post('/login', json=data)
        self.mostrar_respuesta(response)
        if response.status_code == 200:
            self.assertIn('token', response.get_json())
        elif response.status_code == 401:
            self.assertIn('error', response.get_json())

    def test_agregar_usuario_dni_existente(self):
        nuevo_usuario = {
            "dni": "12345678A",
            "nombre": "Pepe",
            "email": "pepe@test.com",
            "telefono": "123456789",
            "contrasena": "password123"
        }
        response = self.app.post('/usuarios', json=nuevo_usuario)
        self.mostrar_respuesta(response)
        if response.status_code == 201:
            self.assertIn('mensaje', response.get_json())
        elif response.status_code == 409:
            self.assertIn('error', response.get_json())

    def test_agregar_usuario(self):
        nuevo_usuario = {
            "dni": "12345678C",
            "nombre": "Juan Márquez",
            "email": "juan@test.com",
            "telefono": "123456789",
            "contrasena": "password123"
        }
        response = self.app.post('/usuarios', json=nuevo_usuario)
        self.mostrar_respuesta(response)
        if response.status_code == 201:
            self.assertIn('mensaje', response.get_json())
        elif response.status_code == 409:
            self.assertIn('error', response.get_json())

    # Publicaciones
    def test_obtener_publicaciones(self):
        response = self.app.get('/publicaciones')
        self.mostrar_respuesta(response)
        if response.status_code == 200:
            self.assertIn('data', response.get_json())
        elif response.status_code == 404:
            self.assertIn('mensaje', response.get_json())

    def test_agregar_publicacion(self):
        nueva_publicacion = {
            "matricula_vehiculo": "1234ABC",
            "dni_usuario": "12345678A",
            "fecha": "2024-12-10T00:00:00"
        }
        response = self.app.post('/publicaciones', json=nueva_publicacion, headers={"Authorization": self.token})
        self.mostrar_respuesta(response)
        if response.status_code == 201:
            self.assertIn('mensaje', response.get_json())
        elif response.status_code == 400:
            self.assertIn('error', response.get_json())

    # Favoritos
    def test_agregar_favorito(self):
        nuevo_favorito = {
            "dni_usuario": "12345678A",
            "matricula_vehiculo": "1234ABC"
        }
        response = self.app.post('/favoritos', json=nuevo_favorito, headers={"Authorization": self.token})
        self.mostrar_respuesta(response)
        if response.status_code == 201:
            self.assertIn('mensaje', response.get_json())
        elif response.status_code == 409:
            self.assertIn('error', response.get_json())

    def test_eliminar_favorito(self):
        favorito = {
            "dni_usuario": "12345678A",
            "matricula_vehiculo": "1234ABC"
        }
        response = self.app.delete('/favoritos', json=favorito, headers={"Authorization": self.token})
        self.mostrar_respuesta(response)
        if response.status_code == 200:
            self.assertIn('mensaje', response.get_json())
        elif response.status_code == 404:
            self.assertIn('error', response.get_json())


if __name__ == '__main__':
    unittest.main()
