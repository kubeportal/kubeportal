import pytest
from django.conf import settings

from kubeportal.models.portalgroup import PortalGroup


@pytest.mark.django_db
def test_single_group_denied(api_client_anon, admin_group):
    response = api_client_anon.get(f'/api/{settings.API_VERSION}/groups/{admin_group.pk}/')
    assert response.status_code == 401


@pytest.mark.django_db
def test_groups_denied(api_client_anon):
    group1 = PortalGroup(name="group1")
    group1.save()
    response = api_client_anon.get(f'/api/{settings.API_VERSION}/groups/{group1.pk}/')
    assert response.status_code == 401


def test_group(api_client, admin_group):
    response = api_client.get(f'/api/{settings.API_VERSION}/groups/{admin_group.pk}/')
    assert response.status_code == 200

    data = response.json()
    assert data['name'] == admin_group.name


def test_group_invalid_id(api_client):
    response = api_client.get(f'/api/{settings.API_VERSION}/groups/777/')
    assert response.status_code == 404


def test_group_non_member(api_client):
    group1 = PortalGroup(name="group1")
    group1.save()
    response = api_client.get(f'/api/{settings.API_VERSION}/groups/{group1.pk}/')
    assert response.status_code == 404