# path/to/your/app/admin.py
from django.contrib import admin

class CustomAdminSite(admin.AdminSite):
    site_header = "My Custom Admin"  # Ganti dengan judul yang diinginkan
    site_title = "My Admin Portal"    # Ganti dengan judul yang diinginkan
    index_title = "Welcome to My Admin"  # Ganti dengan judul yang diinginkan

# Daftarkan admin kustom
admin_site = CustomAdminSite(name='custom_admin')

# Register your models here