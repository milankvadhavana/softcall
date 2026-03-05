"""
fix_admin_login.py
==================
Run this ONCE to fix existing admins who have is_staff=False
and therefore cannot login to the Django admin panel.

Place next to manage.py and run:
    python fix_admin_login.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'softcall.settings')
django.setup()

from soft.models import CustomUser

print("=" * 50)
print("Fixing admin users login access...")
print("=" * 50)

admins = CustomUser.objects.filter(role='admin')
fixed  = 0

for admin in admins:
    if not admin.is_staff:
        admin.is_staff     = True   # ✅ Must be True to login to /admin/
        admin.is_superuser = False  # ✅ Must be False to restrict full access
        admin.save(update_fields=['is_staff', 'is_superuser'])
        print(f"  Fixed: {admin.name} ({admin.email})")
        fixed += 1
    else:
        print(f"  OK:    {admin.name} ({admin.email}) — already has access")

print(f"\n✅ Fixed {fixed} admin(s).")
print("Admins can now login to /admin/ panel.")
print("=" * 50)
