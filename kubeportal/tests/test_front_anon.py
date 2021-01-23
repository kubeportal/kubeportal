import pytest
from kubeportal.models.webapplication import WebApplication

@pytest.mark.django_db
def test_index_view(client):
    response = client.get('/', follow=True)
    assert response.status_code == 200


@pytest.mark.django_db
def test_subauth_view_nonexistent_app(client):
    response = client.get('/subauthreq/42/')
    assert response.status_code == 404


@pytest.mark.django_db
def test_subauth_view_existent_app(client):
    app1 = WebApplication(name="app1")
    app1.save()
    response = client.get('/subauthreq/{}/'.format(app1.pk))
    assert response.status_code == 401


@pytest.mark.django_db
def test_django_secret_generation(client, mocker):
    with mocker.patch('os.path.isfile', return_value=False):
        response = client.get('/stats/')
        assert response.status_code == 302
