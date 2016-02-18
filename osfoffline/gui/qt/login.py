import logging
import sys
import urllib

from PyQt5.QtWidgets import QDialog, QInputDialog, QMessageBox

from sqlalchemy.orm.exc import NoResultFound
from urllib.request import urlopen
from urllib.error import URLError

from osfoffline import language
from osfoffline.database import Session
from osfoffline.database.models import User
from osfoffline.database.utils import save
from osfoffline.exceptions import AuthError, TwoFactorRequiredError
from osfoffline.utils.internetchecker import InternetChecker
from osfoffline.utils.authentication import AuthClient
from osfoffline.utils.log import add_user_to_sentry_logs
from osfoffline.gui.qt.generated.login import Ui_login

logger = logging.getLogger(__name__)


class LoginScreen(QDialog, Ui_login):
    def __init__(self):
        super().__init__()
        self.user = None
        self.setupUi(self)
        self.logInButton.clicked.connect(self.login)

    def get_user(self):
        try:
            self.user = Session().query(User).one()
            try:
                urlopen("http://www.google.com")
            except URLError:
                logger.info('Internet is down')
                InternetChecker().start()
            else:
                logger.info("Internet is up and running.")
                self.user = AuthClient().populate_user_data(self.user)
                save(Session(), self.user)
        except AuthError:
            self.usernameEdit.setText(self.user.login)
            self.passwordEdit.setFocus()
        except NoResultFound:
            self.usernameEdit.setFocus()
        else:
            # Add the user id of the logged in user to Sentry logs
            add_user_to_sentry_logs()
            return self.user

        self.exec_()

        if self.user:
            # Add the user id of the logged in user to Sentry logs
            add_user_to_sentry_logs()

        return self.user

    def login(self, *, otp=None):
        logger.debug('attempting to log in')
        username = self.usernameEdit.text()
        password = self.passwordEdit.text()
        auth_client = AuthClient()

        try:
            self.user = auth_client.login(username=username, password=password, otp=otp)
        except TwoFactorRequiredError:
            # Prompt user for 2FA code, then re-try authentication
            otp_val, ok = QInputDialog.getText(self, 'Enter one-time code',
                                               language.TFA_PROMPT)
            if ok:
                return self.login(otp=otp_val)
        except AuthError as e:
            logger.exception(e.message)
            QMessageBox.warning(None, 'Login Failed', e.message)
            # self.start_screen.logInButton.setEnabled(True)
        else:
            logger.info('Successfully logged in user: {}'.format(self.user))
            self.accept()

    def closeEvent(self, event):
        sys.exit(1)
