from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.template.loader import get_template
from django.test import RequestFactory, TestCase

from django_utils.admin import CreatedByAdminMixin, IsPublicAdminMixin, ReadOnlyAdminMixin

from .models import OwnedItem, OwnedPublicItem, PublicItem


class OwnedItemAdmin(CreatedByAdminMixin, admin.ModelAdmin):
    pass


class PublicItemAdmin(IsPublicAdminMixin, admin.ModelAdmin):
    pass


class ReadOnlyOwnedItemAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    pass


class AdminTestCase(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.factory = RequestFactory()
        self.user_model = get_user_model()
        self.owner = self.user_model.objects.create_user(username="owner", is_staff=True)
        self.other = self.user_model.objects.create_user(username="other", is_staff=True)
        self.superuser = self.user_model.objects.create_superuser(username="root")

    def request(self, user, path="/", **params):
        request = self.factory.get(path, params)
        request.user = user
        return request


class CreatedByAdminMixinTests(AdminTestCase):
    def setUp(self):
        super().setUp()
        self.admin = OwnedItemAdmin(OwnedItem, self.site)
        self.mine = OwnedItem.objects.create(created_by=self.owner)
        self.theirs = OwnedItem.objects.create(created_by=self.other)
        self.owner.user_permissions.add(*Permission.objects.filter(content_type__app_label="tests"))

    def test_queryset_is_scoped_to_the_user(self):
        self.assertEqual(list(self.admin.get_queryset(self.request(self.owner))), [self.mine])

    def test_superuser_sees_everything(self):
        self.assertEqual(self.admin.get_queryset(self.request(self.superuser)).count(), 2)

    def test_save_model_stamps_created_by_on_creation_only(self):
        obj = OwnedItem()
        self.admin.save_model(self.request(self.owner), obj, form=None, change=False)
        self.assertEqual(obj.created_by, self.owner)

        self.admin.save_model(self.request(self.superuser), obj, form=None, change=True)
        self.assertEqual(obj.created_by, self.owner)

    def test_foreign_objects_are_read_only_for_non_superusers(self):
        request = self.request(self.owner)
        self.assertTrue(self.admin.has_change_permission(request, self.mine))
        self.assertFalse(self.admin.has_change_permission(request, self.theirs))
        self.assertFalse(self.admin.has_delete_permission(request, self.theirs))

    def test_superuser_can_change_foreign_objects(self):
        request = self.request(self.superuser)
        self.assertTrue(self.admin.has_change_permission(request, self.theirs))
        self.assertTrue(self.admin.has_delete_permission(request, self.theirs))

    def test_list_display_and_exclude(self):
        request = self.request(self.owner)
        self.assertEqual(self.admin.get_list_display(request), ("__str__", "created_by", "created_at"))
        self.assertEqual(self.admin.get_exclude(request), ("id", "created_by"))

    def test_username_filter(self):
        request = self.request(self.superuser, created_by__username="oth")
        filter_class = self.admin.get_list_filter(request)[0]
        list_filter = filter_class(request, dict(request.GET.items()), OwnedItem, self.admin)

        self.assertEqual(list(list_filter.queryset(request, OwnedItem.objects.all())), [self.theirs])

    def test_filter_template_exists(self):
        self.assertTrue(get_template(self.admin.get_list_filter(self.request(self.owner))[0].template))


class IsPublicAdminMixinTests(AdminTestCase):
    def setUp(self):
        super().setUp()
        self.admin = PublicItemAdmin(PublicItem, self.site)

    def test_is_public_is_displayed_and_filterable(self):
        request = self.request(self.superuser)
        self.assertEqual(self.admin.get_list_display(request), ("__str__", "is_public"))
        self.assertEqual(self.admin.get_list_filter(request), ("is_public",))

    def test_is_public_is_hidden_from_non_superusers(self):
        self.assertIn("is_public", self.admin.get_exclude(self.request(self.owner)))
        self.assertNotIn("is_public", self.admin.get_exclude(self.request(self.superuser)))

    def test_queryset_contains_private_objects(self):
        PublicItem.objects.create(is_public=False)
        self.assertEqual(self.admin.get_queryset(self.request(self.superuser)).count(), 1)


class ReadOnlyAdminMixinTests(AdminTestCase):
    def test_everything_is_read_only(self):
        model_admin = ReadOnlyOwnedItemAdmin(OwnedItem, self.site)
        request = self.request(self.superuser)

        self.assertFalse(model_admin.has_add_permission(request))
        self.assertFalse(model_admin.has_change_permission(request))
        self.assertIn("created_by", model_admin.get_readonly_fields(request))


class AdminMixinsOrderTests(AdminTestCase):
    """Combining the mixins must scope the objects to their owner whatever the order of the bases."""

    def test_non_superusers_only_see_their_objects_whatever_the_order(self):
        class PublicFirst(IsPublicAdminMixin, CreatedByAdminMixin, admin.ModelAdmin):
            pass

        class OwnerFirst(CreatedByAdminMixin, IsPublicAdminMixin, admin.ModelAdmin):
            pass

        mine = OwnedPublicItem.objects.create(created_by=self.owner)
        OwnedPublicItem.objects.create(created_by=self.other, is_public=True)

        for admin_class in (PublicFirst, OwnerFirst):
            with self.subTest(admin_class=admin_class.__name__):
                queryset = admin_class(OwnedPublicItem, self.site).get_queryset(self.request(self.owner))
                self.assertEqual(list(queryset), [mine])

    def test_private_objects_are_listed(self):
        private = OwnedPublicItem.objects.create(created_by=self.owner, is_public=False)

        class Combined(CreatedByAdminMixin, IsPublicAdminMixin, admin.ModelAdmin):
            pass

        queryset = Combined(OwnedPublicItem, self.site).get_queryset(self.request(self.owner))
        self.assertEqual(list(queryset), [private])
