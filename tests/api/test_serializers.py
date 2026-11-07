from django.contrib.auth.models import AnonymousUser, Permission
from django.test import TestCase
from rest_framework import serializers
from rest_framework.test import APIRequestFactory

from django_utils.api.serializers import RequestUserSerializerMixin

from ..helpers import create_user
from ..models import OwnedUUIDItem
from .viewsets import OwnedUUIDItemSerializer


class RequestUserSerializerMixinTests(TestCase):
    def serializer(self, user=None, with_request=True):
        class Serializer(RequestUserSerializerMixin, serializers.Serializer):
            pass

        context = {}
        if with_request:
            request = APIRequestFactory().get("/")
            request.user = user
            context["request"] = request
        return Serializer(context=context)

    def test_check_user_returns_the_authenticated_user(self):
        user = create_user()
        self.assertEqual(self.serializer(user).check_user(), user)

    def test_check_user_requires_a_request(self):
        with self.assertRaises(serializers.ValidationError):
            self.serializer(with_request=False).check_user()

    def test_check_user_requires_authentication(self):
        with self.assertRaises(serializers.ValidationError):
            self.serializer(AnonymousUser()).check_user()

    def test_check_perm(self):
        user = create_user()
        serializer = self.serializer(user)
        with self.assertRaises(serializers.ValidationError):
            serializer.check_perm("tests.add_owneduuiditem")

        user.user_permissions.add(Permission.objects.get(codename="add_owneduuiditem"))
        user = type(user).objects.get(pk=user.pk)  # drop the permission cache
        self.assertEqual(self.serializer(user).check_perm("tests.add_owneduuiditem"), user)


class CreatedByAndUUIDMixinSerializerTests(TestCase):
    def setUp(self):
        self.user = create_user()
        request = APIRequestFactory().post("/")
        request.user = self.user
        self.context = {"request": request}

    def test_create_sets_created_by_from_the_request(self):
        serializer = OwnedUUIDItemSerializer(data={}, context=self.context)
        serializer.is_valid(raise_exception=True)
        item = serializer.save()

        self.assertEqual(item.created_by, self.user)

    def test_representation(self):
        item = OwnedUUIDItem.objects.create(created_by=self.user)
        data = OwnedUUIDItemSerializer(item, context=self.context).data

        self.assertEqual(data["id"], str(item.uuid))
        self.assertEqual(data["created_by"], "john")
        self.assertEqual(data["created_at_display"], item.get_created_at_display())

    def test_ownership_and_id_are_read_only(self):
        serializer = OwnedUUIDItemSerializer(data={"created_by": "x", "id": "x"}, context=self.context)
        serializer.is_valid(raise_exception=True)
        self.assertEqual(serializer.validated_data, {})
