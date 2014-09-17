# encoding: utf-8

from django.db import models
from abc import ABCMeta, abstractmethod

class StoredResponse(models.Model):
  'This class permits a separation of concerns between the code specifying responses on the one hand, and their content on the other hand.'
  text  = models.TextField()
  code  = models.TextField()

  @staticmethod
  def fetch_tranform(cod, msg):
    'Fetch a response by code, creating it (with simple default text) if it does not yet exist.'
    ans = StoredResponse.fetch(cod)
    return ans

  @staticmethod
  def fetch(cod):
    'Fetch a response by code, creating it (with simple default text) if it does not yet exist.'
    msg = StoredResponse.objects.filter(code = cod)
    if msg.count():
      return msg[0].text
    else:
      news  = StoredResponse(text = 'Error code: ' + cod, code = cod)
      news.save()
      return StoredResponse.fetch(cod)

class StoredSMS(models.Model):
  'Recording every SMS message that comes in. Very simple format.'
  message = models.TextField()
  sender  = models.TextField()
  when    = models.DateTimeField(auto_now_add = True)

class SMSError(models.Model):
  pass
  # TODO: link this to StoredSMS.
