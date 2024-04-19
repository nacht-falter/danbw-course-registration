# Generated by Django 4.2.3 on 2024-04-15 22:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_registration', '0041_externalcourse_guestregistration_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='course',
            name='description',
        ),
        migrations.AddField(
            model_name='internalcourse',
            name='description',
            field=models.TextField(blank=True),
        ),
    ]