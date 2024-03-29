# Generated by Django 4.1.7 on 2023-03-24 08:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quickcomm', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='host',
            name='serializer_class',
            field=models.CharField(choices=[('THTH', 'Too Hot To Hindle (Group 2)'), ('INTERNAL', 'Internal Default')], default='INTERNAL', help_text='The serializer class to use for the host. This is used to determine which serializer to use when interacting with the host.', max_length=100, verbose_name='Serializer Class'),
        ),
    ]
