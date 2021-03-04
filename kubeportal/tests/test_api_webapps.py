from django.conf import settings

from kubeportal.models.webapplication import WebApplication


def test_single_webapp_denied(api_client_anon, admin_group):
    app1 = WebApplication(name="app1", link_show=True,
                          link_name="app1", link_url="http://www.heise.de")
    app1.save()
    admin_group.can_web_applications.add(app1)

    response = api_client_anon.get(f'/api/{settings.API_VERSION}/webapps/{app1.pk}/')
    assert response.status_code == 401


def test_webapps_denied(api_client_anon, admin_group):
    app1 = WebApplication(name="app1", link_show=True,
                          link_name="app1", link_url="http://www.heise.de")
    app1.save()
    admin_group.can_web_applications.add(app1)

    response = api_client_anon.get(f'/api/{settings.API_VERSION}/webapps/{app1.pk}/')
    assert response.status_code == 401


def test_webapp_user_not_in_group(api_client):
    app1 = WebApplication(name="app1", link_show=True,
                          link_name="app1", link_url="http://www.heise.de")
    app1.save()

    response = api_client.get(f'/api/{settings.API_VERSION}/webapps/{app1.pk}/')
    assert response.status_code == 404


def test_webapp_invalid_id(api_client):
    response = api_client.get(f'/api/{settings.API_VERSION}/webapps/777/')
    assert response.status_code == 404


def test_webapp_invisible(api_client, admin_group):
    app1 = WebApplication(name="app1", link_show=False,
                          link_name="app1", link_url="http://www.heise.de")
    app1.save()
    admin_group.can_web_applications.add(app1)

    response = api_client.get(f'/api/{settings.API_VERSION}/webapps/{app1.pk}/')
    assert response.status_code == 404


def test_webapp(api_client, admin_group):
    app1 = WebApplication(name="app1", link_show=True,
                          link_name="app1", link_url="http://www.heise.de")
    app1.save()
    admin_group.can_web_applications.add(app1)

    response = api_client.get(f'/api/{settings.API_VERSION}/webapps/{app1.pk}/')
    assert response.status_code == 200

    data = response.json()
    assert data['link_name'] == 'app1'
    assert data['link_url'] == 'http://www.heise.de'
    assert data['category'] == "GENERIC"


def test_webapp_placeholders(api_client, admin_group, admin_user_with_k8s_system):
    app1 = WebApplication(name="app1", link_show=True,
                          link_name="app1", link_url="http://www.heise.de/{{{{namespace}}}}/{{{{serviceaccount}}}}")
    app1.save()
    admin_group.can_web_applications.add(app1)

    response = api_client.get(f'/api/{settings.API_VERSION}/webapps/{app1.pk}/')
    assert response.status_code == 200

    data = response.json()
    assert data['link_url'] == 'http://www.heise.de/kube-system/default'