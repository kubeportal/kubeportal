from unittest import skip

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from kubeportal.admin import merge_users, UserAdmin
from kubeportal.k8s import kubernetes_api as api
from kubeportal.models import UserState
from kubeportal.models.kubernetesnamespace import KubernetesNamespace
from kubeportal.models.kubernetesserviceaccount import KubernetesServiceAccount
from kubeportal.models.portalgroup import PortalGroup
from .helpers import run_minikube_sync


@pytest.mark.django_db
@pytest.mark.usefixtures("minikube_sync")
def test_kube_ns_changelist(admin_client):
    response = admin_client.get(
        reverse('admin:kubeportal_kubernetesnamespace_changelist'))
    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.usefixtures("minikube_sync")
def test_kube_svc_changelist(admin_client):
    response = admin_client.get(
        reverse('admin:kubeportal_kubernetesserviceaccount_changelist'))
    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.usefixtures("minikube_sync")
def test_user_changelist(admin_client):
    response = admin_client.get(reverse('admin:kubeportal_user_changelist'))
    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.usefixtures("minikube_sync")
def test_new_external_ns_sync():
    api.create_k8s_ns("new-external-ns1")
    try:
        run_minikube_sync()
        new_ns_object = KubernetesNamespace.objects.get(
            name="new-external-ns1")
        assert new_ns_object.is_synced() == True
        for svc_account in new_ns_object.service_accounts.all():
            assert svc_account.is_synced() == True
    finally:
        api.delete_k8s_ns("new-external-ns1")


@pytest.mark.django_db
@pytest.mark.usefixtures("minikube_sync")
def test_exists_both_sides_sync():
    api.create_k8s_ns("new-external-ns2")
    new_ns = KubernetesNamespace(name="new-external-ns2")
    new_ns.save()
    try:
        run_minikube_sync()
    finally:
        api.delete_k8s_ns("new-external-ns2")


@pytest.mark.django_db
@pytest.mark.usefixtures("minikube_sync")
def test_new_svc_sync():
    default_ns = KubernetesNamespace.objects.get(name="default")
    new_svc = KubernetesServiceAccount(name="foobar", namespace=default_ns)
    new_svc.save()
    run_minikube_sync()
    svc_names = [
        svc.metadata.name for svc in api.get_service_accounts()]
    assert "foobar" in svc_names


@pytest.mark.django_db
@pytest.mark.usefixtures("minikube_sync")
def test_new_ns_sync():
    new_ns = KubernetesNamespace(name="foo")
    new_ns.save()
    run_minikube_sync()
    ns_names = [ns.metadata.name for ns in api.get_namespaces()]
    assert "foo" in ns_names


@pytest.mark.django_db
@pytest.mark.usefixtures("minikube_sync")
def test_new_ns_broken_name_sync():
    test_cases = {"foo_bar": "foobar", "ABCDEF": "abcdef"}
    for old, new in test_cases.items():
        new_ns = KubernetesNamespace(name=old)
        new_ns.save()
        run_minikube_sync()
        ns_names = [ns.metadata.name for ns in api.get_namespaces()]
        assert old not in ns_names
        assert new in ns_names


def test_admin_index_view(admin_client):
    response = admin_client.get('/admin/')
    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.usefixtures("minikube_sync")
def test_special_k8s_approved(rf, admin_index_request):
    # Creating an auto_add_approved group should not change its member list.
    group = PortalGroup.objects.get(special_k8s_accounts=True)
    assert group.members.count() == 0
    # Create a new user should not change the member list
    User = get_user_model()
    u = User(username="Hugo", email="a@b.de")
    u.save()
    assert group.members.count() == 0
    # walk through approval workflow
    url = reverse('welcome')
    request = rf.get(url)
    u.send_access_request(request)
    u.save()
    # Just sending an approval request should not change to member list
    assert group.members.count() == 0
    # Prepare K8S namespace
    ns = KubernetesNamespace(name="default")
    ns.save()
    new_svc = KubernetesServiceAccount(name="foobar", namespace=ns)
    new_svc.save()
    # Perform approval
    assert(u.approve(admin_index_request, new_svc))
    u.save()
    # Should lead to addition of user to the add_approved group
    assert group.members.count() == 1


