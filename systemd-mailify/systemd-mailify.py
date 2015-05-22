#!/usr/bin/python2
import threading
import time
import datetime
import select
from systemd import journal
from threading import Thread
import ConfigParser
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class LogReader(threading.Thread):
    """
    LogReader
    :desc: Class that notifies the user for failed systemd services
    Extends threading.Thread
    Has an constructor that calls the parent one, a run method and a destructor
    """

    def __init__(self):
        """
        __init__
        return parent constructor
        """
        Thread.__init__(self)

    def parse_config(self):
        conf = ConfigParser.RawConfigParser()
        conf.read('/etc/systemd-mailify.conf')
        subject = conf.get("JournalReader", "subject")
        host = conf.get("JournalReader", "smtp")
        config_message = conf.get("JournalReader", "message")
        mail_from = conf.get("JournalReader", "mail_from")
        mail_to = conf.get("JournalReader", "mail_to")
        auth_user = conf.get("JournalReader", "auth_user")
        auth_password = conf.get("JournalReader", "auth_password")
        conf_dict = {}
        conf_dict['subject'] = subject
        conf_dict['host'] = host
        conf_dict['config_message'] = config_message
        conf_dict['mail_to'] = mail_to
        conf_dict['mail_from'] = mail_from
        conf_dict['auth_user'] = auth_user
        conf_dict['auth_password'] = auth_password
        return conf_dict

    def run(self):
        """
        run
        return void
        :desc: function that goes on an infinite loop polling the systemd-journal for failed services
        Helpful API->http://www.freedesktop.org/software/systemd/python-systemd/
        """
        dictionary = self.parse_config()
        j_reader = journal.Reader()
        j_reader.log_level(journal.LOG_INFO)
        # j.seek_tail() #faulty->doesn't move the cursor to the end of journal

        # it is questionable whether there is actually a record with the real
        # datetime we provide but we assume it moves the cursor to somewhere
        # near the end of the journal fd
        j_reader.seek_realtime(datetime.datetime.now())
        poller = select.poll()
        poller.register(j_reader, j_reader.get_events())
        while poller.poll():
            #next is a debugging call
            # if it prints True it is pollable
            #reliable = j.reliable_fd()
            #print reliable
            waiting = j_reader.process()
            # if JOURNAL append or JOURNAL logrotate
            if waiting == 1 or waiting == 2:
                j_reader.get_next()
                for entry in j_reader:
                    if 'MESSAGE' in entry:
                        pattern = "entered failed state"
                        try:
                            string = entry['MESSAGE']
                            if string and pattern in string:
                                msg = MIMEMultipart('alternative')
                                msg['Subject'] = dictionary['subject']
                                msg['From'] = dictionary['mail_from']
                                msg['To'] = dictionary['mail_to']
                                # Record the MIME types of parts - text/plain.
                                part1 = MIMEText(dictionary['config_message'], 'plain')
                                part2 = MIMEText(string, 'plain')
                                msg.attach(part1)
                                msg.attach(part2)
                                if dictionary['auth_user'] and dictionary['auth_password']:
                                    try:
                                        s = smtplib.SMTP(dictionary['host'])
                                        s.sendmail(msg['From'], msg['To'], msg.as_string())
                                        s.quit()
                                    except Exception as ex:
                                        template = "An exception of type {0} occured. Arguments:\n{1!r}"
                                        message = template.format(type(ex).__name__, ex.args)
                                        journal.send("systemd-mailify: "+message)
                                else:
                                    try:
                                        s = smtplib.SMTP(dictionary['host'])
                                        s.login(dictionary['auth_user'], dictionary['auth_password'])
                                        s.sendmail(msg['From'], msg['To'], msg.as_string())
                                        s.quit()
                                    except Exception as ex:
                                        template = "An exception of type {0} occured. Arguments:\n{1!r}"
                                        message = template.format(type(ex).__name__, ex.args)
                                        journal.send("systemd-mailify: "+message)
                            else:
                                continue
                        except Exception as ex:
                            template = "An exception of type {0} occured. Arguments:\n{1!r}"
                            message = template.format(type(ex).__name__, ex.args)
                            journal.send("systemd-mailify: "+message)
                    else:
                        continue
            else:
                pass
            continue

    def __del__(self):
        """__del__
        return parent destructor or del objects
        :desc: destructor function that wont run because the gc will run first, but we provide it for completeness
        """
        if callable(getattr(threading.Thread, "__del__")):
            super.__del__()
            return
        else:
            del self.run
            return


if __name__ == "__main__":
    """
    __main__
    :desc: Somewhat main function though we are linux only
    based on user configuration starts classes
    """

    try:
        config = ConfigParser.RawConfigParser()
    except Exception as ex:
        template = "An exception of type {0} occured. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        journal.send("systemd-mailify: "+message)
    try:
        config.read('/etc/systemd-mailify.conf')
    except Exception as ex:
        template = "An exception of type {0} occured. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        journal.send("systemd-mailify: "+message)
    try:
        config_logreader_start = config.getboolean("JournalReader", "start")
    except Exception as ex:
        template = "An exception of type {0} occured. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        journal.send("systemd-mailify: "+message)

    if isinstance(config_logreader_start, bool) and config_logreader_start == True:
        lg = LogReader()
        lg.daemon = True
        lg.start()
