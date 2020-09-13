# Generated by Django 2.2.10 on 2020-04-01 10:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('kubeportal', '0004_auto_20200330_1207'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='portalgroup',
            name='can_subauth',
        ),
        migrations.AddField(
            model_name='webapplication',
            name='can_subauth',
            field=models.BooleanField(default=False, help_text='Enables an URL to allow proxy sub-authentication for this web application.', verbose_name='Enable sub-authentication URL'),
        ),
        migrations.AlterField(
            model_name='portalgroup',
            name='auto_add_approved',
            field=models.BooleanField(default=False, help_text='Enabling this makes all newly approved Kubernetes users automatically a member of this group. Existing users are not modified. Users with cluster approval being removed stay in this group.', verbose_name='Auto-add approved users'),
        ),
        migrations.AlterField(
            model_name='portalgroup',
            name='auto_add_new',
            field=models.BooleanField(default=False, help_text='Enabling this makes all newly created users automatically a member of this group. Existing users are not modified.', verbose_name='Auto-add new users'),
        ),
        migrations.AlterField(
            model_name='portalgroup',
            name='can_admin',
            field=models.BooleanField(default=False, help_text='Enabling this allows members of this group to access the administrative backend.', verbose_name='Backend access'),
        ),
        migrations.AlterField(
            model_name='portalgroup',
            name='can_web_applications',
            field=models.ManyToManyField(blank=True, help_text='Web applications that are accessible for members of this group.', related_name='portal_groups', to='kubeportal.WebApplication', verbose_name='Web applications'),
        ),
        migrations.AlterField(
            model_name='webapplication',
            name='link_name',
            field=models.CharField(blank=True, help_text="The title of the link on the landing page. You can use the placeholders '{{namespace}}' and '{{serviceaccount}}'.", max_length=100, null=True, verbose_name='Link title'),
        ),
        migrations.AlterField(
            model_name='webapplication',
            name='link_show',
            field=models.BooleanField(default=False, help_text='Show link on the landing page when user has access rights.', verbose_name='Show link'),
        ),
        migrations.AlterField(
            model_name='webapplication',
            name='link_url',
            field=models.URLField(blank=True, help_text="The URL of the link on the landing page. You can use the placeholders '{{namespace}}' and '{{serviceaccount}}'.", null=True, verbose_name='Link URL'),
        ),
        migrations.AlterField(
            model_name='webapplication',
            name='oidc_client',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='oidc_provider.Client', verbose_name='OpenID Connect Client'),
        ),
    ]
