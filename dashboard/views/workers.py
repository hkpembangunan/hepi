from django.shortcuts import redirect, render
from django.urls import reverse
from dashboard.forms import UserChangePasswordForm, WorkerCreationForm, WorkerEditForm
from dashboard.helper.util import b64_str, construct_worker_info, is_left_role_higher_or_equal
from dashboard.models import CustomUserModel, Helmet, HelmetNotification, Site, WorkerSite
from django.db.models.functions import Concat
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.db.models import Q, Value
from django.contrib.auth import update_session_auth_hash

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from dashboard.templatetags.dashboard_extras import construct_notification

def workers_list(request):
    if request.user.is_authenticated:
        site_id = request.GET.get("site_id", "all")
        name = request.GET.get("name", None)
        if request.user.role == CustomUserModel.Roles.ADMIN:
            poolworkers = CustomUserModel.objects.filter(role=CustomUserModel.Roles.WORKER)
            sites = Site.objects.filter(actual_end_date__isnull=True)
        elif request.user.role == CustomUserModel.Roles.DIRECTOR:
            poolworkers = CustomUserModel.objects.filter(workersite__site__project__director=request.user, workersite__site__actual_end_date__isnull=True).distinct()
            sites = Site.objects.filter(project__director=request.user, actual_end_date__isnull=True)
        elif request.user.role == CustomUserModel.Roles.PIC:
            sites = Site.objects.filter(pic=request.user, actual_end_date__isnull=True)
            poolworkers = CustomUserModel.objects.filter(workersite__site__pic=request.user,
                                                         workersite__site__actual_end_date__isnull=True
                                                         ).distinct()
        else:
            return redirect(reverse("dashboard"))
        if site_id.isdigit():
            workers = poolworkers.filter(
                workersite__site__id=site_id
            )
        elif site_id == "unassigned":
            workers = poolworkers.filter(
                workersite__site__isnull=True
            )
        else:
            workers = poolworkers
        if name:
            workers = workers.annotate(full_name=Concat("first_name", Value(" "), "last_name")).filter(full_name__icontains=name)
        return render(request=request, template_name="dashboard/workers/list.html", context={
            "user":request.user, 
            "workers": construct_worker_info(workers),
            "sites": sites,
        }) 
    else:
        return redirect(reverse("login"))

