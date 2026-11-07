import io
import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from django_utils.utils import (
    M2M_APPEND,
    M2M_REPLACE,
    get_model_permission,
    lookup_by_uuid,
    md5_checksum,
    set_m2m,
)

from .models import OwnedUUIDItem


class Md5ChecksumTests(TestCase):
    def test_digest_and_seek_position(self):
        file_obj = io.BytesIO(b"hello")
        file_obj.seek(2)

        self.assertEqual(md5_checksum(file_obj), "5d41402abc4b2a76b9719d911017c592")
        self.assertEqual(file_obj.tell(), 0)


class SetM2MTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="b")
        self.groups = [Group.objects.create(name="g1"), Group.objects.create(name="g2")]
        self.user.groups.add(self.groups[0])

    def test_append_keeps_existing(self):
        set_m2m(self.user, "groups", [self.groups[1]], M2M_APPEND)
        self.assertEqual(self.user.groups.count(), 2)

    def test_append_is_default(self):
        set_m2m(self.user, "groups", [self.groups[1]])
        self.assertEqual(self.user.groups.count(), 2)

    def test_replace_overrides_existing(self):
        set_m2m(self.user, "groups", [self.groups[1]], M2M_REPLACE)
        self.assertEqual(list(self.user.groups.all()), [self.groups[1]])


class LookupByUUIDTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="owner")
        self.other = get_user_model().objects.create_user(username="other")
        self.item = OwnedUUIDItem.objects.create(created_by=self.user)

    def test_found_for_owner(self):
        self.assertEqual(lookup_by_uuid(OwnedUUIDItem, self.item.uuid, self.user), (self.item, True))

    def test_uuid_taken_by_another_user(self):
        self.assertEqual(lookup_by_uuid(OwnedUUIDItem, self.item.uuid, self.other), (None, False))

    def test_unknown_uuid_can_be_reused(self):
        self.assertEqual(lookup_by_uuid(OwnedUUIDItem, uuid.uuid4(), self.user), (None, True))


class GetModelPermissionTests(TestCase):
    def test_permission_string(self):
        self.assertEqual(get_model_permission(OwnedUUIDItem, "add"), "tests.add_owneduuiditem")
        self.assertEqual(get_model_permission(OwnedUUIDItem, "change"), "tests.change_owneduuiditem")
