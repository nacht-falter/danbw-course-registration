# Generated by Django 4.2.3 on 2024-04-16 20:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_registration', '0045_remove_course_organizer_externalcourse_organizer'),
    ]

    operations = [
        migrations.AddField(
            model_name='internalcourse',
            name='organizer',
            field=models.CharField(blank=True, default='DANBW', max_length=200),
        ),
    ]