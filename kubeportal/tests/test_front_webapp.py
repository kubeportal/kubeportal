from kubeportal.models.portalgroup import PortalGroup
from kubeportal.models.webapplication import WebApplication
from kubeportal.tests import AdminLoggedInTestCase


class FrontendLoggedInWebApp(AdminLoggedInTestCase):
    '''
    Tests for frontend functionality when admin is logged in,
    and sees some web applications.
    '''

    def setUp(self):
        super().setUp()

    def test_webapp_user_not_in_group(self):
        app1 = WebApplication(name="app1", link_show=True,
                              link_name="app1", link_url="http://www.heise.de")
        app1.save()
        response = self.c.get('/welcome/')
        # User is not in a group that has this web app enabled
        self.assertNotContains(response, "http://www.heise.de")

    def test_webapp_user_in_group(self):
        app1 = WebApplication(name="app1", link_show=True,
                              link_name="app1", link_url="http://www.heise.de")
        app1.save()
        group = PortalGroup()
        group.save()
        self.admin.portal_groups.add(group)
        response = self.c.get('/welcome/')
        # User is in group, but this group has the web app not enabled
        self.assertNotContains(response, "http://www.heise.de")

        group.can_web_applications.add(app1)
        response = self.c.get('/welcome/')
        # User is now in a group that has this web app enabled
        self.assertContains(response, "http://www.heise.de")
        self.assertEquals(1, str(response.content).count("http://www.heise.de"))

        app1.link_show = False
        app1.save()
        response = self.c.get('/welcome/')
        # User is now in a group that has this web app, but disabled
        self.assertNotContains(response, "http://www.heise.de")

    def test_webapp_user_in_multiple_groups(self):
        app1 = WebApplication(name="app1", link_show=True,
                              link_name="app1", link_url="http://www.heise.de")
        app1.save()
        group1 = PortalGroup()
        group1.save()
        group1.can_web_applications.add(app1)
        group2 = PortalGroup()
        group2.save()
        group2.can_web_applications.add(app1)
        self.admin.portal_groups.add(group1)
        self.admin.portal_groups.add(group2)
        response = self.c.get('/welcome/')
        self.assertContains(response, "http://www.heise.de")
        self.assertEquals(1, str(response.content).count("http://www.heise.de"))
