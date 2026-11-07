from django.contrib.auth.models import Permission
from django.test import TestCase
from rest_framework import serializers
from rest_framework.test import APIRequestFactory, force_authenticate

from django_utils.api.serializers import GatedFieldsSerializerMixin
from django_utils.api.views import GatedFeaturesView
from django_utils.gating import get_gated_features

from ..helpers import create_user
from ..models import GatedItem


class GatedItemSerializer(GatedFieldsSerializerMixin, serializers.ModelSerializer):
    gated_fields = {"secret": "tests.use_secret"}

    class Meta:
        model = GatedItem
        fields = ["name", "secret"]


class GatedFieldsSerializerMixinTests(TestCase):
    def setUp(self):
        self.user = create_user()

    def serializer(self, data, user=None, **kwargs):
        request = APIRequestFactory().post("/")
        request.user = user or self.user
        return GatedItemSerializer(data=data, context={"request": request}, **kwargs)

    def grant(self):
        self.user.user_permissions.add(Permission.objects.get(codename="use_secret"))
        self.user = type(self.user).objects.get(pk=self.user.pk)

    def test_gated_field_is_refused_without_permission(self):
        serializer = self.serializer({"name": "a", "secret": "x"})

        self.assertFalse(serializer.is_valid())
        self.assertEqual(list(serializer.errors), ["secret"])

    def test_gated_field_is_accepted_with_permission(self):
        self.grant()
        self.assertTrue(self.serializer({"name": "a", "secret": "x"}).is_valid())

    def test_empty_value_is_a_no_op(self):
        self.assertTrue(self.serializer({"name": "a", "secret": ""}).is_valid())

    def test_partial_update_not_touching_the_field(self):
        item = GatedItem.objects.create(secret="kept")
        self.assertTrue(self.serializer({"name": "b"}, instance=item, partial=True).is_valid())

    def test_without_request_a_gated_field_is_refused(self):
        serializer = GatedItemSerializer(data={"secret": "x"})
        self.assertFalse(serializer.is_valid())

    def test_without_request_ungated_data_is_fine(self):
        self.assertTrue(GatedItemSerializer(data={"name": "a"}).is_valid())


class GatedFeaturesViewTests(TestCase):
    def setUp(self):
        get_gated_features.cache_clear()
        self.factory = APIRequestFactory()

    def test_anonymous_is_rejected(self):
        response = GatedFeaturesView.as_view()(self.factory.get("/"))
        self.assertIn(response.status_code, (401, 403))

    def test_returns_the_features_of_the_user(self):
        user = create_user()
        request = self.factory.get("/")
        force_authenticate(request, user)

        response = GatedFeaturesView.as_view()(request)

        self.assertEqual(response.data, {"use_secret": False})
