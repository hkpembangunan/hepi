from django.http import HttpResponseNotFound
from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib import messages
from django.utils.safestring import mark_safe
from dashboard.forms import SiteFinishForm, SiteModelForm, SiteUnfinishForm
from dashboard.helper.util import b64_str, construct_worker_info, is_left_role_higher_or_equal
from dashboard.models import CustomUserModel, Helmet, Project, Site, WorkerSite


def sites_list(request):
    if request.user.is_authenticated:
        if is_left_role_higher_or_equal(request.user.role, CustomUserModel.Roles.ADMIN):
            sites = Site.objects.all()
        elif request.user.role == CustomUserModel.Roles.DIRECTOR:
            sites = Site.objects.filter(project__director=request.user)
        elif request.user.role == CustomUserModel.Roles.PIC:
            sites = Site.objects.filter(pic=request.user)
        else:
            return redirect(reverse("dashboard"))
        return render(request=request, template_name="dashboard/sites/list.html", context={
            "user":request.user, 
            "sites":sites
        }) 
    else:
        return redirect(reverse("login"))

def sites_view(request, site_id):
    if request.user.is_authenticated:
        site = Site.objects.get(id=site_id)
        return render(request=request, template_name="dashboard/sites/view.html", context={
            "user":request.user, 
            "site":site,
            "can_edit": (is_left_role_higher_or_equal(request.user.role, CustomUserModel.Roles.ADMIN) or request.user == site.pic or request.user == site.project.director) and not site.actual_end_date,
            "can_delete": is_left_role_higher_or_equal(request.user.role, CustomUserModel.Roles.ADMIN),
            "can_mark_as_done": not site.actual_end_date and (is_left_role_higher_or_equal(request.user.role, CustomUserModel.Roles.ADMIN) or request.user == site.pic or request.user == site.project.director),
            "can_unmark_as_done": site.actual_end_date and (is_left_role_higher_or_equal(request.user.role, CustomUserModel.Roles.ADMIN) or request.user == site.pic or request.user == site.project.director),
            "workers": construct_worker_info(site.workers.all())
        }) 
    else:
        return redirect(reverse("login"))    

def sites_add(request):
    if request.user.is_authenticated:
        if request.user.role == CustomUserModel.Roles.ADMIN:
            projects = Project.objects.all()
        elif request.user.role == CustomUserModel.Roles.DIRECTOR:
            projects = Project.objects.filter(director=request.user)
        else:
            return redirect(reverse("sites"))
        if request.method == "POST":
            if request.user.role == CustomUserModel.Roles.DIRECTOR and request.POST.get("project") not in [str(project.id) for project in projects]:
                messages.error(request, mark_safe(f"You are not allowed to add site to project <b>{request.POST.get('project')}</b>."), extra_tags="danger")
                return redirect(reverse("sites_add"))
            form = SiteModelForm(request.POST)
            redirect_to = b64_str(request.POST.get("redirect_to"))
            if form.is_valid():
                form.save()
                # redirect to redirect_to if it exists
                if redirect_to:
                    messages.success(request, mark_safe(f"Site added successfully."), extra_tags="success")
                    return redirect(redirect_to)
                else:
                    messages.success(request, mark_safe(f"Site added successfully. <a href={reverse('sites')}>Back to sites list</a>."), extra_tags="success")
                    return redirect(reverse("sites_view", kwargs={"site_id":form.instance.id}))

        PICs = CustomUserModel.objects.filter(role=CustomUserModel.Roles.PIC)
        return render(request=request, template_name="dashboard/sites/add.html", context={
            'user': request.user,
            'projects': projects,
            "pics": PICs,
            "formerrors": form.errors if 'form' in locals() and form.errors else None,
        }) 
    else:
        return redirect(reverse("login"))

