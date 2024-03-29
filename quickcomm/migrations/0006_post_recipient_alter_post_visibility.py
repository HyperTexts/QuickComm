# Generated by Django 4.1.7 on 2023-04-02 22:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quickcomm', '0005_registrationsettings_allow_api_access_without_login_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='recipient',
            field=models.UUIDField(editable=False, null=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='visibility',
            field=models.CharField(max_length=50),
        ),
    ]
