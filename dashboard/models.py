import uuid
from django.db import IntegrityError, models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.utils import timezone

from enum import Enum
# Create your models here.

class CustomUserModelManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, role, **kwargs):
        user = self.model(
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
            role=role,
            **kwargs
        )
        user.set_password(kwargs.get("password"))
        user.save(using=self._db)
        return user
    def get(self, *args, **kwargs):
        try: 
            return super().get(*args, **kwargs)
        except CustomUserModel.DoesNotExist:
            return None
    def create_superuser(self, email, first_name, last_name, role, **kwargs):
        kwargs.setdefault("is_superuser", True)
        kwargs.setdefault("is_active", True)
        kwargs.setdefault("is_staff", True)
        return self.create_user(email, first_name, last_name, role, **kwargs)

class CustomUserModel(AbstractUser):
    def phone_validator(value):
        if not value.isdigit():
            raise ValidationError(
                _('%(value)s is not a valid phone number'),
                params={'value': value},
            )
        if value[0] != '0':
            value = '0' + value
        if len(value) < 10:
            raise ValidationError(
                _('%(value)s is not a valid phone number'),
                params={'value': value},
            )
        
    class Roles(models.TextChoices):
        WORKER = "WRK", _("Worker")
        PIC = "PIC", _("PIC")
        DIRECTOR = "PRD", _("Project Director")
        ADMIN = "ADM", _("Admin")
    username = None
    role = models.CharField(max_length=3, choices=Roles.choices, default=Roles.WORKER)
    email = models.EmailField(_('Email Address'), unique=True)
    phone = models.CharField(max_length=32, validators=[phone_validator]) # with leading 0
    department = models.CharField(max_length=50)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        "first_name",
        "last_name",
        "role",
    ]
    objects = CustomUserModelManager()
    def __str__(self):
        return self.email

class ProjectManager(models.Manager):
    def get(self, *args, **kwargs):
        try: 
            return super().get(*args, **kwargs)
        except Project.DoesNotExist:
            return None

class Project(models.Model):
    name = models.CharField(max_length=50)
    director = models.ForeignKey(CustomUserModel, on_delete=models.CASCADE,
                                limit_choices_to={'role': CustomUserModel.Roles.DIRECTOR})
    region = models.CharField(max_length=50, default="")
    description = models.TextField(default="", blank=True)
    start_date = models.DateField(default=timezone.now)
    expected_end_date = models.DateField(default=timezone.now)
    actual_end_date = models.DateField(null=True, blank=True)
    department = models.CharField(max_length=50, default="")
    objects = ProjectManager()
    def __str__(self):
        return self.name

class SiteManager(models.Manager):
    def get(self, *args, **kwargs):
        try: 
            return super().get(*args, **kwargs)
        except Site.DoesNotExist:
            return None
        
        

class Site(models.Model):
    name = models.CharField(max_length=50)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="sites")
    pic = models.ForeignKey(CustomUserModel, on_delete=models.CASCADE,
                            limit_choices_to={'role': CustomUserModel.Roles.PIC},
                            related_name="pic")
    workers = models.ManyToManyField(CustomUserModel, through="WorkerSite", related_name="sites", blank=True)
    description = models.TextField(default="", blank=True)
    start_date = models.DateField(default=timezone.now)
    expected_end_date = models.DateField(default=timezone.now)
    actual_end_date = models.DateField(null=True, blank=True)
    objects = SiteManager()
    def __str__(self):
        return self.name
        
class HelmetManager(models.Manager):
    def get(self, *args, **kwargs):
        try: 
            return super().get(*args, **kwargs)
        except Helmet.DoesNotExist:
            return None

class Helmet(models. Model):
    identifier = models.CharField(max_length=50, unique=True,
                                  validators=[RegexValidator(r'^[0-9a-zA-Z-]*$')])
    name = models.CharField(max_length=50)
    user = models.OneToOneField(CustomUserModel, on_delete=models.SET_NULL, null=True, blank=True, unique=True)
    site = models.ForeignKey(Site, on_delete=models.SET_NULL, null=True, blank=True)
    last_active = models.DateTimeField(auto_now=True)
    objects = HelmetManager()
    def __str__(self):
        return self.name

