from django.contrib import admin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.admin import UserAdmin
from django.contrib import admin
from .models import CustomUserModel, WorkerRecord, Project, Site, WorkerSite, Helmet
# Register your models here.
class UserModelCreationForm(UserCreationForm):
    class Meta:
        model = CustomUserModel
        fields = [
            "email",
            "first_name",
            "last_name",
            "department",
            "phone",
            "role",
        ]

class UserModelChangeForm(UserChangeForm):
    class Meta:
        model = CustomUserModel
        fields = [
            "email",
            "first_name",
            "last_name",
            "department",
            "phone",
            "role",
        ]





# class WorkerRecordAdmin(admin.ModelAdmin):
    # list_display = [
        # "user",
        # "timestamp",
        # "temperature",
    # ]
    # search_fields = ("user",)
    # ordering = ("user",)

class WorkerRecordInline(admin.TabularInline):
    model = WorkerRecord
    verbose_name_plural = "Worker Records"
    verbose_name = "Worker Record"
    extra = 0

class WorkerSiteInline(admin.TabularInline):
    model = WorkerSite
    verbose_name_plural = "Workers Sites"
    verbose_name = "Worker Site"
    extra = 0

class SiteInline(admin.TabularInline):
    model = Site
    verbose_name_plural = "Sites"
    verbose_name = "Site"
    extra = 0

class ProjectAdmin(admin.ModelAdmin):
    list_display = [
        "name",
    ]
    inlines = [
        SiteInline,
    ]
    search_fields = ("name",)
    ordering = ("name",)

class SiteAdmin(admin.ModelAdmin):
    list_display = [
        "name",
    ]
    inlines = [
        WorkerSiteInline
    ]
    search_fields = ("name",)
    ordering = ("name",)

class HelmetAdmin(admin.ModelAdmin):
    list_display = [
        "name",
    ]
    search_fields = ("name",)
    ordering = ("name",)

class CustomUserAdmin(UserAdmin):
    add_form = UserModelCreationForm
    form = UserModelChangeForm
    model = CustomUserModel
    inlines = [
        WorkerSiteInline,
        WorkerRecordInline
    ]
    list_display = [
        "email",
        "is_staff",
        "role",
    ]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "department", "phone", "role")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "department", "phone", "role", "password1", "password2", "is_active", "is_staff", "is_superuser"),
        }),
    )
    search_fields = ("email",)
    ordering = ("email",)
    list_filter = ("is_active", "is_staff", "is_superuser", "role")

# admin.site.register(WorkerRecord, WorkerRecordAdmin)
admin.site.register(Helmet, HelmetAdmin)
admin.site.register(Site, SiteAdmin)
admin.site.register(CustomUserModel, CustomUserAdmin)
admin.site.register(Project, ProjectAdmin)