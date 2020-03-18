# Generated by Django 2.2.10 on 2020-03-18 20:57

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oidc_provider', '0026_client_multiple_response_types'),
        ('kubeportal', '0002_auto_20200224_1637'),
    ]

    operations = [
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('members', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
                ('oidc_clients', models.ManyToManyField(to='oidc_provider.Client')),
            ],
        ),
    ]