def sites_edit(request, site_id):
    if request.user.is_authenticated:
        site = Site.objects.get(id=site_id)
        if site.actual_end_date:
            return redirect(reverse("sites_view", kwargs={"site_id":site_id}))
        if is_left_role_higher_or_equal(request.user.role, CustomUserModel.Roles.ADMIN):
            projects = Project.objects.all()
        elif request.user == site.project.director:
            projects = Project.objects.filter(director=request.user)
        elif request.user == site.pic:
            projects = Project.objects.filter(id=site.project.id)
        else:
            return redirect(reverse("sites_view", kwargs={"site_id":site_id}))
        if request.method == "POST":
            postcopy = request.POST.copy()
            workers = site.workers.all()
            postcopy.setlist("workers", [worker.id for worker in workers])
            form = SiteModelForm(postcopy, instance=site)
            redirect_to = b64_str(request.POST.get("redirect_to"))
            if form.is_valid():
                form.save()
                if redirect_to:
                    messages.success(request, mark_safe(f"Site edited successfully."), extra_tags="success")
                    return redirect(redirect_to)
                else:
                    messages.success(request, mark_safe(f"Site edited successfully. <a href={reverse('sites')}>Back to sites list</a>."), extra_tags="success")
                    return redirect(reverse("sites_view", kwargs={"site_id":form.instance.id}))

        PICs = CustomUserModel.objects.filter(role=CustomUserModel.Roles.PIC)
        site.start_date = site.start_date.strftime("%Y-%m-%d")
        site.expected_end_date = site.expected_end_date.strftime("%Y-%m-%d")
        if site.actual_end_date:
            site.actual_end_date = site.actual_end_date.strftime("%Y-%m-%d")
        return render(request=request, template_name="dashboard/sites/edit.html", context={
            'user': request.user,
            'projects': projects,
            'site': site,
            'pics': PICs,
            'is_site_pic': request.user == site.pic,
            'is_project_director': request.user == site.project.director,
            'higher_than_director': is_left_role_higher_or_equal(request.user.role, CustomUserModel.Roles.DIRECTOR),
            'workers': construct_worker_info(site.workers.all()),
            "formerrors": form.errors if 'form' in locals() and form.errors else None,
        }) 
    else:
        return redirect(reverse("login"))

def sites_delete(request):
    if request.user.is_authenticated:
        if not is_left_role_higher_or_equal(request.user.role, CustomUserModel.Roles.DIRECTOR):
            return redirect(reverse("sites"))
        if request.method == "POST":
            site_id = request.POST.get("site_id")
            site = Site.objects.get(id=site_id)
            workers = site.workers.all()
            helmets = Helmet.objects.filter(user__in=workers)
            for helmet in helmets:
                helmet.user = None
                helmet.save()
            site_name = site.name
            site.delete()
            messages.success(request, mark_safe(f"Site <b>{site_name}</b> deleted successfully."), extra_tags="success")
            redirect_to = b64_str(request.POST.get("redirect_to"))
            if redirect_to:
                return redirect(redirect_to)
            else:
                return redirect(reverse("sites"))
        else:
            return redirect(reverse("sites"))
    else:
        return redirect(reverse("login")) 

def sites_finish(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            site = Site.objects.get(id=request.POST.get("site_id", None))
            if site:
                form = SiteFinishForm(request.POST, instance=site)
                if form.is_valid():
                    form.save()
                    messages.success(request, mark_safe(f"Site <b>{site.name}</b> marked as done."), extra_tags="success")
                else:
                    for field in form.errors:
                        for error in form.errors[field]:
                            messages.error(request, mark_safe(f"{error}"), extra_tags="danger")
                redirect_to = b64_str(request.POST.get("redirect_to"))
                if redirect_to:
                    return redirect(redirect_to)
            return redirect(reverse("sites_view", kwargs={"site_id":site.id}))
        else:
            return redirect(reverse("sites"))
    else:
        return redirect(reverse("login"))

def sites_unfinish(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            site = Site.objects.get(id=request.POST.get("site_id", None))
            if site:
                form = SiteUnfinishForm(request.POST, instance=site)
                if form.is_valid():
                    form.save()
                    messages.success(request, mark_safe(f"Site <b>{site.name}</b> marked as undone."), extra_tags="success")
                else:
                    for field in form.errors:
                        for error in form.errors[field]:
                            messages.error(request, mark_safe(f"{error}"), extra_tags="danger")
                redirect_to = b64_str(request.POST.get("redirect_to"))
                if redirect_to:
                    return redirect(redirect_to)
            return redirect(reverse("sites_view", kwargs={"site_id":site.id}))
        else:
            return redirect(reverse("sites"))
    else:
        return redirect(reverse("login"))

def sites_add_existing_workers(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            worker = CustomUserModel.objects.get(id=request.POST.get("worker_id", None))
            site = Site.objects.get(id=request.POST.get("site_id", None))
            if worker and site:
                try: 
                    WorkerSite.objects.create(worker=worker, site=site)
                    messages.success(request, mark_safe(f"Worker <b>{worker.first_name} {worker.last_name}</b> added to site <b>{site.name}</b>."), extra_tags="success")
                except:
                    messages.error(request, mark_safe(f"Worker <b>{worker.first_name} {worker.last_name}</b> already added to site <b>{site.name}</b>."), extra_tags="danger")
                redirect_to = b64_str(request.POST.get("redirect_to"))
                if redirect_to:
                    return redirect(redirect_to)
                else:
                    return redirect(reverse("sites_view", kwargs={"site_id":site.id}))
        return redirect(reverse("sites"))
    else:
        return redirect(reverse("login"))