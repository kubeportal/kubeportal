import json
from django.conf import settings
from kubeportal.models.portalgroup import PortalGroup
from kubeportal.models.webapplication import WebApplication
import pytest
from kubeportal.tests.helpers import minikube_unavailable


@pytest.mark.skipif(minikube_unavailable(), reason="Minikube is unavailable")
def test_user(api_client, admin_user_with_k8s_system):
    webapp1 = WebApplication(name="webapp1", link_show=True)
    webapp1.save()
    group1 = PortalGroup(name="group1")
    group1.save()
    group1.can_web_applications.add(webapp1)
    group1.save()
    admin_user_with_k8s_system.portal_groups.add(group1)

    user_attr_expected = [
        'firstname',
        'name',
        'username',
        'user_id',
        'primary_email',
        'all_emails',
        'admin',
        'serviceaccount_urls',
        'k8s_token',
        'webapp_urls',
        'group_urls'
    ]

    response = api_client.get(f'/api/{settings.API_VERSION}/users/{admin_user_with_k8s_system.pk}/')
    assert response.status_code == 200
    data = response.json()

    assert True is data['admin']

    for key in user_attr_expected:
        assert key in data

    assert len(data["group_urls"]) > 0   # all users group, at least
    assert len(data["serviceaccount_urls"]) > 0
    assert data['all_emails'] == ['admin@example.com']
    assert data['serviceaccount_urls'][0].startswith("http://testserver")
    assert data['group_urls'][0].startswith("http://testserver")


def test_patch_user(api_client, admin_user):
    data_mock = {"primary_email": "foo@bar.de"}

    response = api_client.patch(f'/api/{settings.API_VERSION}/users/{admin_user.pk}/', data_mock)

    updated_primary_email = json.loads(response.text)['primary_email']
    assert updated_primary_email == data_mock['primary_email']
    assert response.status_code == 200


def test_user_all_email_adrs(api_client, admin_user):
    admin_user.email = "a@b.de"
    admin_user.alt_mails = ["c@d.de", "e@f.de"]
    admin_user.save()

    response = api_client.get(f'/api/{settings.API_VERSION}/users/{admin_user.pk}/')

    all_emails = json.loads(response.text)['all_emails']
    assert all_emails == ["a@b.de", "c@d.de", "e@f.de"]
    assert response.status_code == 200


def test_user_all_email_adrs_empty_alt(api_client, admin_user):
    admin_user.alt_mails = None
    admin_user.save()

    response = api_client.get(f'/api/{settings.API_VERSION}/users/{admin_user.pk}/')

    all_emails = json.loads(response.text)['all_emails']
    assert all_emails == ["admin@example.com"]
    assert response.status_code == 200


def test_patch_user_invalid_id(api_client):
    response = api_client.patch(f'/api/{settings.API_VERSION}/users/777/', {})
    assert response.status_code == 404


def test_patch_user_not_himself(api_client, second_user):
    response = api_client.patch(f'/api/{settings.API_VERSION}/users/{second_user.pk}/', {})
    assert response.status_code == 404


def test_user_invalid_id(api_client):
    response = api_client.get(f'/api/{settings.API_VERSION}/users/777/')
    assert response.status_code == 404


def test_get_user_not_himself(api_client, second_user):
    response = api_client.get(f'/api/{settings.API_VERSION}/users/{second_user.pk}/')
    assert response.status_code == 200
    data = json.loads(response.text)
    assert len(data.keys()) == 3
    assert 'k8s_token' not in data.keys()
    assert 'firstname' in data.keys()
    assert data['firstname'] == second_user.first_name

def test_no_general_user_list(api_client):
    response = api_client.get(f'/api/{settings.API_VERSION}/users/')
    assert response.status_code == 404


def test_user_services_list_no_k8s(api_client):
    response = api_client.post(f'/api/{settings.API_VERSION}/namespaces/default/services/')
    assert 404 == response.status_code


def test_get_approval_information(api_client, admin_user):
    response = api_client.get(f'/api/{settings.API_VERSION}/users/{admin_user.pk}/approval/')
    assert response.status_code == 200
    data = response.json()

    assert data['state'] == admin_user.state
    assert data['approving_admin_urls'][0].endswith(f"{admin_user.pk}/")


def test_apply_for_approval(api_client, admin_user):
    assert admin_user.state == "NEW"
    response = api_client.get(f'/api/{settings.API_VERSION}/users/{admin_user.pk}/approval/')
    assert response.status_code == 200
    data = response.json()
    admin_url = data['approving_admin_urls'][0]

    # Admin tries to approve himself
    response = api_client.post(f'/api/{settings.API_VERSION}/users/{admin_user.pk}/approval/', {'approving_admin_url': admin_url })

    assert response.status_code == 202

    admin_user.refresh_from_db()

    assert admin_user.state == "ACCESS_REQUESTED"
