from django.db import models
from oidc_provider.models import Client


class WebApplication(models.Model):
    """
    A web application protected and / or linked by KubePortal.
    """
    CATEGORIES = [
        ("GENERIC", "Generic"),
        ("DOCUMENTATION", "Documentation"),
        ("COMMUNICATION", "Communication"),
        ("KUBERNETES", "Kubernetes"),
        ("DEVELOPER", "Developer"),
        ("DATABASE", "Database"),
        ("MONITORING", "Monitoring")
    ]


    name = models.CharField(max_length=100)
    category = models.CharField(
        max_length=255, 
        choices=CATEGORIES, 
        default="GENERIC",
        help_text="Category of the web application, impacts the visual representation on the frontend.")
    link_show = models.BooleanField(
        verbose_name="Show link",
        default=False,
        help_text="Show link on the landing page when user has access rights.")
    link_name = models.CharField(
        null=True, blank=True,
        verbose_name="Link title",
        help_text="The title of the link on the landing page. You can use the placeholders '{{namespace}}' and '{{serviceaccount}}'.", max_length=100)
    link_url = models.URLField(
        null=True, blank=True,
        verbose_name="Link URL",
        help_text="The URL of the link on the landing page. You can use the placeholders '{{namespace}}' and '{{serviceaccount}}'.")
    oidc_client = models.OneToOneField(
        Client, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="OpenID Connect Client")
    can_subauth = models.BooleanField(
        verbose_name="Enable sub-authentication URL",
        help_text="Enables an URL to allow proxy sub-authentication for this web application.",
        default=False)

    class Meta:
        verbose_name = 'web application'

    def __str__(self):
        return self.name
