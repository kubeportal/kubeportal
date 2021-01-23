from kubeportal.models.portalgroup import PortalGroup
from kubeportal.models.webapplication import WebApplication


def contains(response, text):
    return text in str(response.content)


def test_webapp_user_not_in_group(admin_client):
    app1 = WebApplication(name="app1", link_show=True,
                          link_name="app1", link_url="http://www.heise.de")
    app1.save()
    response = admin_client.get('/welcome/')
    # User is not in a group that has this web app enabled
    assert not contains(response, "http://www.heise.de")


def test_webapp_user_in_group(admin_client, admin_user):
    app1 = WebApplication(name="app1", link_show=True,
                          link_name="app1", link_url="http://www.heise.de")
    app1.save()
    group = PortalGroup()
    group.save()
    admin_user.portal_groups.add(group)
    response = admin_client.get('/welcome/')
    # User is in group, but this group has the web app not enabled
    assert not contains(response, "http://www.heise.de")

    group.can_web_applications.add(app1)
    response = admin_client.get('/welcome/')
    # User is now in a group that has this web app enabled
    assert contains(response, "http://www.heise.de")
    assert 1 == str(response.content).count("http://www.heise.de")

    app1.link_show = False
    app1.save()
    response = admin_client.get('/welcome/')
    # User is now in a group that has this web app, but disabled
    assert not contains(response, "http://www.heise.de")


def test_webapp_user_in_multiple_groups(admin_client, admin_user):
    app1 = WebApplication(name="app1", link_show=True,
                          link_name="app1", link_url="http://www.heise.de")
    app1.save()
    group1 = PortalGroup()
    group1.save()
    group1.can_web_applications.add(app1)
    group2 = PortalGroup()
    group2.save()
    group2.can_web_applications.add(app1)
    admin_user.portal_groups.add(group1)
    admin_user.portal_groups.add(group2)
    response = admin_client.get('/welcome/')
    assert contains(response, "http://www.heise.de")
    assert 1 == str(response.content).count("http://www.heise.de")
