# Generated by Django 2.2.16 on 2020-09-17 15:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kubeportal', '0008_user_alt_mails'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='validity_date',
            field=models.DateField(null=True, verbose_name='Validity date'),
        ),
    ]
