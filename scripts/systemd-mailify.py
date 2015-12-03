#!/usr/bin/python2
#encoding=utf-8
from systemd import journal
from systemd import daemon
import ConfigParser
from mailify.loggger import Loggger
from mailify.logreader import LogReader
import os

if __name__ == "__main__":
    """
    __main__
    :desc: Somewhat main function though we are linux only
    based on user configuration starts the class
    """

    try:
        config = ConfigParser.RawConfigParser()
    except Exception as ex:
        template = "An exception of type {0} occured. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        journal.send("systemd-mailify: "+message)
        journal.send("systemd-mailify: ERROR"+" Could not parse\
                /etc/systemd-mailify.conf. Exiting...")
    try:
        config.read('/etc/systemd-mailify.conf')
    except Exception as ex:
        template = "An exception of type {0} occured. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        journal.send("systemd-mailify: "+message)
        journal.send("systemd-mailify: ERROR"+" Could not read\
                /etc/systemd-mailify.conf. Exiting...")
    try:
        config_logreader_start = config.getboolean("SYSTEMD-MAILIFY", "start")
    except Exception as ex:
        template = "An exception of type {0} occured. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        journal.send("systemd-mailify: "+message)
        journal.send("systemd-mailify: ERROR"+" Could not read\
                /etc/systemd-mailify.conf [SYSTEMD-MAILIFY] start value. Exiting...")

    if isinstance(config_logreader_start, bool) and config_logreader_start == True:
        loog = Loggger()
        lg = LogReader()
        pid = os.getpid()
        try:
            with open('/var/run/systemd-mailify.pid', 'w') as of:
                of.write(str(pid))
        except Exception as ex:
            templated = "An exception of type {0} occured. Arguments:\n{1!r}"
            messaged = templated.format(type(ex).__name__, ex.args)
            journal.send("systemd-mailify: "+messaged)
            if loog.logg == True and loog.logg_facility == "log_file" or loog.logg_facility == "both":
                loog.logging.error(message)
        finally:
            if loog.logg == True and loog.logg_facility == "log_file" or loog.logg_facility == "both":
                loog.logging.info("systemd-mailify started")
            daemon.notify(status="READY=1", unset_environment=False)
            lg.run()
