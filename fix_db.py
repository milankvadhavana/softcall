"""
fix_db.py  — Run ONCE to fix the IntegrityError
Place this file next to manage.py and run:  python fix_db.py
"""
import os, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'softcall.settings')
django.setup()

from django.db import connection

print("=" * 50)
print("Checking soft_customuser table columns...")
print("=" * 50)

with connection.cursor() as cursor:
    cursor.execute("PRAGMA table_info(soft_customuser)")
    cols = [row[1] for row in cursor.fetchall()]
    print(f"Existing columns: {cols}\n")

    if 'updated_at' not in cols:
        print("Adding updated_at ...")
        cursor.execute("""
            ALTER TABLE soft_customuser
            ADD COLUMN updated_at DATETIME NOT NULL
            DEFAULT (STRFTIME('%Y-%m-%dT%H:%M:%f', 'NOW'))
        """)
        print("updated_at added")
    else:
        print("updated_at already exists")

    if 'created_at' not in cols:
        print("Adding created_at ...")
        cursor.execute("""
            ALTER TABLE soft_customuser
            ADD COLUMN created_at DATETIME NOT NULL
            DEFAULT (STRFTIME('%Y-%m-%dT%H:%M:%f', 'NOW'))
        """)
        print("created_at added")
    else:
        print("created_at already exists")

print("Done! Now run: python manage.py makemigrations soft && python manage.py migrate")
