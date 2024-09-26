from django.urls import path

from dashboard.views import dbg
from .views import (
    auth, dashboard, workers, projects,
    sites, helmets, profile
)

urlpatterns = [
    path('login/', auth.login_request, name='login'),
    path('logout/', auth.logout_request, name='logout'),
    path('', dashboard.dashboard_request, name='dashboard'),
    # workers
    path('workers/', workers.workers_list, name='workers'),
    path('workers/add/', workers.workers_add, name='workers_add'),
    path('workers/<int:worker_id>/edit', workers.workers_edit, name='workers_edit'),
    path('workers/<int:worker_id>/change_password', workers.workers_change_password, name='workers_change_password'),
    path('workers/delete/', workers.workers_delete, name='workers_delete'),
    path('workers/notifications', workers.workers_notifications, name='workers_notifications'),
    path('workers/send_help', workers.workers_send_help, name='workers_send_help'),
    # projects
    path('projects/', projects.projects_list, name='projects'),
    path('projects/add/', projects.projects_add, name='projects_add'),
    path('projects/<int:project_id>/edit/', projects.projects_edit, name='projects_edit'),
    path('projects/<int:project_id>/', projects.projects_view, name='projects_view'),
    path('projects/delete/', projects.projects_delete, name='projects_delete'),
    path('projects/finish/', projects.projects_finish, name='projects_finish'),
    # sites
    path('sites/', sites.sites_list, name='sites'),
    path('sites/add/', sites.sites_add, name='sites_add'),
    path('sites/<int:site_id>/', sites.sites_view, name='sites_view'),
    path('sites/<int:site_id>/edit/', sites.sites_edit, name='sites_edit'),
    path('sites/delete/', sites.sites_delete, name='sites_delete'),
    path('sites/finish/', sites.sites_finish, name='sites_finish'),
    path('sites/addworker/', sites.sites_add_existing_workers, name='sites_add_existing_workers'),
    # helmets
    path('helmets/', helmets.helmets_list, name='helmets'),
    path('helmets/add/', helmets.helmets_add, name='helmets_add'),
    path('helmets/delete/', helmets.helmets_delete, name='helmets_delete'),
    path('helmets/<str:identifier>/', helmets.helmets_view, name='helmets_view'),
    path('helmets/<str:identifier>/edit/', helmets.helmets_edit, name='helmets_edit'),
    path('helmets/notification/done/', helmets.helmets_notification_done, name='helmets_notification_done'),

    # profile
    path('profile/<int:user_id>/', profile.profile_view, name='profile_view'),
    path('profile/<int:user_id>/edit/', profile.profile_edit, name='profile_edit'),
    path('profile/<int:user_id>/change_password/', profile.profile_change_password, name='profile_change_password'),

    # dbg
    path('dbg/camera/', dbg.camera, name='dbg_camera'),
    path('dbg/stream/<str:identifier>/', dbg.jpeg, name='dbg_jpeg'),
]
