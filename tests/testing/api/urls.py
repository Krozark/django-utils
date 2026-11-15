from rest_framework.routers import DefaultRouter

from .viewsets import ContentTypeViewSet, ContractItemViewSet, NPlusOneViewSet, UserPermissionsViewSet

router = DefaultRouter()
router.register("items", ContractItemViewSet, basename="contractitem")
router.register("n-plus-one", NPlusOneViewSet, basename="nplusone")
router.register("content-type", ContentTypeViewSet, basename="contenttype")
router.register("user-permissions", UserPermissionsViewSet, basename="userpermissions")

urlpatterns = router.urls
