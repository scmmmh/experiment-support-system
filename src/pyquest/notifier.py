import smtplib
import time
import transaction

from email.mime.text import MIMEText
from threading import Thread

from pyquest.models import DBSession, Survey

class Notifier(Thread):

    def __init__(self, settings):
        Thread.__init__(self)
        if 'email.smtp_host' in settings and 'email.sender' in settings:
            self.smtp_host = settings['email.smtp_host']
            self.from_field = settings['email.sender']
            if 'notifier.interval' in settings:
                self.interval = int(settings['notifier.interval'])
            else:
                self.interval = 3600
            if 'notifier.time_factor' in settings:
                self.time_factor = int(settings['notifier.time_factor'])
            else:
                self.time_factor = 3600 * 24
        else:
            self.smtp_host = None
            self.from_field = None

    def run(self):
        if self.smtp_host and self.from_field:
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
                                response = notification.respond(dbsession, self.time_factor)
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
            email['Subject'] = 'Notification of experiment status'
            email['From'] = self.from_field
            email['To'] = address
            smtp = smtplib.SMTP(self.smtp_host)
            smtp.sendmail(self.from_field, address, email.as_string())
            smtp.quit()

        
