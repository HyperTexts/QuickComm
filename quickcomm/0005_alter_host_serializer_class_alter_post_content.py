# Generated by Django 4.1.7 on 2023-04-02 01:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quickcomm', '0004_alter_comment_content_type_followrequest'),
    ]

    operations = [
        migrations.AlterField(
            model_name='host',
            name='serializer_class',
            field=models.CharField(choices=[('THTH', 'Too Hot To Hindle (Group 2)'), ('INTERNAL', 'Internal Default'), ('GROUP1', 'Group 1')], default='INTERNAL', help_text='The serializer class to use for the host. This is used to determine which serializer to use when interacting with the host.', max_length=100, verbose_name='Serializer Class'),
        ),
        migrations.AlterField(
            model_name='post',
            name='content',
            field=models.CharField(max_length=1000000000),
        ),
    ]
