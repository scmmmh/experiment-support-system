import time
import sys
from threading import Thread
from pyquest.models import DBSession, Survey

class Notifier(Thread):

    def __init__(self):
        sys.stderr.write('Notifier.__init__\n')
        Thread.__init__(self)

    def run(self):
        while self.carryon == True:
            sys.stderr.write('run start\n')
            dbsession = DBSession()
            surveys = dbsession.query(Survey).filter(Survey.status=='running').all()
            for survey in surveys:
                sys.stderr.write('Survey "%s" belonging to %s is running.\n' % (survey.title, survey.owner.username))
            sys.stderr.write('run end\n')
            time.sleep(15)

    def start(self):
        sys.stderr.write('Notifier.start\n')
        self.carryon = True
        Thread.start(self)

    def stop(self):
        sys.stderr.write('Notifier.stop\n')
        self.carryon = False

    
        
