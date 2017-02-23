from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from core.models import TextMessage, SmsRecipient


class TextMessageSerializer(ModelSerializer):
    message = serializers.CharField(max_length=300, initial="The quick brown fox jumped over the old fence",
                                    style={'placeholder': 'Type message here', 'autofocus': True})

    class Meta:
        model = TextMessage
        fields = ("sender", "message", "file")


class SMSRecipientSerializer(ModelSerializer):
    class Meta:
        model = SmsRecipient
        fields = ("phone_number", "status", "names", "request_id")
