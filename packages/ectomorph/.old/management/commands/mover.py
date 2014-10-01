from rapidsmsrw1000.apps.thoureport.reports.reports import *
from rapidsmsrw1000.settings import *

class Command(BaseCommand):
    help = 'Testing that the transfer program would work correctly.'

    def handle(self, **options):
      thid  = ThouReport.store({}, 'weird_testing_table')
      print 'Saved that as report number', thid
