from rest_framework.routers import DefaultRouter

from .viewsets import ContractItemViewSet, NPlusOneViewSet

router = DefaultRouter()
router.register("items", ContractItemViewSet, basename="contractitem")
router.register("n-plus-one", NPlusOneViewSet, basename="nplusone")

urlpatterns = router.urls
