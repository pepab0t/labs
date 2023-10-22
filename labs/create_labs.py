import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "labs.settings")
import django

django.setup()

from main import models
from django.utils.timezone import make_aware
from datetime import datetime


for d in range(2, 12):
    topic = models.LabTopic.objects.first()
    event = models.LabEvent(
        lab_datetime=make_aware(datetime(2023, 10, d)),
        close_login=make_aware(datetime(2023, 10, d)),
        close_logout=make_aware(datetime(2023, 9, 1)),
    )
    event.save()

    link = models.LinkTopicEvent(event=event, topic=topic)
    link.save()
