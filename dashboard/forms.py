from django.urls import reverse
from django.utils import timezone
from .models import HelmetNotification, Project, Site, CustomUserModel, WorkerSite, Helmet
from .helper import debug_tools as deb
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.safestring import mark_safe

class ProjectModelForm(forms.ModelForm):
    def is_valid(self):
        valid = super(ProjectModelForm, self).is_valid()
        if not valid:
            return valid
        self.data = self.data.copy()
        start_date = self.cleaned_data.get('start_date')
        expected_end_date = self.cleaned_data.get('expected_end_date')
        if start_date > expected_end_date:
            self.add_error("expected_end_date", "Expected end date must be after start date")
            return False
        sites = Site.objects.filter(project=self.instance)
        earliest_site_by_start_date = sites.order_by("start_date").first()
        latest_site_by_expected_end_date = sites.order_by("-expected_end_date").first()
        if earliest_site_by_start_date:
            if start_date > earliest_site_by_start_date.start_date:
                self.add_error("start_date", 
                    mark_safe(
                    "Start date must be before earliest site start date which is " +
                        earliest_site_by_start_date.start_date.strftime("%d-%m-%Y")
                    + " in <a href=\'" + reverse('sites_view', kwargs={'site_id': earliest_site_by_start_date.id}) + "\'> this site</a>"
                    )
                )
                return False
        if latest_site_by_expected_end_date:
            if expected_end_date < latest_site_by_expected_end_date.expected_end_date:
                self.add_error("expected_end_date",
                            mark_safe(
                                "Expected end date must be after latest site expected end date which is " +
                                    latest_site_by_expected_end_date.expected_end_date.strftime("%d-%m-%Y")
                                    + " in <a href=\'" + reverse('sites_view', kwargs={'site_id': latest_site_by_expected_end_date.id}) + "\'> this site</a>"
                            )
                            )
                return False
        return True
        
    class Meta:
        model = Project
        fields = "__all__"

class SiteModelForm(forms.ModelForm):
    def is_valid(self) -> bool:
        valid = super(SiteModelForm, self).is_valid()
        if not valid:
            return valid
        start_date = self.cleaned_data.get('start_date')
        expected_end_date = self.cleaned_data.get('expected_end_date')
        project_start_date = self.instance.project.start_date
        project_end_date = self.instance.project.expected_end_date
        if start_date < project_start_date:
            self.add_error("start_date", "Start date must be after project start date which is " + project_start_date.strftime("%d-%m-%Y"))
            return False
        if expected_end_date > project_end_date:
            self.add_error("expected_end_date", "Expected end date must be before project expected end date which is " + project_end_date.strftime("%d-%m-%Y"))
            return False
        if start_date > expected_end_date:
            self.add_error("expected_end_date", "Expected end date must be after start date")
            return False
        return True
    class Meta:
        model = Site
        fields = "__all__"

class HelmetModelForm(forms.ModelForm):
    class Meta:
        model = Helmet
        fields = "__all__"
    def is_valid(self):
        self.data = self.data.copy()
        if ids:= self.data.get('identifier'):
            self.data["identifier"] = ids.upper()
        if self.data.get('site') == "unassigned":
            self.data["site"] = None
        if self.data.get('user') == "unassigned":
            self.data["user"] = None
        valid = super(HelmetModelForm, self).is_valid()
        if not valid:
            return valid
        user = self.cleaned_data.get('user')
        site = self.cleaned_data.get('site')
        if (user is not None and site is None):
            self.add_error("user", "User is not assigned to this site")
            return False
        elif user and site and (user.workersite_set.filter(site__actual_end_date__isnull=True).first().site != site):
            self.add_error("user", "User is not assigned to this site")
            return False
        elif user and Helmet.objects.filter(user=user).exists() and Helmet.objects.filter(user=user).first() != self.instance:
            self.add_error("user", "User already has a helmet")
            return False
        else:
            return True

class WorkerCreationForm(UserCreationForm):
    site = forms.IntegerField(required=False)
    class Meta:
        model = CustomUserModel
        fields = ("email", "first_name", "last_name", "phone", "department", "role", "site", "password1", "password2")
    def is_valid(self):
        valid = super(WorkerCreationForm, self).is_valid()
        if not valid:
            return valid
        if self.cleaned_data.get("role") != "WRK":
            self.add_error("role", "Role must be Worker")
            return False
        if site_id := self.cleaned_data.get("site"):
            if not Site.objects.filter(id=site_id).exists():
                self.add_error("site", "Site does not exist")
                return False
            else:
                return True
        return True
    def save(self, commit=True):
        user = super(WorkerCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data.get("password1"))
        if commit:
            user.save()
            if site_id := self.cleaned_data.get("site"):
                WorkerSite.objects.create(worker=user, site_id=site_id)
        return user