def workers_add(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            mutablereq = request.POST.copy()
            if mutablereq.get("site") == "unassigned":
                mutablereq["site"] = None
            form = WorkerCreationForm(mutablereq)
            redirect_to = b64_str(request.POST.get("redirect_to"))
            if form.is_valid():
                form.save()
                if redirect_to:
                    messages.success(request, mark_safe("Worker added successfully"), extra_tags="success")
                    return redirect(redirect_to)
                else:
                    messages.success(request, mark_safe(f"Worker added successfully."), extra_tags="success")
                    return redirect(reverse("workers"))
        sites = Site.objects.filter(actual_end_date__isnull=True)
        all_workers = CustomUserModel.objects.filter(role=CustomUserModel.Roles.WORKER)
        active_workersite = WorkerSite.objects.filter(site__actual_end_date__isnull=True)
        unassigned_workers = all_workers.exclude(id__in=active_workersite.values_list("worker__id", flat=True))
        return render(request=request, template_name="dashboard/workers/add.html", context={
            "user":request.user,
            "sites": sites,
            "unassigned_workers": unassigned_workers if request.GET.get("site_id", None) else None,
            "site_specific": Site.objects.get(id=request.GET.get("site_id", None)),
            "worker_role": CustomUserModel.Roles.WORKER,
            "formerrors": form.errors if 'form' in locals() and form.errors else None,
        })
    else:
        return redirect(reverse("login"))


def workers_edit(request, worker_id):
    if request.user.is_authenticated:
        worker = CustomUserModel.objects.get(id=worker_id)
        if not worker or worker.role != CustomUserModel.Roles.WORKER:
            return redirect(reverse("workers"))
        if request.method == "POST":
            mutablereq = request.POST.copy()
            redirect_to = b64_str(request.POST.get("redirect_to"))
            if mutablereq.get("site") == "unassigned":
                mutablereq["site"] = None
            form = WorkerEditForm(mutablereq, instance=worker)
            if form.is_valid():
                form.save()
                if redirect_to:
                    messages.success(request, mark_safe("Worker edited successfully"), extra_tags="success")
                    return redirect(redirect_to)
                else:
                    messages.success(request, mark_safe(f"Worker edited successfully."), extra_tags="success")
                    return redirect(reverse("workers"))
        sites = Site.objects.filter(actual_end_date__isnull=True)
        workerinfo = construct_worker_info([worker])[0]
        helmets = list(Helmet.objects.filter(
            Q(user__isnull=True) | Q(user=worker)
        ))
        return render(request=request, template_name="dashboard/workers/edit.html", context={
            "user":request.user,
            "worker": workerinfo,
            "sites": sites,
            "formerrors": form.errors if 'form' in locals() and form.errors else None,
            "worker_role": CustomUserModel.Roles.WORKER,
            "helmets": helmets,
        })
    else:
        return redirect(reverse("login"))

def workers_change_password(request, worker_id):
    if request.user.is_authenticated:
        worker = CustomUserModel.objects.get(id=worker_id)
        if not worker or worker.role != CustomUserModel.Roles.WORKER:
            return redirect(reverse("workers"))
        if request.method == "POST":
            redirect_to = b64_str(request.POST.get("redirect_to"))
            form = UserChangePasswordForm(request.POST, instance=worker)
            if form.is_valid():
                form.save()
                update_session_auth_hash(request, worker)
                if redirect_to:
                    messages.success(request, mark_safe("Password changed successfully"), extra_tags="success")
                    return redirect(redirect_to)
                else:
                    messages.success(request, mark_safe(f"Password changed successfully."), extra_tags="success")
                    return redirect(reverse("workers"))
        return render(request=request, template_name="dashboard/workers/change_password.html", context={
            "user":request.user,
            "worker": construct_worker_info([worker])[0],
            "formerrors": form.errors if 'form' in locals() and form.errors else None,
        })
    else:
        return redirect(reverse("login"))
        
def workers_delete(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            worker_id = request.POST.get("worker_id")
            worker = CustomUserModel.objects.get(id=worker_id)
            if worker.role != CustomUserModel.Roles.WORKER:
                return redirect(reverse("workers"))
            worker_name = (worker.first_name + " " + worker.last_name).title()
            worker.delete()
            messages.success(request, mark_safe(f"Worker <b>{worker_name}</b> deleted successfully."), extra_tags="success")
            redirect_to = b64_str(request.POST.get("redirect_to"))
            if redirect_to:
                return redirect(redirect_to)
            else:
                return redirect(reverse("workers"))
        return redirect(reverse("workers"))
    else:
        return redirect(reverse("login"))

def workers_notifications(request):
    if request.user.is_authenticated:
        if not is_left_role_higher_or_equal(request.user.role, CustomUserModel.Roles.PIC):
            return redirect(reverse("dashboard"))
        site_id = request.GET.get("site_id", "all")
        sites = Site.objects.filter(actual_end_date__isnull=True)    
        if site_id.isdigit():
            notifications = HelmetNotification.objects.filter(site__id=site_id)
        else:
            notifications = HelmetNotification.objects.all()

        notification_type = request.GET.get("notification_type", "unresolved")
        if notification_type == "unresolved":
            notifications = notifications.filter(resolved_at__isnull=True)
        elif notification_type == "resolved":
            notifications = notifications.filter(resolved_at__isnull=False)
        
        if request.user.role == CustomUserModel.Roles.DIRECTOR:
            sites = sites.filter(project__director=request.user)
            notifications = notifications.filter(site__in=sites)
        elif request.user.role == CustomUserModel.Roles.PIC:
            sites = sites.filter(pic=request.user)
            notifications = notifications.filter(site__pic=request.user)

        return render(
            request=request, template_name="dashboard/workers/notifications.html", context={
                "user":request.user,
                "sites": sites,
                "notifications": notifications
            }
        )
    else:
        return redirect(reverse("login"))

def workers_send_help(request):
    if request.user.is_authenticated:
        if request.user.role == CustomUserModel.Roles.WORKER and request.method == "POST":
            identifier = request.POST.get("identifier", None)
            site_id = request.POST.get("site_id", None)
            user_who_to_be_notified = HelmetNotification.objects.get_who_to_notify(site_id)
            notification_instance = HelmetNotification.objects.create_notification(
                type=HelmetNotification.Types.WARNING,
                message="Help Needed!",
                helmet=Helmet.objects.get(identifier__iexact=identifier),
                user=request.user,
                site=Site.objects.get(id=site_id),
                resolved_at=None,
            )
            if notification_instance is None:
                messages.error(request, mark_safe(f"Help Request Already Sent!"), extra_tags="danger")
                return redirect(reverse("dashboard"))
            channel_layer = get_channel_layer()
            for user in user_who_to_be_notified:
                async_to_sync(channel_layer.group_send)(
                    'notification_user_%s' % user.id, {
                        'type': 'user_send_notification',
                    } | construct_notification(notification_instance)
                )
            messages.success(request, mark_safe(f"Help Request Sent!"), extra_tags="success")
            return redirect(reverse("dashboard"))
    else:
        return redirect(reverse("dashboard"))