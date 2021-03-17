from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings

from oidc_provider.models import UserConsent
from kubeportal.models.portalgroup import PortalGroup
from kubeportal.models.kubernetesserviceaccount import KubernetesServiceAccount
from kubeportal.models.kubernetesnamespace import KubernetesNamespace
from django.db import connection
from oidc_provider.models import Token, Code
from django.core.exceptions import ObjectDoesNotExist

class Command(BaseCommand):
    '''
        Check for well-known integrity problems in the Kubeportal database.
    '''

    def handle(self, *args, **option):
            try:
                Token.objects.count()
            except:
                print("This is a fresh installation, not database exists. Skipping integrity check.")
                exit(0)
            print("Checking for lost users in OIDC provider tokens ...")
            for token in Token.objects.all():
                try:
                    u = token.user
                except ObjectDoesNotExist:
                    print(f"Missing referenced user for OIDC provider token {token}. Deleting the token object.")
                    token.delete()
            print("Checking for lost users in OIDC provider codes ...")
            for code in Code.objects.all():
                try:
                    u = code.user
                except ObjectDoesNotExist:
                    print(f"Missing referenced user for OIDC provider code {code}. Deleting the code object.")
                    code.delete()
            print("Checking for lost users in OpenID consents ...")
            for consent in UserConsent.objects.all():
                try:
                    u = consent.user
                except ObjectDoesNotExist:
                    print(f"Missing referenced user for OpenID consent {consent}. Deleting the consent object.")
                    consent.delete()
            print("Checking for lost users in portal groups ...")
            for group in PortalGroup.objects.all():
                for entry in group.members.through.objects.all():
                    try:
                        u = entry.user
                    except ObjectDoesNotExist:
                        print(f"Missing referenced user for group / user relation {entry}. Deleting the relation object.")
                        entry.delete()
            print("Deleting obsolete social auth tables ...")
            with connection.cursor() as cursor:
                for table in ["social_auth_usersocialauth", "social_auth_partial", "social_auth_nonce", "social_auth_code", "social_auth_association"]:
                    try:
                        cursor.execute(f"drop table {table};")
                    except:
                        pass # table already gone
            print("Checking for lost namespaces in Kubernetes service accounts ...")
            # The manager crashes on the normal "objects.all()" access, so we use the ID-based reference check here
            for entry in KubernetesServiceAccount.objects.values():
                try:
                    ns = KubernetesNamespace.objects.get(pk=entry['namespace_id'])
                except:
                    print(f"Missing referenced namespace for service account {entry}. Deleting the service account object.")
                    broken_svca = KubernetesServiceAccount.objects.get(pk=entry['id'])
                    broken_svca.delete()
            print("Check for default portal groups ...")
            has_admin_group = PortalGroup.objects.filter(can_admin=True).exists()
            if not has_admin_group:
                print("Creating missing default group 'Admin users")
                admin_group = PortalGroup(name="Admin users", can_admin=True)
                admin_group.save()
