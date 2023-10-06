from django.contrib import admin
<<<<<<< HEAD

# Register your models here.
=======
from .models import CustomUser, LabEvent, LabTopic, LinkTopicEvent

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(LabEvent)
admin.site.register(LabTopic)
admin.site.register(LinkTopicEvent)
>>>>>>> 9e226dca4e55879351b06833d522709091645517
