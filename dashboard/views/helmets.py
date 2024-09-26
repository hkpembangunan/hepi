from types import SimpleNamespace
from django.contrib import messages
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.shortcuts import redirect, render
from django.urls import reverse
from dashboard.forms import HelmetModelForm
from dashboard.helper.util import b64_str, construct_worker_info

from dashboard.models import CustomUserModel, Helmet, HelmetNotification, Site, WorkerRecord


def helmets_list(request):
    if request.user.is_authenticated:
        if request.user.role == CustomUserModel.Roles.ADMIN:
            helmets = Helmet.objects.all()
        elif request.user.role == CustomUserModel.Roles.DIRECTOR:
            helmets = Helmet.objects.filter(site__project__director=request.user,
                                            site__actual_end_date__isnull=True).distinct()
        elif request.user.role == CustomUserModel.Roles.PIC:
            helmets = Helmet.objects.filter(site__pic=request.user, site__actual_end_date__isnull=True).distinct()
        else:
            return redirect(reverse("dashboard"))
        return render(request=request, template_name="dashboard/helmets/list.html", context={
            "user":request.user, 
            "helmets":helmets
        }) 
    else:
        return redirect(reverse("login"))

def helmets_add(request):
    if request.user.is_authenticated:
        if not request.user.role == CustomUserModel.Roles.ADMIN:
            return redirect(reverse("helmets"))
        all_worker = CustomUserModel.objects.filter(role=CustomUserModel.Roles.WORKER)
        user_has_helmet = Helmet.objects.filter(user__isnull=False)
        worker_has_no_helmet = all_worker.exclude(id__in=user_has_helmet.values_list("user", flat=True))
        workerinfos = construct_worker_info(worker_has_no_helmet)
        if request.method == "POST":
            form = HelmetModelForm(request.POST)
            redirect_to = b64_str(request.POST.get("redirect_to"))
            if form.is_valid():
                form.save()
                if redirect_to:
                    messages.success(request, mark_safe(f"Helmet added successfully."), extra_tags="success")
                    return redirect(redirect_to)
                else:
                    messages.success(request, mark_safe(f"Helmet added successfully. <a href={reverse('helmets')}>Back to helmets list</a>."), extra_tags="success")
                    return redirect(reverse("helmets_view", kwargs={"identifier":form.instance.identifier.upper()}))
        return render(request=request, template_name="dashboard/helmets/add.html", context={
            "user":request.user,
            "formerrors": form.errors if 'form' in locals() and form.errors else None,
            "workers": workerinfos,
            "sites": Site.objects.filter(actual_end_date__isnull=True),
        })
    else:
        return redirect(reverse("login"))

def helmets_view(request, identifier):
    if request.user.is_authenticated:
        helmet = Helmet.objects.get(identifier__iexact=identifier)
        last_record = WorkerRecord.objects.filter(helmet=helmet).order_by("-timestamp").first()
        last_record_temp = WorkerRecord.objects.filter(helmet=helmet, temperature__isnull=False).order_by("-timestamp").first()
        last_record_gps = WorkerRecord.objects.filter(helmet=helmet, latitude__isnull=False, longitude__isnull=False).order_by("-timestamp").first()
        l20temp = []
        l20pos = []
        for record in WorkerRecord.objects.filter(helmet=helmet, temperature__isnull=False).order_by("-timestamp")[:20]:
            l20temp.append([record.timestamp, record.temperature] if record.temperature else [record.timestamp, "N/A"])
        
        for record in WorkerRecord.objects.filter(helmet=helmet, latitude__isnull=False, longitude__isnull=False).order_by("-timestamp")[:20]:
            pos = SimpleNamespace()
            pos.lat = record.latitude
            pos.lng = record.longitude
            l20pos.append(pos)
    
        if l20temp.__len__() <= 0:
            l20temp = None
        if l20pos.__len__() <= 0:
            l20pos = None
        return render(request=request, template_name="dashboard/helmets/view.html", context={
            "user":request.user, 
            "helmet":helmet,
            'l20temp': l20temp,
            'l20pos': l20pos,
            'last_record': last_record if 'last_record' in locals() else None,
            'last_record_temp': last_record_temp if 'last_record_temp' in locals() else None,
            'last_record_gps': last_record_gps if 'last_record_gps' in locals() else None,
            "can_edit": request.user.role == CustomUserModel.Roles.ADMIN or request.user == helmet.site.project.director or request.user == helmet.site.pic,
            "can_delete": request.user.role == CustomUserModel.Roles.ADMIN,
        }) 
    else:
        return redirect(reverse("login"))