class WorkerEditForm(UserChangeForm):
    site = forms.IntegerField(required=False)
    helmet = forms.IntegerField(required=False) 
    class Meta:
        model = CustomUserModel
        fields = ("email", "first_name", "last_name", "role", "phone", "department")
    def is_valid(self):
        self.data = self.data.copy()
        helmet_id = self.data.get('helmet')
        site_id = self.data.get('site')
        phone = self.data.get('phone')
        if phone[0] != "0":
            self.data["phone"] = "0" + phone
        if helmet_id == "unassigned":
            self.data["helmet"] = None
        if site_id == "unassigned":
            self.data["site"] = None
        valid = super(WorkerEditForm, self).is_valid()
        if not valid:
            return valid
        if self.cleaned_data.get("role") != CustomUserModel.Roles.WORKER: 
            self.add_error("role", "Role must be Worker")
            return False
        
        site_id = self.cleaned_data.get("site")
        helmet_id = self.cleaned_data.get("helmet")
        site_instance = Site.objects.filter(id=site_id).first()
        helmet_instance = Helmet.objects.filter(id=helmet_id).first()
        if site_id and not site_instance:
            self.add_error("site", "Site does not exist")
            return False
        if helmet_id and not helmet_instance:
            self.add_error("helmet", "Helmet does not exist")
            return False

        if site_instance:
            if helmet_instance:
                if helmet_instance.site != site_instance:
                    self.add_error("helmet", "Helmet is not assigned to this site")
                    return False
                if helmet_instance.user is not None and helmet_instance.user != self.instance:
                    self.add_error("helmet", "Helmet is already assigned to another user")
                    return False
        return True 

    def save(self, commit=True):
        user = super(WorkerEditForm, self).save(commit=False)
        if commit:
            old_site_id = WorkerSite.objects.filter_active(worker=user).values_list("site_id", flat=True).first()
            # delete old site
            if old_site_id:
                WorkerSite.objects.filter_active(worker=user, site_id=old_site_id).delete()
            if site_id := self.cleaned_data.get("site"):
                WorkerSite.objects.create(worker=user, site_id=site_id)
            if helmet_id := self.cleaned_data.get("helmet"):
                Helmet.objects.filter(user=user).update(user=None)
                Helmet.objects.filter(id=helmet_id).update(user=user)
            if helmet_id is None:
                Helmet.objects.filter(user=user).update(user=None)
            if site_id is None:
                helmobj = Helmet.objects.filter(user=user).first()
                if helmobj:
                    helmobj.update(site=None)
            user.save()
        return user

class ProfileChangeForm(UserChangeForm):
    class Meta:
        model = CustomUserModel
        fields = ("email", "first_name", "last_name", "phone")
    def is_valid(self):
        self.data = self.data.copy()
        phone = self.data.get('phone')
        if phone[0] != "0":
            self.data["phone"] = "0" + phone
        return super(ProfileChangeForm, self).is_valid()
        
class UserChangePasswordForm(UserCreationForm):
    class Meta:
        model = CustomUserModel
        fields = ("password1", "password2")
    def save(self, commit=True):
        user = super(UserChangePasswordForm, self).save(commit=False)
        user.set_password(self.cleaned_data.get("password1"))
        if commit:
            user.save()
        return user
    
class SiteFinishForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = ("actual_end_date",)
    def is_valid(self):
        self.data = self.data.copy()
        self.data["actual_end_date"] = timezone.now().date()
        valid = super(SiteFinishForm, self).is_valid()
        if not valid:
            return valid
        if self.data.get("actual_end_date") < self.instance.start_date:
            self.add_error("actual_end_date", "Site not started yet")
            return False
        return True
    def save(self, commit=True):
        site = super(SiteFinishForm, self).save(commit=False)
        if commit:
            site.save()
            # clear all helmet
            Helmet.objects.filter(site=site).update(site=None, user=None)
            site_notifs = HelmetNotification.objects.filter(site=site, resolved_at__isnull=True)
            for notif in site_notifs:
                notif.resolved_at = site.actual_end_date
                notif.save()
        return site

class SiteUnfinishForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = ("actual_end_date",)
    def is_valid(self):
        self.data = self.data.copy()
        self.data["actual_end_date"] = None
        project = self.instance.project
        if project.actual_end_date:
            self.add_error("actual_end_date", "Project already finished")
            return False
        return super(SiteUnfinishForm, self).is_valid()
    def save(self, commit=True):
        site = super(SiteUnfinishForm, self).save(commit=False)
        if commit:
            site.save()
        return site

class ProjectFinishForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ("actual_end_date",)
    def is_valid(self):
        self.data = self.data.copy()
        self.data["actual_end_date"] = timezone.now().date()
        valid = super(ProjectFinishForm, self).is_valid()
        if not valid:
            return valid
        if self.data.get("actual_end_date") < self.instance.start_date:
            self.add_error("actual_end_date", "Project not started yet")
            return False
        sites = Site.objects.filter(project=self.instance)
        not_started_sites = sites.filter(start_date__gt=self.cleaned_data.get("actual_end_date"))
        if not_started_sites.exists():
            self.add_error("actual_end_date", "There are sites that have not started yet")
            return False
        return True
    def save(self, commit=True):
        project = super(ProjectFinishForm, self).save(commit=False)
        if commit:
            project.save()
            # clear all helmet
            Helmet.objects.filter(site__project=project).update(site=None, user=None)
            # finish all sites
            for site in Site.objects.filter(project=project):
                site.actual_end_date = project.actual_end_date
                site.save()
                Helmet.objects.filter(site=site).update(site=None, user=None)
                site_notifs = HelmetNotification.objects.filter(site=site, resolved_at__isnull=True)
                for notif in site_notifs:
                    notif.resolved_at = project.actual_end_date
                    notif.save()
        return project

class ProjectUnfinishForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ("actual_end_date",)
    def is_valid(self):
        self.data = self.data.copy()
        self.data["actual_end_date"] = None
        return super(ProjectUnfinishForm, self).is_valid()
    def save(self, commit=True):
        project = super(ProjectUnfinishForm, self).save(commit=False)
        if commit:
            project.save()
        return project
    
