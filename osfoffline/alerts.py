__author__ = 'himanshu'
from PyQt5.QtWidgets import QSystemTrayIcon
from queue import Queue
from datetime import datetime, timedelta
class AlertHandler(object):

    show_alerts = True

    DOWNLOAD = 0
    UPLOAD = 1
    MODIFYING = 2
    DELETING = 3
    MOVING = 4

    ALERT_TIME = 1000


    alert_icon = None

    last_alert_time = None
    alert_queue = Queue()


    @classmethod
    def setup_alerts(cls, system_tray_icon):
        cls.alert_icon = system_tray_icon
        if not cls.alert_icon.supportsMessages():
            cls.show_alerts = False

    @classmethod
    def alert_running(cls):
        cur_time = datetime.now()
        if not cls.last_alert_time:
            return False
        return cur_time - cls.last_alert_time < timedelta(milliseconds=cls.ALERT_TIME)

    @classmethod
    def run_alert(cls, alert_title, alert_message):
        cls.alert_icon.showMessage(
                    alert_title,
                    alert_message,
                    QSystemTrayIcon.NoIcon,
                    msecs=cls.ALERT_TIME  # fixme: currently, I have NO control over duration of alert. I think this is only for linux... hopefully.
        )
        cls.last_alert_time = datetime.now()

    @classmethod
    def clear_queue(cls):
        # clear the queue in a thread safe manner.
        with cls.alert_queue.mutex:
            cls.alert_queue.queue.clear()

    @classmethod
    def info(cls, file_name, action):
        if cls.alert_icon is None or not cls.show_alerts:
            return
        else:
            title = {
                cls.DOWNLOAD: "Downloading",
                cls.UPLOAD: "Uploading",
                cls.MODIFYING: "Modifying",
                cls.DELETING: "Deleting",
            }

            text = "{} {}".format(title[action], file_name)
            alert_tuple = (text, "- OSF Offline")
            if cls.alert_icon.supportsMessages():
                """Idea is that if there is an alert already running, we will IGNORE the new alert.
                   Don't want to queue them up and run them one by one because a queued alert could be outdated.
                   Don't want to give a 'updating x files' alert because
                """
                if cls.alert_running():
                    cls.alert_queue.put_nowait(alert_tuple)
                else:
                    if cls.alert_queue.empty():
                        cls.run_alert(alert_tuple[0], alert_tuple[1])
                    elif datetime.now() - cls.last_alert_time < timedelta(milliseconds=cls.ALERT_TIME * 3 ) :  # last alert was recent
                        cls.run_alert('Updating {} files'.format(cls.alert_queue.qsize() + 1), "Check <a href='www.osf.io'>www.osf.io</a> for details.")
                        cls.clear_queue()
                    else:
                        cls.run_alert(alert_tuple[0], alert_tuple[1])
                        cls.clear_queue()

            else:
                cls.show_alerts = False