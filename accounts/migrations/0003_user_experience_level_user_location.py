# Generated by Django 5.2.3 on 2025-06-24 21:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_resume'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='experience_level',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='location',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
