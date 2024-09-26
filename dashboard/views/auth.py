from multiprocessing import AuthenticationError
from wsgiref.simple_server import WSGIRequestHandler
from django.forms import BoundField
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib.auth.forms import AuthenticationForm


def login_request(request: WSGIRequestHandler) -> HttpResponse:
    form: AuthenticationError
    if request.method == "POST":
        try:
            form = AuthenticationForm(request=request, data=request.POST)
            if form.is_valid():
                username: str = form.cleaned_data.get("username")
                password: str = form.cleaned_data.get('password')
                user = authenticate(username=username, password=password)
                if user is not None:
                    login(request, user)
                    return redirect(reverse("dashboard"))
                else:
                    messages.error(request, "Invalid email or password.", extra_tags="danger")
            else:
                messages.error(request, "Invalid email or password.", extra_tags="danger")
        except Exception as e:
            messages.error(request, "Invalid email or password.", extra_tags="danger")
    if request.user.is_authenticated:
        return redirect(reverse("dashboard"))
    form = AuthenticationForm()
    f: BoundField
    for f in form.visible_fields():
        f.field.widget.attrs["class"] = "form-control"
        
    return render(request=request, template_name="dashboard/login.html", context={"login_form":form})

    
def logout_request(request):
    # handle logout via POST
    if request.method == "POST":
        if request.user.is_authenticated:
            logout(request)
    return redirect(reverse("dashboard"))