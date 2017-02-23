from __future__ import absolute_import
from celery import shared_task
from lib import africat
from structlog import get_logger
from core.models import SmsTransaction, SmsRecipient, TextMessage


@shared_task
def add(x, y):
    """
    You can import this example task as: from core.tasks import add
    """
    return x + y


@shared_task(bind=True, name="tasks.send_messages")
def send_messages(*args, **kwargs):
    logger = get_logger(__name__).bind(
        action="send_sms_task",
        args=args,
        kwargs=kwargs
    )
    logger.info("start sending of SMS to Africa's Talking")
    text_message_id = kwargs.get('text_message_id')
    transaction_id = kwargs.get('sms_transaction_id')
    transaction = SmsTransaction.objects.get(pk=transaction_id)
    text_message = TextMessage.objects.get(pk=text_message_id)
    message_cost = kwargs.get('sms', {}).get('message_cost')
    to_, message_text = text_message.create_sms_recipients(message_cost=message_cost, transaction_=transaction)
    sms = kwargs['sms']
    enqueue_ = sms.get('enqueue')
    sender_id = sms.get('sender_id')
    response = africat.info_send(sender_id=sender_id, to=to_, message=message_text, enqueue_=enqueue_)
    recipients = SmsRecipient.objects.filter(transactions=transaction)
    if not response:
        recipients.update(status="Failed")
    elif isinstance(response, str):
        recipients.update(status="Failed")
    else:
        for res in response:
            rec = recipients.get(phone_number=res.get('to'))
            rec.waiting_confirmation() if res.get('status') == "Success" else rec.transaction_failed()
            rec.request_id = res['messageId']
            rec.save()