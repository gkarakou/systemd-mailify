#!/usr/bin/python2
#encoding=utf-8
from systemd import journal
import os
from .loggger import Loggger
from pwd import getpwnam

class SystemFuncs():
    def __init__(self):
        self.log_ger = Loggger()

    def get_conf_userid(self, name):
        """
        get_user
        :desc : Function that returns user id as int from config
        return int
        """

        try:
            username_to_id = getpwnam(name).pw_uid
        except Exception as ex:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            journal.send("systemd-mailify: Error getting uid from the username provided in the .conf"+ message)
        return username_to_id

    def get_euid(self):
        """
        get_euid_
        :desc : Function that returns effective user id as int
        return int
        """
        euid = os.geteuid()
        ppid = os.getpid()
        if self.log_ger.logg == True and self.log_ger.logg_facility == "log_file" and\
        self.log_ger.logg_level == 10:
            self.log_ger.logging.debug("Running inside get_euid(): euid == "+str(euid))
            self.log_ger.logging.debug("Running inside get_euid(): pid == "+str(ppid))
        return euid

    def set_euid(self, uid):
        """
        set_euid
        :desc : Function that sets effective user id
        return void
        :param uid int:
        """
        euid = int(uid)
        try:
            setuid = os.seteuid(euid)
        except Exception as ex:
            templat = "An exception of type {0} occured. Arguments:\n{1!r}"
            messag = templat.format(type(ex).__name__, ex.args)
            journal.send("systemd-mailify: Error setting euid " + messag)
        if setuid == None:
            if self.log_ger.logg == True:
                self.log_ger.logging.debug('Running inside set_euid() and trying to set effective uid: '+ str(self.get_euid()))
        else:
            if self.log_ger.logg == True and self.log_ger.logg_facility == "both":
                self.log_ger.logging.error("there is a problem setting the correct uid for the process to run as. Please check the unit file for the CAP_SETUID capability ")
                journal.send("systemd-mailify: there is a problem setting the correct uid for the process to run as. Please check the unit file for the CAP_SETUID capability ")
            elif self.log_ger.logg == True and self.log_ger.logg_facility == "log_file":
                self.log_ger.logging.error("there is a problem setting the correct uid for the process to run as. Please check the unit file for the CAP_SETUID capability ")

            else:
                journal.send("systemd-mailify: there is a problem setting the correct uid for the process to run as. Please check the unit file for the CAP_SETUID capability ")

    def get_egid(self):
        """
        get_egid_
        :desc : Function that returns effective gid as int
        return int
        """
        egid = os.getegid()
        if self.log_ger.logg == True and self.log_ger.logg_facility == "log_file" and\
        self.log_ger.logg_level == 10:
            self.log_ger.logging.debug("Running inside get_egid(): egid == "+str(egid))
        return egid

    def set_egid(self):
        """
        set_egid
        :desc : Function that sets effective gid to systemd-journal groups id
        return void
        """

        egid = 190
        gid = os.setegid(egid)
        if gid == None:
            if self.log_ger.logg == True:
                self.log_ger.logging.debug('Running inside set_egid() trying to egid=190 to the process: '+ str(self.get_egid()))
            else:
                pass
        else:
            if self.log_ger.logg == True and self.log_ger.logg_facility == "both":
                self.log_ger.logging.error("there is a problem setting the correct gid for the process to run as. Please check the unit file for the CAP_SETGID capability ")
                journal.send("systemd-mailify: there is a problem setting the correct gid for the process to run as. Please check the unit file for the CAP_SETGID capability ")
            elif self.log_ger.logg == True and self.log_ger.logg_facility == "log_file":
                self.log_ger.logging.error("there is a problem setting the correct gid for the process to run as. Please check the unit file for the CAP_SETGID capability ")
            else:
                journal.send("systemd-mailify: there is a problem setting the correct gid for the process to run as. Please check the unit file for the CAP_SETGID capability ")

