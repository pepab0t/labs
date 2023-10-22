from django.contrib import admin
from .models import CustomUser, LabEvent, LabTopic, LinkTopicEvent

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(LabEvent)
admin.site.register(LabTopic)
admin.site.register(LinkTopicEvent)
