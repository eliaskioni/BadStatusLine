from django.conf.urls import url, include
from rest_framework import routers

from core.views import TextMessageModelApi

router = routers.DefaultRouter()
router.register(r'send_message', TextMessageModelApi, base_name="send_message")

urlpatterns = [
    url(r'^', include(router.urls)),
]
