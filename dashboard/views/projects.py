from django.shortcuts import redirect, render
from django.urls import reverse
from dashboard.forms import ProjectFinishForm, ProjectModelForm, ProjectUnfinishForm
from dashboard.helper.util import b64_str, is_left_role_higher_or_equal
from dashboard.models import CustomUserModel, Helmet, Project, Site
from django.contrib import messages
from django.utils.safestring import mark_safe


def projects_list(request):
    if request.user.is_authenticated:
        if request.user.role == CustomUserModel.Roles.ADMIN:
            projects = Project.objects.all()
            sites = Site.objects.all()
        elif request.user.role == CustomUserModel.Roles.DIRECTOR:
            projects = Project.objects.filter(director=request.user)
            sites = Site.objects.filter(project__in=projects)
        else:
            return redirect(reverse("dashboard"))
        return render(request=request, template_name="dashboard/projects/list.html", context={
            "user":request.user, 
            "projects":projects,
            "sites": sites
        }) 
    else:
        return redirect(reverse("login"))

def projects_add(request):
    if request.user.is_authenticated:
        if not is_left_role_higher_or_equal(request.user.role, CustomUserModel.Roles.ADMIN):
            return redirect(reverse("projects"))
        if request.method == "POST":
            form = ProjectModelForm(request.POST)
            redirect_to = b64_str(request.POST.get("redirect_to"))
            if form.is_valid():
                form.save()
                if redirect_to:
                    messages.success(request, mark_safe("Project added successfully"), extra_tags="success")
                    return  redirect(redirect_to)
                else:
                    messages.success(request, mark_safe(f"Project added successfully. <a href={reverse('projects')}>Back to projects list</a>."), extra_tags="success")
                    return redirect(reverse("projects_view", kwargs={"project_id":form.instance.id}))
        return render(request=request, template_name="dashboard/projects/add.html", context={
            'user': request.user,
            'directors': CustomUserModel.objects.filter(role=CustomUserModel.Roles.DIRECTOR),
            'formerrors': form.errors if 'form' in locals() and form.errors else None,
        }) 
    else:
        return redirect(reverse("login"))

def projects_edit(request, project_id):
    if request.user.is_authenticated:
        project = Project.objects.get(id=project_id)
        if is_left_role_higher_or_equal(request.user.role, CustomUserModel.Roles.ADMIN) or request.user == project.director: 
            if request.method == "POST":
                form = ProjectModelForm(request.POST, instance=project)
                redirect_to = b64_str(request.POST.get("redirect_to"))
                if form.is_valid():
                    form.save()
                    if redirect_to:
                        messages.success(request, mark_safe("Project edited successfully"), extra_tags="success")
                        return redirect(redirect_to)
                    else:
                        messages.success(request, mark_safe(f"Project edited successfully. <a href={reverse('projects')}>Back to projects list</a>."), extra_tags="success")
                        return redirect(reverse("projects_view", kwargs={"project_id":form.instance.id}))
            sites_inside_this_project = Site.objects.filter(project=project)
            project.start_date = project.start_date.strftime("%Y-%m-%d")
            project.expected_end_date = project.expected_end_date.strftime("%Y-%m-%d")
            try:
                project.end_date = project.end_date.strftime("%Y-%m-%d")
            except:
                pass
            return render(request=request, template_name="dashboard/projects/edit.html", context={
                'user': request.user,
                'directors': CustomUserModel.objects.filter(role=CustomUserModel.Roles.DIRECTOR),
                'project': project,
                'sites': sites_inside_this_project,
                'not_admin': not is_left_role_higher_or_equal(request.user.role, CustomUserModel.Roles.ADMIN),
                'formerrors': form.errors if 'form' in locals() and form.errors else None,
            }) 
        else:
            return redirect(reverse("projects_view", kwargs={"project_id":project_id}))
    else:
        return redirect(reverse("login"))

def projects_view(request, project_id):
    if request.user.is_authenticated:
        project = Project.objects.get(id=project_id)
        sites_inside_this_project = Site.objects.filter(project=project).order_by('-start_date')
        return render(request=request, template_name="dashboard/projects/view.html", context={
            'user': request.user,
            'project': project,
            'counts': {
                "sites": sites_inside_this_project.count(),
                "workers": sum([site.workers.count() for site in sites_inside_this_project]),
            },
            'can_edit': not project.actual_end_date and (is_left_role_higher_or_equal(request.user.role, CustomUserModel.Roles.ADMIN) or request.user == project.director),
            'can_delete': is_left_role_higher_or_equal(request.user.role, CustomUserModel.Roles.ADMIN),
            'can_mark_as_done': not project.actual_end_date and (is_left_role_higher_or_equal(request.user.role, CustomUserModel.Roles.ADMIN) or request.user == project.director),
            'can_unmark_as_done': project.actual_end_date and (is_left_role_higher_or_equal(request.user.role, CustomUserModel.Roles.ADMIN) or request.user == project.director),
            'CustomUserModel.Roles': CustomUserModel.Roles,
            'sites': sites_inside_this_project,
        }) 
    else:
        return redirect(reverse("login"))


def projects_delete(request):
    if request.user.is_authenticated:
        if request.method == "POST" and is_left_role_higher_or_equal(request.user.role, CustomUserModel.Roles.ADMIN):
            project_id = request.POST.get("project_id")
            workers = CustomUserModel.objects.filter(
                workersite__site__project__id=project_id,
                role=CustomUserModel.Roles.WORKER
            )
            helmets = Helmet.objects.filter(
                user__in=workers
            )
            for helmet in helmets:
                helmet.user = None
                helmet.save()
            project = Project.objects.get(id=project_id)
            project_name = project.name
            project.delete()
            messages.success(request, mark_safe(f"Project <b>{project_name}</b> deleted successfully."), extra_tags="success")
            redirect_to = b64_str(request.POST.get("redirect_to"))
            if redirect_to:
                return redirect(redirect_to)
            else:
                return redirect(reverse("projects"))
        return redirect(reverse("projects"))
    else:
        return redirect(reverse("login"))


def projects_finish(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            project = Project.objects.get(id=request.POST.get("project_id", None))
            if project:
                form = ProjectFinishForm(request.POST, instance=project)
                if form.is_valid():
                    form.save()
                    messages.success(request, mark_safe(f"Project <b>{project.name}</b> marked as finished successfully."), extra_tags="success")
                else:
                    for error in form.errors:
                        messages.error(request, mark_safe(f"{error}: {form.errors[error]}"), extra_tags="danger")
                redirect_to = b64_str(request.POST.get("redirect_to"))
                if redirect_to:
                    return redirect(redirect_to)
                else:
                    return redirect(reverse("projects_view", kwargs={"project_id":project.id}))
        return redirect(reverse("projects"))
    else:
        return redirect(reverse("login"))

def projects_unfinish(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            project = Project.objects.get(id=request.POST.get("project_id", None))
            if project:
                form = ProjectUnfinishForm(request.POST, instance=project)
                if form.is_valid():
                    form.save()
                    messages.success(request, mark_safe(f"Project <b>{project.name}</b> marked as unfinished successfully."), extra_tags="success")
                else:
                    for error in form.errors:
                        messages.error(request, mark_safe(f"{error}: {form.errors[error]}"), extra_tags="danger")
                redirect_to = b64_str(request.POST.get("redirect_to"))
                if redirect_to:
                    return redirect(redirect_to)
                else:
                    return redirect(reverse("projects_view", kwargs={"project_id":project.id}))
        return redirect(reverse("projects"))
    else:
        return redirect(reverse("login"))