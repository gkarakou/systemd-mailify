#!/usr/bin/python2
#encoding=utf-8
from systemd import journal
#from .systemfuncs import SystemFuncs
import ConfigParser
from pwd import getpwnam
import os
import logging

class Loggger():
    """
    """

    def __init__(self):

        conf = ConfigParser.RawConfigParser()
        conf.read('/etc/systemd-mailify.conf')
        user = conf.get("SYSTEMD-MAILIFY", "user")
        if len(user) == 0:
            user = "root"
        log = conf.get("LOGGING", "log")
        if log == "log_file":
            self.logg_facility = "log_file"
        elif log == "journal":
            self.logg_facility = "journal"
        else:
            self.logg_facility = "both"
        try:
            uid = getpwnam(user).pw_uid
        except Exception as ex:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            journal.send("systemd-mailify: Error getting uid from the username provided in the .conf"+ message)
        gid = 0
        if log == "log_file" or log == "both":
            if  os.path.isfile("/var/log/systemd-mailify.log"):
                try:
                    os.chown("/var/log/systemd-mailify.log", uid, gid)
                    os.chmod("/var/log/systemd-mailify.log", 436)
                except Exception as ex:
                    template = "An exception of type {0} occured. Arguments:\n{1!r}"
                    message = template.format(type(ex).__name__, ex.args)
                    journal.send("systemd-mailify: "+ message)
                    journal.send("systemd-mailify: there is a problem chowning/chmoding the log file. Please check the unit file for the CAP_CHOWN/CAP_FOWNER capability ")
            else:
                #create log file and chown/chmod
                try:
                    with open('/var/log/systemd-mailify.log', 'a+') as f:
                        f.write()
                except Exception as ex:
                    template = "An exception of type {0} occured. Arguments:\n{1!r}"
                    message = template.format(type(ex).__name__, ex.args)
                try:
                    os.chown("/var/log/systemd-mailify.log", uid, gid)
                    os.chmod("/var/log/systemd-mailify.log", 436)
                except Exception as ex:
                    template = "An exception of type {0} occured. Arguments:\n{1!r}"
                    message = template.format(type(ex).__name__, ex.args)
                    journal.send("systemd-mailify: "+ message)
                    journal.send("systemd-mailify: there is a problem chowning/chmoding the log file. Please check the unit file for the CAP_CHOWN/CAP_FOWNER capability ")
            self.logg = True
        else:
            #journal logging
            self.logg = False
        log_level = conf.get("LOGGING", "log_level")
        str_to_num = {"ERROR":40, "CRITICAL":50, "DEBUG":10, "INFO":20, "WARNING":30}
        for key, value in str_to_num.iteritems():
            if log_level == key:
                self.logg_level = value
        if log == "log_file" or log == "both":
            formatter = '%(asctime)s %(levelname)s %(message)s'
            logging.basicConfig(filename='/var/log/systemd-mailify.log', level=self.logg_level, format=formatter)
            self.logging = logging
        else:
            self.logging = None
