from rest_framework.routers import DefaultRouter

from .viewsets import ContractItemViewSet, NPlusOneViewSet, UserPermissionsViewSet

router = DefaultRouter()
router.register("items", ContractItemViewSet, basename="contractitem")
router.register("n-plus-one", NPlusOneViewSet, basename="nplusone")
router.register("user-permissions", UserPermissionsViewSet, basename="userpermissions")

urlpatterns = router.urls
