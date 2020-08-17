# Generated by Django 2.2.10 on 2020-03-30 12:07

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('kubeportal', '0003_auto_20200326_2224'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='answered_by',
            field=models.ForeignKey(blank=True, help_text='Which user approved the cluster access for this user.', null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Approved by'),
        ),
        migrations.AlterField(
            model_name='user',
            name='comments',
            field=models.CharField(blank=True, default='', max_length=150, null=True),
        ),
        migrations.CreateModel(
            name='PortalGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('auto_add_new', models.BooleanField(default=False, help_text='Enabling this makes all new users automatically a member of this group. Existing users are not modified.', verbose_name='Add all new users automatically')),
                ('auto_add_approved', models.BooleanField(default=False, help_text='Enabling this makes all approved Kubernetes users automatically a member of this group. Existing users are not modified.', verbose_name='Add all approved users automatically')),
                ('can_subauth', models.BooleanField(default=False, help_text='Enabling this allows group members to perform token-based sub-authentication with their Kubernetes account.', verbose_name='Allow sub-authentication for members')),
                ('can_admin', models.BooleanField(default=False, help_text='Enabling this allows group members to access the administrative backend.', verbose_name='Allow administration for members')),
                ('can_web_applications', models.ManyToManyField(blank=True, help_text='Web applications that are accessible for group members.', related_name='portal_groups', to='kubeportal.WebApplication', verbose_name='Web applications')),
            ],
            options={
                'verbose_name': 'User Group',
            },
        ),
        migrations.AddField(
            model_name='user',
            name='portal_groups',
            field=models.ManyToManyField(blank=True, help_text='The user groups this account belongs to.', related_name='members', to='kubeportal.PortalGroup', verbose_name='Groups'),
        ),
    ]
