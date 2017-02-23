from decimal import Decimal

import phonenumbers
from structlog import get_logger
from celery_declarations.celery import app
from .models import *


def create_send_sms_task(sms_sender, sms_details, sender_id=None):
    """
    This method does the following:
        - it gets the sms details
        - validates the phone_numbers
        - Persist Text Message
        - Create celery task for async interactions with Africa's Talking

    :param user:
    :param sms_details:
    :return: status, {'transaction_id': transaction_id}
    """
    message_cost = Decimal(message_cost_calculator(sms_details.keys()[0]))  # calculate message cost
    logger = get_logger(__name__).bind(
        action="create_send_sms_task",
        sms_sender=sms_sender,
        sms_details_count=len(sms_details),
        sender_id=sender_id,
        message_cost=message_cost,
    )

    logger.debug("start")

    # Check if sms_details is a dict
    if not isinstance(sms_details, dict):
        logger.info("invalid_data_structure")
        return False, [{"error": "Invalid data structure", "index": -1}]

    for index, sms_values in enumerate(sms_details):
        the_msg = sms_values
        the_numbers = sms_details[sms_values]
        valid, error = validated_phone_sms(the_numbers, the_msg)

        if not valid:
            error['index'] = index
            logger.warning("invalid_data", error=error)
            return valid, [error]

    sms_dict = {}
    list_of_transaction_to_create = []
    recipient_split = {}
    message = sms_details.keys()[0]
    list_of_transactions_created = []

    for index, recipient_data in enumerate(sms_details.values()[0]):
        phone_number = recipient_data[0]
        if phone_number.startswith('254'):
            phone_number = phone_number.replace('254', '+254', 1)
        if phone_number.startswith('7'):
            phone_number = '+254' + phone_number
        if phone_number.startswith('0'):
            phone_number = '+254' + phone_number[-9:]
        if not phone_number.startswith('+'):
            phone_number = '+' + phone_number
        recipient_split.update({phone_number: recipient_data[1]})
        if (index + 1) % 400 == 0:
            sms_transaction = SmsTransaction.objects.create()
            text_message = TextMessage.objects.create(sender=str(sms_sender.username), to={
                "recipient": recipient_split
            }, message=message)
            list_of_transaction_to_create.append(
                text_message.id
            )
            list_of_transactions_created.append(sms_transaction.id)
            recipient_split = {}
    if recipient_split:
        text_message = TextMessage.objects.create(sender=str(sms_sender.username), to={
            "recipient": recipient_split
        }, message=message)
        list_of_transaction_to_create.append(
            text_message.id
        )
        sms_transaction = SmsTransaction.objects.create()
        list_of_transactions_created.append(sms_transaction.id)

    sms_dict.update(dict(
        sent_from=str(sms_sender.username),
        message=message,
        bulkSMSMode=1,
        enqueue=0,
        keyword=None,
        linkId=None,
        sender_id=sender_id,
        message_cost=message_cost
    ))

    for id_, transaction_id in zip(list_of_transaction_to_create, list_of_transactions_created):
        app.send_task(
            'tasks.send_messages',
            kwargs={
                'sms': sms_dict,
                'text_message_id': id_,
                'sms_transaction_id': transaction_id
            }
        )
    logger.info('data_sent_to_worker', transaction_id=list_of_transactions_created, sms=sms_dict)

    logger.info("end")
    return True, {'transaction_id': list_of_transactions_created}


def validate_number(recipients):
    for recipient in recipients:
        if not isinstance(recipient, tuple) and not isinstance(recipient, list):
            return {"to": " recipient should be a tuple or a list"}
        if len(recipient) != 2:
            return {"to": " recipient should have phone_number and name only"}

        phone_number = str(recipient[0]).strip()
        try:
            match = re.match(r'^(0)(?P<number>\d{9})$', phone_number)

            if match:
                phone_number = '+254' + match.groupdict()['number']

            if not phone_number.startswith("+"):
                phone_number = "+" + str(phone_number)

            phone_number = phonenumbers.parse(phone_number, None)
            if not phonenumbers.is_valid_number(phone_number):
                return {"to": str(phone_number.country_code) + str(
                    phone_number.national_number) + " is not a valid phone number should start with 0 or"
                                                    " +254, +256(Uganda) and "
                                                    "more than 9 digits"}
        except ValueError:
            return {"to": " phone number should start with 0 or +254, +256(Uganda) and 9 or more digits "}


def validate_sms(message):
    try:
        msg_str = isinstance(message, basestring)
        # import pdb;pdb.set_trace()
        if msg_str:
            msg_str_len = message.__len__()

            if msg_str_len == 0:
                return {'message': ' message field should not be empty'}

        else:
            return {"message": " a message has to be in string format to be sent"}
    except ValueError:
        return {'message': ' message field should not be empty'}


def validated_phone_sms(recipients, sms):
    error = {}

    recipients_errors = validate_number(recipients)

    if recipients_errors:
        error.update(recipients_errors)

    msg_errors = validate_sms(sms)
    if msg_errors:
        error.update(msg_errors)
    try:
        if error:
            return False, error
        else:
            return True, True

    except ValueError:
        return False, error


def message_cost_calculator(message):
    message_length = len(message)
    extra_characters = message_length % 160
    extra_exact = (message_length - extra_characters) / 160
    return extra_exact + 1
