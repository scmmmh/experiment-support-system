import time
import sys
from threading import Thread
from pyquest.models import DBSession, Survey, Participant
from email.mime.text import MIMEText
import smtplib

class Notifier(Thread):

    really = False

    def __init__(self, settings):
        sys.stderr.write('Notifier.__init__\n')
        self.smtp_host = settings['email.smtp_host']
        Thread.__init__(self)

    def run(self):
        while self.carryon == True:
            sys.stderr.write('run start\n')
            dbsession = DBSession()
            surveys = dbsession.query(Survey).filter(Survey.status=='running').all()
            sys.stderr.write('There are %d running surveys.\n' % len(surveys))
            for survey in surveys:
                if len(survey.notifications) > 0:
                    for notification in survey.notifications:
                        response = notification.respond(dbsession)
                        if response['message']:
                            sys.stderr.write(response['message'])
                            self.sendmail(response)
                        else:
                            sys.stderr.write('Notification gave no response.\n')
                else:
                    sys.stderr.write('Survey "%s" has no notifications\n' % survey.title)
            sys.stderr.write('run end\n')
            dbsession.close()
            time.sleep(15)

    def start(self):
        sys.stderr.write('Notifier.start\n')
        self.carryon = True
        Thread.start(self)

    def stop(self):
        sys.stderr.write('Notifier.stop\n')
        self.carryon = False

    def sendmail(self, response):
        message = response['message']
        if self.really:
            for address in response['addresses']:
                email = MIMEText(message)
                email['Subject'] = 'Notification of survey status'
                email['From'] = 'noreply@paths.sheffield.ac.uk'
                email['To'] = address
                smtp = smtplib.SMTP(self.smtp_host)
                smtp.sendmail('noreply@paths.sheffield.ac.uk', address, email.as_string())
                smtp.quit()

        
