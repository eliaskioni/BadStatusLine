# Import the helper gateway class
from django.conf import settings
from lib.AfricasTalkingGateway import AfricasTalkingGateway, AfricasTalkingGatewayException
import json
import requests
from structlog import get_logger
import re

def info_send(sender_id, to, message, enqueue_=0):
    logger = get_logger(__name__).bind(
    )
    # Specify the numbers that you want to send to in a comma-separated list
    # Please ensure you include the country code (+254 for Kenya in this case)

    # Create a new instance of our awesome gateway class
    gateway = AfricasTalkingGateway(settings.AFRICAS_TALKING_USERNAME, settings.AFRICAS_TALKING_API_KEY, "sandbox")

    # Any gateway errors will be captured by our custom Exception class below,
    # so wrap the call in a try-catch block
    response = []
    try:
        # Thats it, hit send and we'll take care of the rest.
        from_ = sender_id
        to = ", ".join(to)

        recipients = gateway.sendMessage(to, message, from_=from_, enqueue_=enqueue_)

        for recipient in recipients:
            # Note that only the Status "Success" means the message was sent
            result = {
                'to': recipient['number'],
                'status': recipient['status'],
                'messageId': recipient['messageId'],
                'cost': recipient['cost']
            }

            response.append(result)

    except AfricasTalkingGatewayException as e:
        error_msg = 'Encountered an error while sending: %s' % str(e)
        # result = {
        #     'to': recipient['number'],
        #     'status': error_msg,
        #     'messageId': recipient['messageId'],
        # }
        response.append(error_msg)
        logger.warning('error', error_msg=error_msg)

    return response


def send_airtime(data):
    headers = {
        'ApiKey': settings.AFRICAS_TALKING_API_KEY,
        'Content-Type': "application/x-www-form-urlencoded",
        'Accept': "Application/json"
    }
    url = settings.AFRICAS_TALKING_SEND_AIRTIME_URL
    username = settings.AFRICAS_TALKING_USERNAME,

    logger = get_logger(__name__).bind(
        action='africas_talking_send_airtime_request',
        data=data
    )

    data = dict(username=username,
                recipients=json.dumps(data))

    logger.info('request', url=url, username=username, data=data)

    try:
        response = requests.post(url=url,
                             data=data,
                             headers=headers,
                             verify=False
                             )
        content = response.content
        status_code = response.status_code

        logger.info('response', content=content, status_code=status_code)
        return response
    except Exception as e:
        logger.error("sending_airtime_exception", error=str(e))


def normalize_phone_number_to_africat_format(phone_number):
    # convert phone number to the standard format stating with 254
    match = re.match(r'^(0|\+?254)(?P<number>\d{9})$', phone_number)
    phone_number = '+254' + match.groupdict()['number']
    return phone_number