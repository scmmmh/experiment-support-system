import time
import sys
from threading import Thread
from pyquest.models import DBSession, Survey

class Notifier(Thread):

    def __init__(self, dbsession):
        self.dbsession = dbsession
        Thread.__init__(self)

    def run(self):
        while self.carryon == True:
#            surveys = self.dbsession.query(Survey).filter(Survey.status=='running').all()
#            sys.stderr.write('AHA' + surveys + '\n')
#            for survey in surveys:
#                sys.stderr.write('Survey "%s" belonging to %s is running.\n' % (survey.title, survey.owner.name))
            sys.stderr.write('ahahahaha\n')
            time.sleep(15)

    def start(self):
        self.carryon = True
        Thread.start(self)

    def stop(self):
        self.carryon = False

    
        
