# Generated by Django 4.2 on 2023-09-23 17:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_customuser_cancelled'),
    ]

    operations = [
        migrations.AddField(
            model_name='linktopicevent',
            name='date',
            field=models.DateTimeField(auto_now=True),
        ),
    ]