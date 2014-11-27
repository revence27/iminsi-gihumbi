from django.core.management.base import BaseCommand
from django.conf import settings
from rapidsmsrw1000.apps.thoureport.reports.reports import *

class Command(BaseCommand):
    help = 'Testing that the transfer program would work correctly.'

    def handle(self, **options):
      thid  = ThouReport.store({}, 'weird_testing_table')
      print 'Saved that as report number', thid
