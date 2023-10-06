from django.urls import path
from . import views
from . import api


urlpatterns = [
    path("create_fake_users/", views.create_users, name="create_fake_users"),
    path("", views.home, name="home"),
    path("login/", views.login_user, name="login"),
    path("register/", views.register_user, name="register"),
    path("logout/", views.logout_user, name="logout"),
    path("topics/", views.show_topics, name="topics"),
    path("event/create", views.create_event, name="create_event"),
    path("event/<int:id>", views.event_page, name="apply_event"),
    path("event/delete/<int:event_id>", views.delete_event, name="delete_event"),
    path("approve/", views.approve_registration_page, name="approve_page"),
    path("my_labs/", views.my_labs, name="my_labs"),
    path("export/", views.export_page, name="export"),
    path("api/topic/all", api.all_topics, name="api_topics"),
    path("api/topic/create", api.new_topic, name="api_new_topic"),
    path("api/topic/delete", api.remove_topic, name="api_remove_topic"),
    path("api/topic/modify", api.modify_topic, name="api_modify_topic"),
    path("api/event/all", api.get_lab_events, name="api_events"),
    path("api/approve/<int:id>", api.approve_user, name="api_approve_user"),
    path("api/decline/<int:id>", api.decline_user, name="api_decline_user"),
    path(
        "api/event/<int:event_id>/user/<int:user_id>",
        api.remove_user_from_event,
        name="api_remove_user_from_event",
    ),
    path("api/export/closed", api.export_closed, name="api_export_closed"),
    path("api/export/history", api.export_history, name="api_export_history"),
    path("api/requests/", api.get_reqister_requests, name="api_register_requests"),
]
