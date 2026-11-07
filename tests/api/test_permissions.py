from unittest.mock import Mock

from django.test import SimpleTestCase

from django_utils.api.permissions import (
    AllowNone,
    CreatedByObjectPermission,
    CurrentUser,
    CurrentUserOrSuperuser,
    CurrentUserOrSuperuserOrReadOnly,
    FullModelPermissions,
    IsSuperuser,
)

__all__ = [
    "AllowNonePermissionTests",
    "IsSuperuserPermissionTests",
    "CurrentUserPermissionTests",
    "CurrentUserOrSuperuserPermissionTests",
    "CurrentUserOrSuperuserOrReadOnlyPermissionTests",
]


class AllowNonePermissionTests(SimpleTestCase):
    """Tests for AllowNone permission class."""

    def setUp(self):
        self.permission = AllowNone()
        self.request = Mock()
        self.view = Mock()

    def test_always_denies_permission(self):
        """Test that AllowNone always returns False."""
        self.request.user = Mock()
        self.assertFalse(self.permission.has_permission(self.request, self.view))

    def test_denies_even_for_superuser(self):
        """Test that AllowNone denies even superusers."""
        self.request.user = Mock(is_superuser=True)
        self.assertFalse(self.permission.has_permission(self.request, self.view))

    def test_denies_for_anonymous(self):
        """Test that AllowNone denies anonymous users."""
        self.request.user = Mock(is_authenticated=False)
        self.assertFalse(self.permission.has_permission(self.request, self.view))


class IsSuperuserPermissionTests(SimpleTestCase):
    """Tests for IsSuperuser permission class."""

    def setUp(self):
        self.permission = IsSuperuser()
        self.request = Mock()
        self.view = Mock()

    def test_allows_superuser(self):
        """Test that IsSuperuser allows superusers."""
        self.request.user = Mock(is_superuser=True)
        self.assertTrue(self.permission.has_permission(self.request, self.view))

    def test_denies_regular_user(self):
        """Test that IsSuperuser denies regular users."""
        self.request.user = Mock(is_superuser=False)
        self.assertFalse(self.permission.has_permission(self.request, self.view))

    def test_denies_anonymous(self):
        """Test that IsSuperuser denies anonymous users."""
        self.request.user = None
        self.assertFalse(self.permission.has_permission(self.request, self.view))


class CurrentUserPermissionTests(SimpleTestCase):
    """Tests for CurrentUser permission class."""

    def setUp(self):
        self.permission = CurrentUser()
        self.request = Mock()
        self.view = Mock()

    def test_allows_current_user(self):
        """Test that CurrentUser allows access to own object."""
        user = Mock(pk=1)
        self.request.user = user
        obj = Mock(pk=1)
        self.assertTrue(self.permission.has_object_permission(self.request, self.view, obj))

    def test_denies_different_user(self):
        """Test that CurrentUser denies access to other user's object."""
        user = Mock(pk=1)
        self.request.user = user
        obj = Mock(pk=2)
        self.assertFalse(self.permission.has_object_permission(self.request, self.view, obj))


class CurrentUserOrSuperuserPermissionTests(SimpleTestCase):
    """Tests for CurrentUserOrSuperuser permission class."""

    def setUp(self):
        self.permission = CurrentUserOrSuperuser()
        self.request = Mock()
        self.view = Mock()

    def test_allows_current_user(self):
        """Test that CurrentUserOrSuperuser allows access to own object."""
        user = Mock(pk=1, is_superuser=False)
        self.request.user = user
        obj = Mock(pk=1)
        self.assertTrue(self.permission.has_object_permission(self.request, self.view, obj))

    def test_allows_superuser_to_any_object(self):
        """Test that CurrentUserOrSuperuser allows superuser access to any object."""
        user = Mock(pk=1, is_superuser=True)
        self.request.user = user
        obj = Mock(pk=999)
        self.assertTrue(self.permission.has_object_permission(self.request, self.view, obj))

    def test_denies_regular_user_other_object(self):
        """Test that CurrentUserOrSuperuser denies regular user access to other objects."""
        user = Mock(pk=1, is_superuser=False)
        self.request.user = user
        obj = Mock(pk=2)
        self.assertFalse(self.permission.has_object_permission(self.request, self.view, obj))


class CurrentUserOrSuperuserOrReadOnlyPermissionTests(SimpleTestCase):
    """Tests for CurrentUserOrSuperuserOrReadOnly permission class."""

    def setUp(self):
        self.permission = CurrentUserOrSuperuserOrReadOnly()
        self.request = Mock()
        self.view = Mock()

    def test_allows_current_user(self):
        """Test that permission allows access to own object."""
        user = Mock(pk=1, is_superuser=False)
        self.request.user = user
        self.request.method = "PUT"
        obj = Mock(pk=1)
        self.assertTrue(self.permission.has_object_permission(self.request, self.view, obj))

    def test_allows_superuser_to_any_object(self):
        """Test that permission allows superuser access to any object."""
        user = Mock(pk=1, is_superuser=True)
        self.request.user = user
        self.request.method = "DELETE"
        obj = Mock(pk=999)
        self.assertTrue(self.permission.has_object_permission(self.request, self.view, obj))

    def test_allows_read_only_for_other_users(self):
        """Test that permission allows read-only access for other users."""
        user = Mock(pk=1, is_superuser=False)
        self.request.user = user
        obj = Mock(pk=2)

        # GET is a safe method
        self.request.method = "GET"
        self.assertTrue(self.permission.has_object_permission(self.request, self.view, obj))

        # HEAD is a safe method
        self.request.method = "HEAD"
        self.assertTrue(self.permission.has_object_permission(self.request, self.view, obj))

        # OPTIONS is a safe method
        self.request.method = "OPTIONS"
        self.assertTrue(self.permission.has_object_permission(self.request, self.view, obj))

    def test_denies_write_for_other_users(self):
        """Test that permission denies write access to other users' objects."""
        user = Mock(pk=1, is_superuser=False)
        self.request.user = user
        obj = Mock(pk=2)

        # POST is not a safe method
        self.request.method = "POST"
        self.assertFalse(self.permission.has_object_permission(self.request, self.view, obj))

        # PUT is not a safe method
        self.request.method = "PUT"
        self.assertFalse(self.permission.has_object_permission(self.request, self.view, obj))

        # DELETE is not a safe method
        self.request.method = "DELETE"
        self.assertFalse(self.permission.has_object_permission(self.request, self.view, obj))


class CreatedByObjectPermissionTests(SimpleTestCase):
    def setUp(self):
        self.permission = CreatedByObjectPermission()
        self.user = Mock()
        self.request = Mock(user=self.user)

    def test_allows_owner(self):
        self.assertTrue(self.permission.has_object_permission(self.request, Mock(), Mock(created_by=self.user)))

    def test_denies_other_user(self):
        self.assertFalse(self.permission.has_object_permission(self.request, Mock(), Mock(created_by=Mock())))

    def test_allows_objects_without_created_by(self):
        self.assertTrue(self.permission.has_object_permission(self.request, Mock(), object()))


class FullModelPermissionsTests(SimpleTestCase):
    def test_get_requires_view_permission(self):
        self.assertEqual(FullModelPermissions.perms_map["GET"], ["%(app_label)s.view_%(model_name)s"])
        self.assertEqual(FullModelPermissions.perms_map["OPTIONS"], [])
