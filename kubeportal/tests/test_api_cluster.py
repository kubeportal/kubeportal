import pytest
from django.conf import settings
from kubeportal.tests.helpers import minikube_unavailable
from kubeportal.api.views import InfoDetailView


@pytest.mark.django_db
def test_cluster_denied(api_client_anon):
    for stat in InfoDetailView.stats.keys():
        response = api_client_anon.get(f'/api/{settings.API_VERSION}/infos/{stat}/')
        assert response.status_code == 401


@pytest.mark.skipif(minikube_unavailable(), reason="Minikube is unavailable")
def test_cluster(api_client):
    for stat in InfoDetailView.stats.keys():
        response = api_client.get(f'/api/{settings.API_VERSION}/infos/{stat}/')
        assert 200 == response.status_code
        data = response.json()
        assert stat in data.keys()
        assert data[stat] is not None


def test_cluster_invalid(api_client):
    response = api_client.get(f'/api/{settings.API_VERSION}/infos/foobar/')
    assert response.status_code == 404