class WorkerRecordManager(models.Manager):
    def get(self, *args, **kwargs):
        try: 
            return super().get(*args, **kwargs)
        except WorkerRecord.DoesNotExist:
            return None
    def first(self, *args, **kwargs):
        try:
            return super().first(*args, **kwargs)
        except WorkerRecord.DoesNotExist:
            return None
    def add_new_record(self, user, helmet, latitude=None, longitude=None, temperature=None, timestamp=None):
        if not (latitude and longitude) and not (temperature):
            return None
        if timestamp is None:
            timestamp = timezone.now()
        record = self.create(timestamp=timestamp, user=user, temperature=temperature, helmet=helmet, latitude=latitude, longitude=longitude)
        return record

class WorkerRecord(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'timestamp'], name='unique_worker_record')
        ]   
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(CustomUserModel, on_delete=models.DO_NOTHING)
    timestamp = models.DateTimeField(auto_now_add=True)
    helmet = models.ForeignKey(Helmet, on_delete=models.DO_NOTHING, null=True, blank=True)
    temperature = models.FloatField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    objects = WorkerRecordManager()
    def __str__(self):
        return f"{self.user} - {self.timestamp} - {self.temperature} - {self.helmet}"

class WorkerSiteManager(models.Manager):
    def get(self, *args, **kwargs):
        try: 
            return super().get(*args, **kwargs)
        except WorkerSite.DoesNotExist:
            return None
    def filter_active(self, *args, **kwargs):
        try:
            return super().filter(*args, **kwargs).filter(site__actual_end_date__isnull=True)
        except:
            return None
        

class WorkerSite(models.Model):
    worker = models.ForeignKey(CustomUserModel, on_delete=models.CASCADE,
                               limit_choices_to={'role': CustomUserModel.Roles.WORKER}, blank=True)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    objects = WorkerSiteManager()
    def __str__(self):
        return f"{self.worker} - {self.site}" 
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['worker', 'site'], name="unique_worker_site")
        ]


class HelmetNotificationManager(models.Manager):
    def get(self, *args, **kwargs):
        try:
            return super().get(*args, **kwargs)
        except HelmetNotification.DoesNotExist:
            return None
    def create_notification(self, type, message, helmet, user, site, resolved_at=None):
        try: 
            if HelmetNotification.objects.filter(type=type, message=message, helmet=helmet, user=user, site=site, resolved_at=resolved_at).exists():
                return None
            notification = self.create(type=type, message=message, helmet=helmet, user=user, site=site, resolved_at=resolved_at)
            return notification
        except IntegrityError:
            return None
    def get_who_to_notify(self, site_id):
        ret = []
        # director
        superusers = CustomUserModel.objects.filter(is_superuser=True).all()
        admins = CustomUserModel.objects.filter(role=CustomUserModel.Roles.ADMIN).all()
        director = Site.objects.get(id=site_id).project.director
        pic = Site.objects.get(id=site_id).pic
        ret.append(director)
        ret.append(pic)
        for user in superusers:
            ret.append(user)
        for user in admins:
            ret.append(user)
        # remove duplicates
        return list(dict.fromkeys(ret))

class HelmetNotification(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['type', 'message', 'helmet', 'user', 'site', 'resolved_at'], name="unique_helmet_notification")
        ]
    class Types(models.TextChoices):
        DANGER = "DNG", _("Danger")
        WARNING = "WRN", _("Warning")
        INFO = "INF", _("Info")
    type = models.CharField(max_length=3, choices=Types.choices, default=Types.INFO)
    message = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    helmet = models.ForeignKey(Helmet, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUserModel, on_delete=models.CASCADE)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    resolved_at = models.DateTimeField(null=True, blank=True)
    objects = HelmetNotificationManager()
    def __str__(self):
        return f"{self.type} - {self.message} - {self.timestamp} - {self.helmet}"