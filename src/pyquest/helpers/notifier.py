import time
import sys
from threading import Thread
from pyquest.models import DBSession, Survey


class Notifier(Thread):

    _surveys = None

    def __init__(self, settings):
        sys.stderr.write('Notifier.__init__\n')
        self.smtp_host = settings['email.smtp_host']
        Thread.__init__(self)

    def run(self):
        while self.carryon == True:
            sys.stderr.write('run start\n')
            dbsession = DBSession()
            surveys = dbsession.query(Survey).all()
            if self._surveys:
                for survey in surveys:
                    if survey.status == 'running':
                        for _survey in self._surveys:
                            old_survey = None
                            if _survey.id == survey.id:
                                old_survey = _survey
                                break
                        if old_survey and old_survey.status != 'running':
                            sys.stderr.write('Survey "%s" has started running\n' % survey.title)
            self._surveys = surveys
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

    def sendmail(user, subject, message):
        email = MIMEText(message)
        email['Subject'] = subject
        email['From'] = 'noreply@paths.sheffield.ac.uk'
        email['To'] = user.email
        smtp = smtplib.SMTP(self.smtp_host)
        smtp.sendmail('noreply@paths.sheffield.ac.uk', user.email, email.as_string())
        smtp.quit()

        
