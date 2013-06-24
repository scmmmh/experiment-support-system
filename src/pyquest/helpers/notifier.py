import time
import sys
import transaction

from threading import Thread
from pyquest.models import DBSession, Survey, Participant
from email.mime.text import MIMEText
import smtplib

class Notifier(Thread):

    #for testing the thread sleeps for one minute, for real one hour is probably more appropriate
    interval = 60
    #interval = 3600

    def __init__(self, settings):
        self.smtp_host = settings['email.smtp_host']
        Thread.__init__(self)

    def run(self):
        while self.carryon == True:
            time.sleep(self.interval)
            dbsession = DBSession()
            surveys = dbsession.query(Survey).filter(Survey.status=='running').all()
            for survey in surveys:
                if len(survey.notifications) > 0:
                    with transaction.manager:
                        dbsession.add(survey)
                        for notification in survey.notifications:
                            dbsession.add(notification)
                            response = notification.respond(dbsession)
                            if response['message']:
                                self.sendmail(response)
                                notification.timestamp = int(time.time())
                                dbsession.flush()
            dbsession.close()

    def start(self):
        self.carryon = True
        Thread.start(self)

    def stop(self):
        self.carryon = False

    def sendmail(self, response):
        message = response['message']
        for address in response['addresses']:
            email = MIMEText(message)
            email['Subject'] = 'Notification of survey status'
            email['From'] = 'noreply@paths.sheffield.ac.uk'
            email['To'] = address
            smtp = smtplib.SMTP(self.smtp_host)
            smtp.sendmail('noreply@paths.sheffield.ac.uk', address, email.as_string())
            smtp.quit()

        