@pytest.mark.django_db
@pytest.mark.usefixtures("minikube_sync")
def test_special_k8s_unapproved():
    group = PortalGroup.objects.get(special_k8s_accounts=True)
    ns = KubernetesNamespace(name="default")
    ns.save()
    new_svc = KubernetesServiceAccount(name="foobar", namespace=ns)
    new_svc.save()
    User = get_user_model()
    # create approved user
    u = User(username="Hugo",
             email="a@b.de",
             state=UserState.ACCESS_APPROVED,
             service_account=new_svc)
    u.save()
    assert group.members.count() == 1
    # unapprove
    u.state = UserState.ACCESS_REJECTED
    u.save()
    assert group.members.count() == 0


@pytest.mark.django_db
@pytest.mark.usefixtures("minikube_sync")
def test_user_rejection(rf, admin_index_request):
    User = get_user_model()
    u = User(username="Hugo", email="a@b.de")
    u.save()
    # walk through rejection workflow
    url = reverse('welcome')
    request = rf.get(url)
    u.send_access_request(request)
    u.save()
    # Build full-fledged request object for logged-in admin
    assert(u.reject(admin_index_request))
    u.save()
    assert(u.has_access_rejected())



'''
Create two users with the secondary (the later created) one having cluster access,
an assigned comment and two assigned groups
Merge both users.
The primary user should be assigned the cluster access, user comment and all the
portal groups of the secondary user.
The secondary user should be deleted.
'''

@pytest.mark.django_db
@pytest.mark.usefixtures("minikube_sync")
def test_user_merge_access_approved(admin_index_request):
    User = get_user_model()
    primary = User(
        username="HUGO",
        email="a@b.de")
    primary.save()

    ns = KubernetesNamespace(name="default")
    ns.save()
    new_svc = KubernetesServiceAccount(name="foobar", namespace=ns)
    new_svc.save()
    secondary = User(
        username="hugo",
        state=UserState.ACCESS_APPROVED,
        email="a@b.de",
        comments="secondary user comment",
        service_account=new_svc)
    secondary.save()

    group1 = PortalGroup(name="testgroup1")
    group1.save()
    group2 = PortalGroup(name="testgroup2")
    group2.save()

    secondary.portal_groups.add(group1)
    secondary.portal_groups.add(group2)
    secondary.save()

    # Build full-fledged request object for logged-in admin
    # approve secondary for cluster access
    secondary.approve(admin_index_request, new_svc)

    # the merge method only accepts a queryset of users since that's what
    # the admin interface creates
    queryset_of_users = User.objects.filter(
        pk__in=[primary.id, secondary.id])

    # merge both users. shouldn't return anything
    assert(not merge_users(UserAdmin, admin_index_request, queryset_of_users))

    # the primary user has been altered but the old object is still in memory
    # we need to query for the updated user again
    primary = User.objects.get(pk=primary.id)

    # Does primary have all the values of secondary user?
    assert primary.comments == "secondary user comment"
    assert primary.portal_groups.filter(name=group1.name)
    assert primary.portal_groups.filter(name=group2.name)
    assert primary.has_access_approved

'''
Create two users with the secondary (the later created) one having rejected cluster access,
Merge both users.
The primary user should be assigned the rejected cluster access.
The secondary user should be deleted.
'''

@pytest.mark.django_db
@pytest.mark.usefixtures("minikube_sync")
def test_user_merge_access_rejected(admin_index_request):
    User = get_user_model()
    primary = User(
        username="HUGO",
        email="a@b.de")
    primary.save()

    ns = KubernetesNamespace(name="default")
    ns.save()

    new_svc = KubernetesServiceAccount(name="foobar", namespace=ns)
    new_svc.save()
    # Perform approval
    assert(primary.approve(admin_index_request, new_svc))
    primary.save()

    secondary = User(
        username="hugo",
        state=UserState.ACCESS_APPROVED,
        email="a@b.de",
        comments="secondary user comment",
        service_account=new_svc)
    secondary.save()

    # reject cluster access for secondary
    secondary.reject(admin_index_request)

    # the merge method only accepts a queryset of users since that's what
    # the admin interface creates
    queryset_of_users = User.objects.filter(
        pk__in=[primary.id, secondary.id])

    # merge both users. shouldn't return anything
    assert(not merge_users(UserAdmin, admin_index_request, queryset_of_users))

    # the primary user has been altered but the old object is still in memory
    # we need to query for the updated user again
    primary = User.objects.get(pk=primary.id)

    assert primary.has_access_rejected

