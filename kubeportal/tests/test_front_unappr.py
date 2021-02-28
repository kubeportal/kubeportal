"""
Tests for the (classic) portal frontend, assuming that a user is logged in.
"""

from django.urls import reverse

from kubeportal.models.portalgroup import PortalGroup
from kubeportal.models.webapplication import WebApplication
from kubeportal.k8s import kubernetes_api as api
from kubeportal.tests.helpers import run_minikube_sync
from pytest_django.asserts import assertRedirects
import re


def test_index_view(admin_client):
    # User is already logged in, expecting welcome redirect
    response = admin_client.get('/')
    assert response.status_code == 302


def test_welcome_view(admin_client):
    response = admin_client.get('/welcome/')
    assert response.status_code == 200


def test_config_view(admin_client):
    response = admin_client.get(reverse('config'))
    assert response.status_code == 200


def test_config_download_view(admin_client):
    response = admin_client.get(reverse('config_download'))
    assert response.status_code == 200


def test_stats_view(admin_client):
    response = admin_client.get('/stats/')
    assert response.status_code == 200


def test_root_redirect_with_next_param(admin_client):
    response = admin_client.get('/?next=/config')
    assert response.status_code == 302


def test_root_redirect_with_rd_param(admin_client):
    response = admin_client.get('/?next=/config')
    assert response.status_code == 302


def test_approval_mail(admin_client, admin_user, client, second_user, mailoutbox):
    # send approval request from non-admin user
    client.force_login(second_user)
    response = client.post('/access/request/', {'selected-administrator': admin_user.username})
    assertRedirects(response, '/config/')
    # check mail to admin
    assert len(mailoutbox) == 1
    m = mailoutbox[0]
    assert m.subject == 'Request for access to "KubePortal"'
    assert f'user "{second_user.username}" requests access to the KubePortal' in m.body
    approval_url = re.search('.*http://.*', m.body)[0]
    assert str(second_user.approval_id) in approval_url
    # call approval web page as admin
    response = admin_client.get(approval_url)
    assert response.status_code == 200
    response_content = re.search('<table.*', str(response.content))[0]
    assert f"<td>Username:</td><td>{second_user.username}</td>" in response_content

def test_approval_create_new(admin_client, admin_user, client, second_user, mailoutbox, random_namespace_name):
    client.force_login(second_user)
    assert second_user.state == second_user.NEW
    response = client.post('/access/request/', {'selected-administrator': admin_user.username})
    assertRedirects(response, '/config/')
    second_user.refresh_from_db()
    assert second_user.state == second_user.ACCESS_REQUESTED
    approval_url = f"/admin/kubeportal/user/{second_user.approval_id}/approve/"
    # Perform approval with new namespace as admin
    response = admin_client.post(approval_url, {'choice': 'approve_create', 'approve_create_name': random_namespace_name, 'comments': ''})
    assertRedirects(response, '/admin/kubeportal/user/')
    second_user.refresh_from_db()
    assert second_user.k8s_namespace().name == random_namespace_name
    assert second_user.state == second_user.ACCESS_APPROVED
    assert second_user.answered_by != None


def test_approval_create_existing(admin_client, admin_user, client, second_user, mailoutbox):
    client.force_login(second_user)
    assert second_user.state == second_user.NEW
    response = client.post('/access/request/', {'selected-administrator': admin_user.username})
    assertRedirects(response, '/config/')
    second_user.refresh_from_db()
    assert second_user.state == second_user.ACCESS_REQUESTED
    approval_url = f"/admin/kubeportal/user/{second_user.approval_id}/approve/"
    # Perform approval with new namespace as admin
    response = admin_client.post(approval_url, {'choice': 'approve_create', 'approve_create_name': 'default', 'comments': ''})
    assertRedirects(response, '/admin/kubeportal/user/')
    second_user.refresh_from_db()
    assert second_user.k8s_namespace().name == 'default'
    assert second_user.state == second_user.ACCESS_APPROVED
    assert second_user.answered_by != None


