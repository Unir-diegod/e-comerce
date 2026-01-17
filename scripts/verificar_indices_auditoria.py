"""
Script de Verificación de Índices de PostgreSQL para Auditoría

Valida que los índices de la tabla de auditoría se crearon correctamente
para garantizar buen rendimiento en consultas forenses.
"""

import os
import sys
import django

# Configurar entorno
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "infrastructure.config.django_settings")
django.setup()

from django.db import connection


def verificar_indices_auditoria():
    print("=" * 70)
    print("VERIFICACIÓN DE ÍNDICES DE AUDITORÍA EN POSTGRESQL")
    print("=" * 70)
    
    with connection.cursor() as cursor:
        # Obtener todos los índices de la tabla de auditoría
        cursor.execute("""
            SELECT
                indexname,
                indexdef
            FROM
                pg_indexes
            WHERE
                tablename = 'auditoria_registros'
            ORDER BY
                indexname;
        """)
        
        indices = cursor.fetchall()
        
        print(f"\n📊 Total de índices encontrados: {len(indices)}\n")
        
        for idx_name, idx_def in indices:
            print(f"✅ {idx_name}")
            print(f"   {idx_def}\n")
        
        # Verificar que existen los índices críticos
        indices_names = [idx[0] for idx in indices]
        
        print("\n" + "=" * 70)
        print("VERIFICACIÓN DE ÍNDICES CRÍTICOS")
        print("=" * 70)
        
        indices_criticos = {
            'timestamp': False,
            'entidad_tipo': False,
            'entidad_id': False,
            'accion': False,
        }
        
        for idx_name in indices_names:
            for campo in indices_criticos:
                if campo in idx_name:
                    indices_criticos[campo] = True
        
        for campo, existe in indices_criticos.items():
            estado = "✅" if existe else "❌"
            print(f"{estado} Índice en '{campo}': {'PRESENTE' if existe else 'AUSENTE'}")
        
        # Verificar estadísticas de la tabla
        cursor.execute("""
            SELECT
                COUNT(*) as total_registros,
                COUNT(DISTINCT entidad_tipo) as tipos_entidad,
                COUNT(DISTINCT accion) as tipos_accion,
                MIN(timestamp) as primer_registro,
                MAX(timestamp) as ultimo_registro
            FROM
                auditoria_registros;
        """)
        
        stats = cursor.fetchone()
        
        print("\n" + "=" * 70)
        print("ESTADÍSTICAS DE LA TABLA")
        print("=" * 70)
        print(f"📊 Total de registros: {stats[0]}")
        print(f"📊 Tipos de entidad diferentes: {stats[1]}")
        print(f"📊 Tipos de acción diferentes: {stats[2]}")
        if stats[3]:
            print(f"📅 Primer registro: {stats[3]}")
            print(f"📅 Último registro: {stats[4]}")
        
        print("\n" + "=" * 70)
        print("✅ VERIFICACIÓN COMPLETADA")
        print("=" * 70)


if __name__ == "__main__":
    try:
        verificar_indices_auditoria()
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
