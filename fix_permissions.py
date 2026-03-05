"""
fix_permissions.py
==================
Run this ONCE to fix all existing admin users.

It will:
  1. Set is_staff=True  (so admin can login to /admin/)
  2. Set is_superuser=False (so admin can't access everything)
  3. Assign correct permissions (so admin sees Contacts + Users sections)

Run with:
    python fix_permissions.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'softcall.settings')
django.setup()

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from soft.models import CustomUser, ContactData

print("=" * 55)
print("Fixing admin users permissions...")
print("=" * 55)

# Get permission objects for ContactData and CustomUser
contact_ct = ContentType.objects.get_for_model(ContactData)
user_ct    = ContentType.objects.get_for_model(CustomUser)

all_perms = Permission.objects.filter(
    content_type__in=[contact_ct, user_ct]
)

print(f"Available permissions: {[p.codename for p in all_perms]}\n")

admins = CustomUser.objects.filter(role='admin')

if not admins.exists():
    print("No admin users found. Create one from superadmin panel first.")
else:
    for admin in admins:
        # Step 1: Set is_staff=True so they can login
        admin.is_staff     = True
        admin.is_superuser = False
        admin.save(update_fields=['is_staff', 'is_superuser'])

        # Step 2: Assign all ContactData + CustomUser permissions
        admin.user_permissions.set(all_perms)

        print(f"  ✅ Fixed: {admin.name} ({admin.email})")
        print(f"     is_staff={admin.is_staff}, is_superuser={admin.is_superuser}")
        print(f"     Permissions: {admin.user_permissions.count()} assigned\n")

print("=" * 55)
print("Done! Admins can now:")
print("  ✔ Login to /admin/")
print("  ✔ See Contacts section (add/edit/delete their contacts)")
print("  ✔ See Users section (add/edit/delete their users)")
print("  ✔ Upload CSV/Excel contacts")
print("=" * 55)
