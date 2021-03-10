import pytest
from django.conf import settings

from kubeportal.api.views import InfoDetailView


@pytest.mark.django_db
def test_cluster_denied(api_client_anon):
    for stat in InfoDetailView.stats.keys():
        response = api_client_anon.get(f'/api/{settings.API_VERSION}/cluster/{stat}/')
        assert response.status_code == 401


def test_cluster(api_client):
    for stat in InfoDetailView.stats.keys():
        response = api_client.get(f'/api/{settings.API_VERSION}/cluster/{stat}/')
        assert 200 == response.status_code
        data = response.json()
        assert stat in data.keys()
        assert data[stat] is not None


def test_cluster_invalid(api_client):
    response = api_client.get(f'/api/{settings.API_VERSION}/cluster/foobar/')
    assert response.status_code == 404