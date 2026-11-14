from rest_framework.routers import DefaultRouter

from .viewsets import ContractItemViewSet

router = DefaultRouter()
router.register("items", ContractItemViewSet, basename="contractitem")

urlpatterns = router.urls
