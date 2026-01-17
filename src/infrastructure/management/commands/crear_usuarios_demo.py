"""
Management command para crear usuarios de demostración

Uso:
    python manage.py crear_usuarios_demo
"""
from django.core.management.base import BaseCommand
from infrastructure.auth.models import Usuario, RolUsuario


class Command(BaseCommand):
    help = 'Crea usuarios de demostración con diferentes roles'

    def handle(self, *args, **options):
        self.stdout.write('Creando usuarios de demostración...\n')
        
        usuarios = [
            {
                'email': 'admin@ecommerce.com',
                'password': 'Admin123!',
                'nombre': 'Administrador Sistema',
                'rol': RolUsuario.ADMIN,
                'is_staff': True,
            },
            {
                'email': 'operador@ecommerce.com',
                'password': 'Operador123!',
                'nombre': 'Operador de Ventas',
                'rol': RolUsuario.OPERADOR,
                'is_staff': False,
            },
            {
                'email': 'lectura@ecommerce.com',
                'password': 'Lectura123!',
                'nombre': 'Usuario Solo Lectura',
                'rol': RolUsuario.LECTURA,
                'is_staff': False,
            },
        ]
        
        creados = 0
        existentes = 0
        
        for datos in usuarios:
            email = datos['email']
            
            if Usuario.objects.filter(email=email).exists():
                self.stdout.write(
                    self.style.WARNING(f'  ⚠ Usuario {email} ya existe')
                )
                existentes += 1
            else:
                Usuario.objects.create_user(**datos)
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Usuario {email} creado ({datos["rol"]})')
                )
                creados += 1
        
        self.stdout.write('\n' + '='*70)
        self.stdout.write(f'Resumen: {creados} creados, {existentes} ya existían')
        self.stdout.write('='*70 + '\n')
        
        if creados > 0:
            self.stdout.write(self.style.SUCCESS('Usuarios de demostración disponibles:'))
            self.stdout.write('')
            for datos in usuarios:
                self.stdout.write(f"  • {datos['email']} / {datos['password']} ({datos['rol']})")
            self.stdout.write('')
