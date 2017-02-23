from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from structlog import get_logger

from core.forms import UploadSMSExcelForm
from core.models import SmsRecipient
from core.serializers import TextMessageSerializer, SMSRecipientSerializer
from rest_framework import response, status

from core.utilities import create_send_sms_task


class TextMessageModelApi(ModelViewSet):
    serializer_class = TextMessageSerializer
    base_name = 'text_messages'

    def list(self, request, *args, **kwargs):
        return self.get_queryset()

    def get_queryset(self):
        recipients = SmsRecipient.objects.all().order_by("-pk")[:5]
        json_payload = [SMSRecipientSerializer(recipient).data for recipient in recipients]
        return Response(json_payload)

    def create(self, request, *args, **kwargs):
        logger = get_logger(__name__).bind(
            action="send_sms_excel"
        )

        logger.debug("start")
        form = UploadSMSExcelForm(request.POST, request.FILES)
        status_, sms_and_recipients_ = form.is_valid(request)
        response_ = response.Response()
        if not status_ and isinstance(sms_and_recipients_, tuple):
            response_.status_code = status.HTTP_400_BAD_REQUEST
            response_.data = {"invalid_format": True, "extension": sms_and_recipients_[1]}
            return response_
        if isinstance(sms_and_recipients_, bool):
            response_.status_code = status.HTTP_400_BAD_REQUEST
            response_.data = {"empty_excel_file": True}
            return response_
        message = request.data.get("message")
        if not message:
            response_.status_code = status.HTTP_400_BAD_REQUEST
            excel = {"data": sms_and_recipients_}
            response_.data = {"message": "Empty message not allowed", "excel": excel, "status": status_}
            response_.data.update({"data": sms_and_recipients_}) if not status_ else ""
            return response_
        if not status_:
            response_.status_code = status.HTTP_400_BAD_REQUEST
            excel = {"data": sms_and_recipients_}
            response_.data = {"excel": excel, "in_valid_excel": True}
            return response_
        sender_id = request.data.get("sender_id")

        if status_:
            data = {str(message): [(value, key) for key, value in sms_and_recipients_.items()]}

            user = User.objects.get(username="guest")
            sms_status, result = create_send_sms_task(sms_sender=user, sms_details=data,
                                                      sender_id=sender_id)
            if sms_status:
                response_.status_code = status.HTTP_200_OK
                return response_
            else:
                response_.status_code = status.HTTP_403_FORBIDDEN
                response_.data = sms_status
                return response_
