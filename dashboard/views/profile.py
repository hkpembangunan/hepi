from types import SimpleNamespace
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.utils.safestring import mark_safe
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from dashboard.forms import ProfileChangeForm, UserChangePasswordForm

from dashboard.helper.util import b64_str, is_left_role_higher_or_equal
from dashboard.models import CustomUserModel, Helmet, Project, Site, WorkerRecord, WorkerSite


def profile_view(request, user_id):
    if request.user.is_authenticated:
        user = CustomUserModel.objects.get(id=user_id)
        if user is None:
            return redirect(reverse("dashboard"))
        if user.role == CustomUserModel.Roles.DIRECTOR:
            showcase = list(user.project_set.order_by('start_date'))
            if len(showcase) >= 3:
                showcase = showcase[-3:]
            projects = Project.objects.filter(director=user)
            sites = Site.objects.filter(project__in=projects)
            workers = WorkerSite.objects.filter(site__in=sites)
            counts = {
                "projects": projects.count(),
                "sites": sites.count(),
                "workers": workers.count(),
            }
        elif user.role == CustomUserModel.Roles.PIC:
            showcase = list(user.pic.order_by('start_date'))
            if len(showcase) >= 3:
                showcase = showcase[-3:]
            sites = Site.objects.filter(pic=user)
            workers = WorkerSite.objects.filter(site__in=sites)
            counts = {
                "sites": sites.count(),
                "workers": workers.count(),
            }
        elif user.role == CustomUserModel.Roles.WORKER:
            helmet = Helmet.objects.get(user=user)
            last_record = WorkerRecord.objects.filter(helmet=helmet).order_by("-timestamp").first()
            last_record_temp = WorkerRecord.objects.filter(helmet=helmet, temperature__isnull=False).order_by("-timestamp").first()
            last_record_gps = WorkerRecord.objects.filter(helmet=helmet, latitude__isnull=False, longitude__isnull=False).order_by("-timestamp").first()
            l20temp = []
            l20pos = []
            for recs in WorkerRecord.objects.filter(helmet=helmet, temperature__isnull=False).order_by('-timestamp')[:20]:
                l20temp.append(
                    [recs.timestamp, recs.temperature]
                )
            for recs in WorkerRecord.objects.filter(helmet=helmet, latitude__isnull=False, longitude__isnull=False).order_by('-timestamp')[:20]:
                pos = SimpleNamespace()
                pos.lat = recs.latitude
                pos.lng = recs.longitude
                l20pos.append(
                    pos
                )
            
            if l20temp.__len__() <= 0:
                l20temp = None
            if l20pos.__len__() <= 0:
                l20pos = None
        return render(request=request, template_name="dashboard/profile/view.html", context={
            "user":request.user, 
            "profile":user,
            'l20temp': l20temp if 'l20temp' in locals() else None,
            'l20pos': l20pos if 'l20pos' in locals() else None,
            'last_record': last_record if 'last_record' in locals() else None,
            'last_record_temp': last_record_temp if 'last_record_temp' in locals() else None,
            'last_record_gps': last_record_gps if 'last_record_gps' in locals() else None,
            'helmet': helmet if 'helmet' in locals() else None,
            "showcase": showcase if 'showcase' in locals() else None,
            "counts": counts if 'counts' in locals() else None,
            "can_edit": is_left_role_higher_or_equal(request.user.role, CustomUserModel.Roles.ADMIN) or request.user.id == user.id
        })
    else:
        return redirect(reverse("login"))

def profile_edit(request, user_id):
    if request.user.is_authenticated:
        if not(is_left_role_higher_or_equal(request.user.role, CustomUserModel.Roles.ADMIN) or request.user.id == user_id):
            return redirect(reverse("profile_view", kwargs={"user_id":user_id}))
        user = CustomUserModel.objects.get(id=user_id)
        if user is None:
            return redirect(reverse("dashboard"))
        if request.method == "POST":
            form = ProfileChangeForm(request.POST, instance=user)
            redirect_to = b64_str(request.POST.get("redirect_to"))
            if form.is_valid():
                form.save()
                if redirect_to:
                    messages.success(request, mark_safe(f"Profile edited successfully."), extra_tags="success")
                    return redirect(redirect_to)
                else:
                    messages.success(request, mark_safe(f"Profile edited successfully."), extra_tags="success")
                    return redirect(reverse("profile_view", kwargs={"user_id":user.id}))
        userinfo = SimpleNamespace()
        userinfo.id = user.id
        userinfo.first_name = user.first_name
        userinfo.last_name = user.last_name
        userinfo.email = user.email
        userinfo.role = CustomUserModel.Roles(user.role)
        userinfo.department = user.department
        userinfo.phone = user.phone
        userinfo.date_joined = user.date_joined.astimezone()
        return render(request=request, template_name="dashboard/profile/edit.html", context={
            "user": request.user,
            "userinfo": userinfo,
            "is_admin": is_left_role_higher_or_equal(request.user.role, CustomUserModel.Roles.ADMIN),
            "formerrors": form.errors if 'form' in locals() and form.errors else None,
        })
    else:
        return redirect(reverse("login"))

def profile_change_password(request, user_id):
    if request.user.is_authenticated:
        user = CustomUserModel.objects.get(id=user_id)
        if user is None:
            return redirect(reverse("dashboard"))
        if request.method == "POST":
            redirect_to = b64_str(request.POST.get("redirect_to"))
            form = UserChangePasswordForm(request.POST, instance=user)
            if form.is_valid():
                form.save()
                update_session_auth_hash(request, user)
                if redirect_to:
                    messages.success(request, mark_safe("Password changed successfully"), extra_tags="success")
                    return redirect(redirect_to)
                else:
                    messages.success(request, mark_safe(f"Password changed successfully."), extra_tags="success")
                    return redirect(reverse("profile_view"))
        return render(request=request, template_name="dashboard/profile/change_password.html", context={
            "user":request.user,
            "formerrors": form.errors if 'form' in locals() and form.errors else None,
        })
    else:
        return redirect(reverse("login"))