def test_approval_assign_plus_comment(admin_client, admin_user, client, second_user, mailoutbox):
    client.force_login(second_user)
    assert second_user.state == second_user.NEW
    response = client.post('/access/request/', {'selected-administrator': admin_user.username})
    assertRedirects(response, '/config/')
    second_user.refresh_from_db()
    assert second_user.state == second_user.ACCESS_REQUESTED
    approval_url = f"/admin/kubeportal/user/{second_user.approval_id}/approve/"
    # Perform approval with existing namespace as admin
    run_minikube_sync()
    response = admin_client.post(approval_url, {'choice': 'approve_choose', 'approve_choose_name': 'default', 'comments': 'The intern'})
    assertRedirects(response, '/admin/kubeportal/user/')
    second_user.refresh_from_db()
    assert second_user.k8s_namespace().name == 'default'
    assert second_user.state == second_user.ACCESS_APPROVED
    assert second_user.comments == "The intern"
    assert second_user.answered_by != None

def test_approval_reject(admin_client, admin_user, client, second_user, mailoutbox):
    client.force_login(second_user)
    assert second_user.state == second_user.NEW
    response = client.post('/access/request/', {'selected-administrator': admin_user.username})
    assertRedirects(response, '/config/')
    second_user.refresh_from_db()
    assert second_user.state == second_user.ACCESS_REQUESTED
    approval_url = f"/admin/kubeportal/user/{second_user.approval_id}/approve/"
    # Perform approval with existing namespace as admin
    response = admin_client.post(approval_url, {'choice': 'reject', 'comments': ''})
    assertRedirects(response, '/admin/kubeportal/user/')
    second_user.refresh_from_db()
    assert second_user.k8s_namespace() == None
    assert second_user.state == second_user.ACCESS_REJECTED
    assert second_user.answered_by != None


def test_reject_retry(admin_client, admin_user, client, second_user, mailoutbox):
    # First approval attempt of user
    client.force_login(second_user)
    response = client.post('/access/request/', {'selected-administrator': admin_user.username})
    assertRedirects(response, '/config/')
    approval_url = f"/admin/kubeportal/user/{second_user.approval_id}/approve/"

    # Admin denies
    response = admin_client.post(approval_url, {'choice': 'reject', 'comments': ''})
    assertRedirects(response, '/admin/kubeportal/user/')

    # Second approval attempt of user
    response = client.post('/access/request/', {'selected-administrator': admin_user.username})
    assertRedirects(response, '/config/')

    second_user.refresh_from_db()

    assert second_user.state == second_user.ACCESS_REQUESTED
    assert second_user.k8s_namespace() == None
    assert second_user.answered_by == None


def test_acess_request_view_mail_broken(admin_client, admin_user, mocker):
    mocker.patch('kubeportal.models.User.send_access_request', return_value=False)
    response = admin_client.post('/access/request/', {'selected-administrator': admin_user.username})
    assertRedirects(response, '/config/')


def test_approval_groups(admin_client, admin_user, client, second_user, mailoutbox, random_namespace_name):
    client.force_login(second_user)
    assert second_user.state == second_user.NEW
    response = client.post('/access/request/', {'selected-administrator': admin_user.username})
    assertRedirects(response, '/config/')
    second_user.refresh_from_db()
    assert second_user.state == second_user.ACCESS_REQUESTED
    approval_url = f"/admin/kubeportal/user/{second_user.approval_id}/approve/"
    # We only check for non-special groups (all / K8s users) here, they are tested elsewhere
    group1 = PortalGroup(name="Group the user does not have, and gets")
    group1.save()
    group2 = PortalGroup(name="Group the user already has, and keeps")
    group2.save()
    second_user.portal_groups.add(group2)
    group3 = PortalGroup(name="Group the user does not have, and still don't get")
    group3.save()
    group4 = PortalGroup(name="Group the user already has, and looses")
    group4.save()
    second_user.portal_groups.add(group4)
    # Perform approval with new namespace as admin
    response = admin_client.post(
        approval_url, 
        {'choice': 'approve_create', 
         'approve_create_name': random_namespace_name, 
         'comments': '', 
         'portal_groups': [group1.pk, group2.pk] 
        }
    )
    assertRedirects(response, '/admin/kubeportal/user/')
    second_user.refresh_from_db()
    assert second_user.k8s_namespace().name == random_namespace_name
    assert second_user.state == second_user.ACCESS_APPROVED
    assert group1 in list(second_user.portal_groups.all())
    assert group2 in list(second_user.portal_groups.all())
    assert group3 not in list(second_user.portal_groups.all())
    assert group4 not in list(second_user.portal_groups.all())
    assert second_user.answered_by != None
