"""
Comando de gestión Django para verificar configuración de base de datos

Ejecutar: python manage.py check_database
"""
from django.core.management.base import BaseCommand
from django.db import connection
from infrastructure.config.database_config import DatabaseConfig


class Command(BaseCommand):
    help = 'Verifica la configuración y conectividad de la base de datos'

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("VERIFICACIÓN DE CONFIGURACIÓN DE BASE DE DATOS"))
        self.stdout.write("=" * 80)
        self.stdout.write("")

        # Mostrar configuración (sin passwords)
        self.stdout.write("📋 Configuración actual:")
        self.stdout.write("-" * 80)
        
        info = DatabaseConfig.get_info()
        for key, value in info.items():
            self.stdout.write(f"   {key.upper()}: {value}")
        
        self.stdout.write("")

        # Probar conexión
        self.stdout.write("🔌 Probando conexión con la base de datos...")
        self.stdout.write("-" * 80)
        
        try:
            # Intentar conectar
            connection.ensure_connection()
            
            # Obtener información del servidor
            with connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
            
            self.stdout.write(self.style.SUCCESS("✅ Conexión exitosa"))
            self.stdout.write(f"   Versión PostgreSQL: {version}")
            
            # Verificar tablas
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name;
                """)
                tables = cursor.fetchall()
            
            self.stdout.write("")
            self.stdout.write(f"📊 Tablas en la base de datos: {len(tables)}")
            if tables:
                for table in tables:
                    self.stdout.write(f"   - {table[0]}")
            else:
                self.stdout.write(self.style.WARNING("   ⚠️  No hay tablas. Ejecutar: python manage.py migrate"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR("❌ Error al conectar con la base de datos"))
            self.stdout.write(f"   Error: {str(e)}")
            self.stdout.write("")
            self.stdout.write(self.style.WARNING("Sugerencias:"))
            self.stdout.write("   1. Verificar que PostgreSQL esté corriendo")
            self.stdout.write("   2. Verificar variables de entorno en .env")
            self.stdout.write("   3. Verificar credenciales de acceso")
            self.stdout.write("   4. Verificar que la base de datos existe")
            return

        self.stdout.write("")
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("✅ VERIFICACIÓN COMPLETADA"))
        self.stdout.write("=" * 80)
