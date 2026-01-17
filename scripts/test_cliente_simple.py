import os
import sys
import django
import json

sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "infrastructure.config.django_settings")
os.environ['DJANGO_ALLOWED_HOSTS'] = 'localhost,127.0.0.1,testserver'
os.environ['DJANGO_SECRET_KEY'] = 'provisional-key-for-testing-purposes-only-must-be-very-long-to-pass-validation-checks-789012'
os.environ['DJANGO_ENVIRONMENT'] = 'development'
django.setup()

from rest_framework.test import APIClient

client = APIClient()

data_cliente = {
    "nombre": "Test",
    "apellido": "User",
    "email": "test@example.com",
    "tipo_documento": "DNI",
    "numero_documento": "12345678",
    "telefono": "555-0000"
}

resp = client.post("/api/v1/clientes", data_cliente, format='json')
print(f"Status Code: {resp.status_code}")
if hasattr(resp, 'data'):
    print(f"Response Data: {json.dumps(resp.data, indent=2, default=str)}")
else:
    print(f"Response Content: {resp.content.decode()[:500]}")
