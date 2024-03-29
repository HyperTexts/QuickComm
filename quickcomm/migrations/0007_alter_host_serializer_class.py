# Generated by Django 4.1.7 on 2023-04-03 08:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quickcomm', '0006_post_recipient_alter_post_visibility'),
    ]

    operations = [
        migrations.AlterField(
            model_name='host',
            name='serializer_class',
            field=models.CharField(choices=[('THTH', 'Too Hot To Hindle (Group 2)'), ('INTERNAL', 'Internal Default'), ('GROUP1', 'Group 1'), ('MATTGROUP', "Matt's Group")], default='INTERNAL', help_text='The serializer class to use for the host. This is used to determine which serializer to use when interacting with the host.', max_length=100, verbose_name='Serializer Class'),
        ),
    ]