def helmets_edit(request, identifier):
    if request.user.is_authenticated:
        helmet = Helmet.objects.get(identifier__iexact=identifier)
        if not request.user.role == CustomUserModel.Roles.ADMIN and not request.user == helmet.site.project.director and not request.user == helmet.site.pic:
            return redirect(reverse("helmets"))
        user_has_helmet = Helmet.objects.filter(user__isnull=False)
        all_worker = CustomUserModel.objects.filter(role=CustomUserModel.Roles.WORKER)
        worker_has_no_helmet = all_worker.exclude(id__in=user_has_helmet.values_list("user", flat=True))
        workerinfos = construct_worker_info(list(worker_has_no_helmet) + [helmet.user])
        sites = Site.objects.filter(actual_end_date__isnull=True)
        if request.method == "POST":
            form = HelmetModelForm(request.POST, instance=helmet)
            redirect_to = b64_str(request.POST.get("redirect_to"))
            if form.is_valid():
                form.save()
                if redirect_to:
                    messages.success(request, mark_safe(f"Helmet edited successfully."), extra_tags="success")
                    return redirect(redirect_to)
                else:
                    messages.success(request, mark_safe(f"Helmet edited successfully. <a href={reverse('helmets')}>Back to helmets list</a>."), extra_tags="success")
                    return redirect(reverse("helmets_view", kwargs={"identifier":form.instance.identifier.upper()}))

        return render(request=request, template_name="dashboard/helmets/edit.html", context={
            "user":request.user,
            "helmet": helmet,
            "formerrors": form.errors if 'form' in locals() and form.errors else None,
            "workers": workerinfos,
            "sites": sites,
        })
    else:
        return redirect(reverse('login'))

def helmets_delete(request):
    if request.user.is_authenticated:
        if not request.user.role == CustomUserModel.Roles.ADMIN:
            return redirect(reverse("helmets"))
        if request.method == "POST":
            identifier = request.POST.get("identifier")
            helmet = Helmet.objects.get(identifier__iexact=identifier)
            helmet.delete()
            redirect_to = b64_str(request.POST.get("redirect_to"))
            if redirect_to:
                messages.success(request, mark_safe(f"Helmet deleted successfully."), extra_tags="success")
                return redirect(redirect_to)
            else:
                messages.success(request, mark_safe(f"Helmet deleted successfully. <a href={reverse('helmets')}>Back to helmets list</a>."), extra_tags="success")
                return redirect(reverse("helmets"))
        return redirect(reverse("helmets"))
    else:
        return redirect(reverse("login"))

def helmets_notification_done(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            redirect_to = b64_str(request.POST.get("redirect_to"))
            helmet_notif_id = request.POST.get("helmet_notif_id")
            try: 
                notif = HelmetNotification.objects.get(id=helmet_notif_id)
                notif.resolved_at = timezone.now()
                notif.save()
                messages.success(request, mark_safe(f"Notification resolved at {notif.resolved_at.astimezone().strftime('%d-%m-%Y %souH:%M:%S')}"), extra_tags="success")
            except:
                messages.error(request, mark_safe(f"Notification not found."), extra_tags="danger")
            if redirect_to:
                return redirect(redirect_to)
            else:
                return redirect(reverse("helmets"))
        else:
            return redirect(reverse("helmets"))
    else:
        return redirect(reverse("login"))