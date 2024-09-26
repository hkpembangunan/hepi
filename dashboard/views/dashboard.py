from types import SimpleNamespace
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.utils.safestring import mark_safe

from dashboard.models import CustomUserModel, Helmet, HelmetNotification, Project, Site, WorkerRecord
from dashboard.templatetags.dashboard_extras import construct_notification


def dashboard_request(request):
    if request.user.is_authenticated:
        counts = SimpleNamespace()
        tznow = timezone.now()
        all_notifications = HelmetNotification.objects.all()
        if request.user.role == CustomUserModel.Roles.ADMIN: 
            projects = Project.objects.filter(actual_end_date__isnull=True, start_date__lte=tznow)
            sites = Site.objects.filter(actual_end_date__isnull=True, start_date__lte=tznow)
            workers = CustomUserModel.objects.filter(role=CustomUserModel.Roles.WORKER, workersite__site__in=sites)
            helmets = Helmet.objects.filter(site__in=sites)
            counts = SimpleNamespace()
            counts.project = projects.count()
            counts.site = sites.count()
            counts.worker = workers.count()
            counts.helmet = helmets.count()
        elif request.user.role == CustomUserModel.Roles.DIRECTOR:
            active_and_upcoming = Project.objects.filter(
                director=request.user, 
                actual_end_date__isnull=True
            )
            projects = Project.objects.filter(
                director=request.user,
                actual_end_date__isnull=True,
                start_date__lte=tznow
            )
            sites = Site.objects.filter(
                project__in=projects,
                actual_end_date__isnull=True,
                start_date__lte=tznow
            )
            workers = CustomUserModel.objects.filter(
                role=CustomUserModel.Roles.WORKER,
                workersite__site__in=sites
            )
            helmets = Helmet.objects.filter(site__in=sites)
            all_notifications = all_notifications.filter(site__project__in=projects)
            counts = SimpleNamespace()
            counts.project = projects.count()
            counts.site = sites.count()
            counts.worker = workers.count()
            counts.helmet = helmets.count()
            if counts.worker > 5:
                top_workers = workers.order_by("-workersite__site__start_date")[:5]
            else:
                top_workers = workers.order_by("-workersite__site__start_date")
        elif request.user.role == CustomUserModel.Roles.PIC:
            active_and_upcoming = Site.objects.filter(pic=request.user, actual_end_date__isnull=True)
            sites = Site.objects.filter(pic=request.user, actual_end_date__isnull=True, start_date__lte=tznow)
            workers = CustomUserModel.objects.filter(role=CustomUserModel.Roles.WORKER, workersite__site__in=sites)
            helmets = Helmet.objects.filter(site__in=sites)
            all_notifications = all_notifications.filter(site__in=sites)
            counts = SimpleNamespace()
            counts.site = sites.count()
            counts.worker = workers.count()
            counts.helmet = helmets.count()
            if counts.worker > 5:
                top_workers = workers.order_by("-workersite__site__start_date")[:5]
            else:
                top_workers = workers.order_by("-workersite__site__start_date")
        else:
            helmet = Helmet.objects.get(user=request.user)
            last_record = WorkerRecord.objects.filter(helmet=helmet).order_by("-timestamp").first()
            last_record_temp = WorkerRecord.objects.filter(helmet=helmet, temperature__isnull=False).order_by("-timestamp").first()
            last_record_gps = WorkerRecord.objects.filter(helmet=helmet, latitude__isnull=False, longitude__isnull=False).order_by("-timestamp").first()
            l20temp = []
            l20pos = []
            for recs in WorkerRecord.objects.filter(helmet=helmet, temperature__isnull=False).order_by("-timestamp")[:20]:
                l20temp.append(
                    [recs.timestamp, recs.temperature]
                )
            
            
            for recs in WorkerRecord.objects.filter(helmet=helmet, latitude__isnull=False, longitude__isnull=False).order_by("-timestamp")[:20]:
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
        
        urn_site_id = request.GET.get("urn_site_id", "all")
        if urn_site_id.isdigit():
            all_notifications = all_notifications.filter(site__id=urn_site_id)
        
        unresolved_notifications = all_notifications.filter(resolved_at__isnull=True).order_by("-id")
        if unresolved_notifications.__len__() > 5:
            unresolved_notifications = unresolved_notifications[:5]
        return render(request=request, template_name="dashboard/dashboard.html", context={
            "user":request.user, 
            "counts":counts,
            "sites":sites if 'sites' in locals() else None,
            "top_workers":top_workers if 'top_workers' in locals() else None,
            "active_and_upcoming":active_and_upcoming if 'active_and_upcoming' in locals() else None,
            "unresolved_notifications": unresolved_notifications if 'unresolved_notifications' in locals() else None,
            "all_notification_counter": all_notifications.count() if 'all_notifications' in locals() else None,
            "resolved_notification_counter": all_notifications.filter(resolved_at__isnull=False).count() if 'all_notifications' in locals() else None,
            # worker
            "helmet":helmet if 'helmet' in locals() else None,
            'l20temp':l20temp if 'l20temp' in locals() else None,
            'l20pos':l20pos if 'l20pos' in locals() else None,
            'last_record':last_record if 'last_record' in locals() else None,
            'last_record_temp':last_record_temp if 'last_record_temp' in locals() else None,
            'last_record_gps':last_record_gps if 'last_record_gps' in locals() else None,
        }) 
    else:
        return redirect(reverse("login"))
