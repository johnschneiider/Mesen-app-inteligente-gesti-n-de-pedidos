#!/usr/bin/env python3
"""
setup.py — Script de configuración inicial de Mesenú
Uso: python setup.py
"""
import os
import sys
import subprocess


def run(cmd, check=True):
    print(f"\n>>> {cmd}")
    result = subprocess.run(cmd, shell=True, check=check)
    return result.returncode == 0


def main():
    print("=" * 60)
    print("   Mesenú — Setup inicial")
    print("=" * 60)

    # Entorno virtual
    if not os.path.exists("venv"):
        print("\n[1/6] Creando entorno virtual…")
        run(f"{sys.executable} -m venv venv")
    else:
        print("\n[1/6] Entorno virtual ya existe, omitiendo…")

    # Pip install
    pip = "venv\\Scripts\\pip" if sys.platform == "win32" else "venv/bin/pip"
    print("\n[2/6] Instalando dependencias…")
    run(f"{pip} install --upgrade pip")
    run(f"{pip} install -r requirements.txt")

    # .env
    if not os.path.exists(".env"):
        print("\n[3/6] Copiando .env de ejemplo…")
        import shutil
        shutil.copy(".env.example", ".env")
        print("  IMPORTANTE: edita .env y configura SECRET_KEY antes de producción")
    else:
        print("\n[3/6] .env ya existe, omitiendo…")

    # Manage py
    manage = "venv\\Scripts\\python manage.py" if sys.platform == "win32" else "venv/bin/python manage.py"

    print("\n[4/6] Ejecutando migraciones…")
    run(f"{manage} makemigrations")
    run(f"{manage} migrate")

    print("\n[5/6] Creando superadmin (3001234567 / admin1234)…")
    create_super = (
        f'{manage} shell -c "'
        "from apps.accounts.models import User; "
        "u = User.objects.filter(phone=\\'3001234567\\').first(); "
        "u = u or User(phone=\\'3001234567\\', full_name=\\'Superadmin Mesenú\\', role=\\'superadmin\\', is_staff=True, is_superuser=True); "
        "u.set_password(\\'admin1234\\'); u.save(); print(\\'Superadmin listo\\')"
        '"'
    )
    run(create_super, check=False)

    print("\n[6/6] ¡Listo! Inicia el servidor con:")
    python = "venv\\Scripts\\python" if sys.platform == "win32" else "venv/bin/python"
    print(f"\n   {python} manage.py runserver\n")
    print("   Superadmin: http://127.0.0.1:8000/superadmin/")
    print("   Tienda demo: http://127.0.0.1:8000/tienda/el-sol/")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
