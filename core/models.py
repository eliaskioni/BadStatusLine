from __future__ import unicode_literals

import re

from django.db import models
from django.db.transaction import atomic
from django_fsm import FSMField, transition
from jsonfield import JSONField

# Create your models here.


class SmsTransaction(models.Model):
    """
    A model that represents an SMS transaction
    """
    created_at = models.DateTimeField(u'Creation Date', auto_now=True)
    updated_at = models.DateTimeField(u'Update Date', auto_now_add=True)
    response = JSONField(blank=True, null=True)

    def __unicode__(self):
        return "{0} - {1}".format(self.account, self.response)

    class Meta:
        verbose_name = "SMS Transaction"
        verbose_name_plural = "SMS Transactions"


class SmsRecipient(models.Model):
    """
    A model that represents an SMS recipient data
    """
    RECEIVED, IN_PROGRESS, TRANSACTION_FAILED, WAITING_CONFIRMATION, SUCCEEDED, NOTIFICATION_FAILED = "received", "in_progress", "Failed", "sent", "success", "failed"
    STATE_CHOICES = (
        (RECEIVED, RECEIVED),
        (IN_PROGRESS, IN_PROGRESS),
        (WAITING_CONFIRMATION, WAITING_CONFIRMATION),
        (SUCCEEDED, SUCCEEDED),
        (TRANSACTION_FAILED, TRANSACTION_FAILED),
        (NOTIFICATION_FAILED, NOTIFICATION_FAILED)
    )

    phone_number = models.CharField(u'Phone Number', max_length=255, blank=True, null=True)
    message = models.TextField(u'Message', max_length=None, blank=True, null=True)
    status = FSMField(u'Status', max_length=255, choices=STATE_CHOICES, default=RECEIVED, protected=True)
    names = models.CharField(u'Names', max_length=255, blank=True, null=True)
    error_message = models.CharField(max_length=255, null=True, blank=True)
    transactions = models.ForeignKey(SmsTransaction, related_name="sms_transactions")
    request_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(u'Creation Date', auto_now=True)
    updated_at = models.DateTimeField(u'Update Date', auto_now_add=True)
    message_cost = models.DecimalField(max_digits=9, decimal_places=2, default=00.00)

    def __unicode__(self):
        return "{0} - {1}".format(self.phone_number, self.status)

    def save(self, *args, **kwargs):
        digits = filter(lambda c: c.isdigit() or c == '+', self.phone_number)
        match = re.match(r'^(0)(?P<number>\d{9})$', digits)

        if match:
            phone_number = '+254' + match.groupdict()['number']
            self.phone_number = phone_number
        if not self.phone_number.startswith("+"):
            self.phone_number = "+" + str(self.phone_number)
        super(SmsRecipient, self).save(*args, **kwargs)

    @property
    def get_user(obj):
        return obj.transactions.account.user

    @transition(status, source=RECEIVED, target=IN_PROGRESS)
    def start_processing(self):
        """
        This supposed to be called when a transaction is sent to worker via rabbitmq
        :return:
        """

    @transition(status, source=(IN_PROGRESS, RECEIVED), target=WAITING_CONFIRMATION)
    def waiting_confirmation(self):
        """
        This is called when a successful response is returned by worker
        :return:
        """

    @transition(status, source=(IN_PROGRESS, RECEIVED), target=TRANSACTION_FAILED)
    def transaction_failed(self):
        """
        this is called when worker returns a failure response
        :return:
        """

    @transition(status, source=WAITING_CONFIRMATION, target=SUCCEEDED)
    def confirmed(self):
        """
        This is called when an SMS delivery report from Africa's Talking has a Success status
        :return:
        """

    @transition(status, source=WAITING_CONFIRMATION, target=NOTIFICATION_FAILED)
    def confirmation_failed(self):
        """
        This is called when an SMS delivery report from Africa's Talking has failed
        :return:
        """

    @transition(status, source=(IN_PROGRESS, RECEIVED), target=TRANSACTION_FAILED)
    def transaction_failed_before_processing(self):
        """
        this is called when worker returns a failure response
        :return:
        """

    class Meta:
        verbose_name = "SMS Recipient"
        verbose_name_plural = "SMS Recipients"


class TextMessage(models.Model):
    """
    A model that stores sent text messages
    """
    Tumacredo, AFRICASTALKING = "Tumacredo", "AFRICASTKNG"
    SENDER_IDS = (
        (Tumacredo, Tumacredo),
        (AFRICASTALKING, AFRICASTALKING)

    )

    sender = models.CharField(u'Sender', max_length=255, choices=SENDER_IDS, null=True, blank=True)
    to = JSONField(default={}, blank=True, null=True)
    message = models.TextField(u'Message', null=True, blank=True,
                               default="The quick brown fox jumped over the old fence")
    file = models.FileField()

    def __unicode__(self):
        return "{0}".format(self.sender)

    def create_sms_recipients(self, message_cost, transaction_):
        to_ = []
        with atomic():
            list_of_sms_recipients_to_create = []
            for name_and_recipient in self.to.get('recipient').items():
                list_of_sms_recipients_to_create.append(
                    SmsRecipient(phone_number=name_and_recipient[0],
                                 names=name_and_recipient[1],
                                 message=self.message,
                                 transactions=transaction_,
                                 message_cost=message_cost
                                 )
                )
                to_.append(name_and_recipient[0])
            SmsRecipient.objects.bulk_create(
                list_of_sms_recipients_to_create
            )
        return to_, self.message