# @skip("Function disabled")
# @pytest.mark.django_db
# @pytest.mark.usefixtures("minikube_sync")
# def test_backend_cleanup_view(admin_cleanup_request):
#     User = get_user_model()
#     u = User(
#         username="HUGO",
#         email="a@b.de")
#     u.save()
#
#     # we need an inactive user for the the filter to work
#     from dateutil.parser import parse
#     u.last_login = parse("2017-09-23 11:21:52.909020")
#     u.save()
#
#     ns = KubernetesNamespace(name="aaasdfadfasdfasdf", visible=True)
#     ns.save()
#
#     new_svc = KubernetesServiceAccount(name="foobar", namespace=ns)
#     new_svc.save()
#     new_svc.delete()
#
#     assert(admin_cleanup_request)
#
# @skip("Function disabled")
# @pytest.mark.django_db
# @pytest.mark.usefixtures("minikube_sync")
# def test_backend_cleanup_entitity_getters():
#     User = get_user_model()
#     from django.utils import dateparse
#     # we need an inactive user for the the filter to work
#     u = User(
#         username="HUGO",
#         email="a@b.de",
#         last_login=dateparse.parse_datetime(
#             "2017-09-23 11:21:52.909020 +02.00")
#     )
#     u.save()
#
#     ns = KubernetesNamespace(name="asdfadfasdfasdf", visible=True)
#     ns.save()
#
#     assert(User.inactive_users()[0] ==
#            User.objects.get(username=u.username))
#     assert(KubernetesNamespace.without_pods()[0] == ns)
#     assert(KubernetesNamespace.without_service_accounts()[0] == ns)

# @skip("Function disabled")
# @pytest.mark.django_db
# @pytest.mark.usefixtures("minikube_sync")
# def test_backend_prune_view():
#     User = get_user_model()
#     from django.utils import dateparse
#     # we need an inactive user for the the filter to work
#     user_list = [
#         User.objects.create_user(
#             username="HUGO1",
#             email="a@b.de",
#             last_login=dateparse.parse_datetime(
#                 "2017-09-23 11:21:52.909020 +02:00")
#         ),
#
#         User.objects.create_user(
#             username="HUGO2",
#             email="b@b.de",
#             last_login=dateparse.parse_datetime(
#                 "2017-09-23 11:21:52.909020 +02:00")
#         ),
#
#         User.objects.create_user(
#             username="HUGO3",
#             email="c@b.de",
#             last_login=dateparse.parse_datetime(
#                 "2017-09-23 11:21:52.909020 +02:00")
#         )
#     ]
#
#     ns_list = [
#         KubernetesNamespace.objects.create(name="test-namespace1"),
#         KubernetesNamespace.objects.create(name="test-namespace2"),
#         KubernetesNamespace.objects.create(name="test-namespace3")
#     ]
#
#     # prune visible namespaces without an assigned service account
#     request = create_backend_request("admin:prune", {
#         'prune': "namespaces-no-service-acc",
#         "namespaces": [ns.name for ns in ns_list]
#     })
#     prune(request)
#
#     assert(not KubernetesNamespace.objects.filter(
#         name__in=[ns.name for ns in ns_list]))
#
#     ns_list = [
#         KubernetesNamespace.objects.create(name="test-namespace1"),
#         KubernetesNamespace.objects.create(name="test-namespace2"),
#         KubernetesNamespace.objects.create(name="test-namespace3")
#     ]
#
#     # prune visible namespaces without pods
#     request = create_backend_request("admin:prune", {
#         'prune': "namespaces-no-pods",
#         "namespaces": [ns.name for ns in ns_list]
#     })
#     prune(request)
#
#     # have all been pruned?
#     assert(not KubernetesNamespace.objects.filter(
#         name__in=[ns.name for ns in ns_list]))
#
#     # prune service accounts that haven't logged in for a long time
#     request = create_backend_request("admin:prune", {
#         'prune': "inactive-users",
#         "users": [u.username for u in user_list]
#     })
#     prune(request)
#
#     # have all been pruned?
#     assert(not KubernetesServiceAccount.objects.filter(
#         name__in=[u.username for u in user_list]))
