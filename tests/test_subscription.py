from django.contrib.auth.models import Group, Permission
from django.db import IntegrityError
from django.test import TestCase

from django_utils.gating.backends import ExtraPermissionsBackend

from .helpers import create_user
from .models import Plan


def permission(codename):
    return Permission.objects.get(codename=codename)


class AbstractSubscriptionPlanTests(TestCase):
    def setUp(self):
        group = Group.objects.create(name="premium")
        group.permissions.add(permission("add_plan"))
        self.plan = Plan.objects.create(name="premium")
        self.plan.groups.add(group)
        self.plan.user_permissions.add(permission("view_plan"))
        Plan.objects.create(name="other").user_permissions.add(permission("delete_plan"))

    def test_str_is_the_name(self):
        self.assertEqual(str(self.plan), "premium")

    def test_plans_are_ordered_by_name(self):
        self.assertEqual([plan.name for plan in Plan.objects.all()], ["other", "premium"])

    def test_name_is_unique(self):
        with self.assertRaises(IntegrityError):
            Plan.objects.create(name="premium")

    def test_get_permissions_returns_group_and_own_permissions_of_the_plan_only(self):
        codenames = set(self.plan.get_permissions().values_list("codename", flat=True))
        self.assertEqual(codenames, {"add_plan", "view_plan"})

    def test_plan_permissions_can_be_granted_by_a_backend(self):
        class PlanBackend(ExtraPermissionsBackend):
            def get_extra_permissions(self, user_obj):
                return self.plan.get_permissions()

        backend = PlanBackend()
        backend.plan = self.plan

        self.assertEqual(backend.get_all_permissions(create_user()), {"tests.add_plan", "tests.view_plan"})
