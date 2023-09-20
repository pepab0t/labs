from django.urls import path
from . import views
from . import api


urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_user, name="login"),
    path("register/", views.register_user, name="register"),
    path("logout/", views.logout_user, name="logout"),
    path("topics/", views.show_topics, name="topics"),
    path("api/topic/all", api.all_topics, name="api_topics"),
    path("api/topic/create", api.new_topic, name="api_new_topic"),
    path("api/topic/delete", api.remove_topic, name="api_remove_topic"),
    path("api/topic/modify", api.modify_topic, name="api_modify_topic"),
]
