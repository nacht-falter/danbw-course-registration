# Generated by Django 4.2.3 on 2024-04-24 19:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_registration', '0062_remove_internalcourse_discount_rate_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='guestcourseregistration',
            name='payment_method',
            field=models.IntegerField(choices=[(0, 'Bank Transfer'), (1, 'Cash')], default=0),
        ),
        migrations.AlterField(
            model_name='usercourseregistration',
            name='payment_method',
            field=models.IntegerField(choices=[(0, 'Bank Transfer'), (1, 'Cash')], default=0),
        ),
    ]