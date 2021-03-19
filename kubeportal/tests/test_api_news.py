import json
from urllib.parse import urlparse

from django.conf import settings

from kubeportal.models.news import News


def test_news_list(api_client, admin_user):
    test_news = News(content="<p>Hello World</p>", title="Foo", author=admin_user)
    test_news.save()

    response = api_client.get(f'/api/{settings.API_VERSION}/news/')
    assert 200 == response.status_code
    data = json.loads(response.content)
    assert "<p>Hello World</p>" == data[0]["content"]
    assert "Foo" == data[0]["title"]
    assert data[0]["author_url"].endswith(f"/{admin_user.pk}/")

def test_foreign_news_author(api_client, admin_user, second_user):
    test_news = News(content="<p>Hello World</p>", title="Foo", author=second_user)
    test_news.save()

    response = api_client.get(f'/api/{settings.API_VERSION}/news/')
    assert response.status_code == 200
    data = json.loads(response.content)

    relative_author_url = urlparse(data[0]['author_url']).path
    response = api_client.get(relative_author_url)
    assert response.status_code == 200
    data = json.loads(response.text)
    assert len(data.keys()) == 3
    assert 'k8s_token' not in data.keys()
    assert 'firstname' in data.keys()
    assert data['firstname'] == second_user.first_name