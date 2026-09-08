from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("login/", LoginView.as_view(template_name="dashboard/login.html", redirect_authenticated_user=True), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("", views.home, name="home"),
    path("knowledge/", views.knowledge_page, name="knowledge"),
    path("knowledge/<int:pk>/delete/", views.knowledge_delete, name="knowledge_delete"),
    path("knowledge/<int:pk>/toggle/", views.knowledge_toggle, name="knowledge_toggle"),
    path("knowledge/rebuild/", views.knowledge_rebuild, name="knowledge_rebuild"),
    path("questions/", views.questions_page, name="questions"),
    path("questions/export/", views.questions_export, name="questions_export"),
]
