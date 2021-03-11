import json

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
    assert data[0]["author"].endswith(f"/{admin_user.pk}/")
