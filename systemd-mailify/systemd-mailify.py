#!/usr/bin/python2
#encoding=utf-8
import datetime
import select
from systemd import journal
from Queue import Queue
from threading import Thread
import multiprocessing
import ConfigParser
import smtplib
import email.utils
import os
import sys
from pwd import getpwnam
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging


class LogReader(multiprocessing.Process):
    """
    LogReader
    :desc: Class that mails a user for failed systemd services
    Extends multiprocessing.Process
    Implements(! interface) a mail worker thread that is spawned to mail failed services. A queue
    is used for notifying the parent process about which tasks were sucessful
    """

    def __init__(self):
        """
        __init__
        :desc: constructor method
        Calls parent and then reads .conf for the global session
        Creates and chowns/chmods the log file if log_file is enabled
        Creates some members to be used in the instance about logging
        """
        super(LogReader, self).__init__()
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
        uid = self.get_conf_userid(user)
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
                    journal.send("systemd-mailify: "+ message)
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

    def get_euid(self):
        """
        get_euid_
        :desc : Function that returns effective user id as int
        return int
        """
        uid = os.geteuid()
        ppid = os.getpid()
        if self.logg == True and self.logg_facility == "log_file" and\
        self.logg_level == 10:
            self.logging.debug("Running inside get_euid: uid == "+str(uid))
            self.logging.debug("Running inside get_euid: pid == "+str(ppid))
        return uid

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
            if self.logg == True:
                self.logging.debug('Running inside set_euid and trying to set effective uid: '+ str(self.get_euid()))
        else:
            if self.logg == True and self.logg_facility == "both":
                self.logging.error("there is a problem setting the correct uid for the process to run as. Please check the unit file for the CAP_SETUID capability ")
                journal.send("systemd-mailify: there is a problem setting the correct uid for the process to run as. Please check the unit file for the CAP_SETUID capability ")
            elif self.logg == True and self.logg_facility == "log_file":
                self.logging.error("there is a problem setting the correct uid for the process to run as. Please check the unit file for the CAP_SETUID capability ")

            else:
                journal.send("systemd-mailify: there is a problem setting the correct uid for the process to run as. Please check the unit file for the CAP_SETUID capability ")




    def get_egid(self):
        """
        get_egid_
        :desc : Function that returns effective gid as int
        return int
        """
        gid = os.getgid()
        return gid

    def set_egid(self):
        """
        set_egid
        :desc : Function that sets effective gid to systemd-journal groups id
        return void
        """

        egid = 190
        gid = os.setegid(egid)
        if gid == None:
            if self.logg == True:
                self.logging.debug('setting gid: '+ str(self.get_egid()))
            else:
                pass
        else:
            if self.logg == True and self.logg_facility == "both":
                self.logging.error("there is a problem setting the correct gid for the process to run as. Please check the unit file for the CAP_SETGID capability ")
                journal.send("systemd-mailify: there is a problem setting the correct gid for the process to run as. Please check the unit file for the CAP_SETGID capability ")
            elif self.logg == True and self.logg_facility == "log_file":
                self.logging.error("there is a problem setting the correct gid for the process to run as. Please check the unit file for the CAP_SETGID capability ")
            else:
                journal.send("systemd-mailify: there is a problem setting the correct gid for the process to run as. Please check the unit file for the CAP_SETGID capability ")

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
            journal.send("systemd-mailify: Error getting uid from the username provided in the .conf")
        return username_to_id


    def parse_config(self):
        """
        parse_config
        :desc : Function that returns a dictionary containing all the values
        from the /etc/systemd-mailify.conf file (minus the global section)
        return dict
        """
        conf = ConfigParser.RawConfigParser()
        conf.read('/etc/systemd-mailify.conf')

        #parse [EMAIL]

        conf_dict = {}
        user = conf.get("SYSTEMD-MAILIFY", "user")
        if len(user) == 0:
            user = "root"
        subject = conf.get("EMAIL", "subject")
        if len(subject) == 0:
            subject = "systemd-mailify"
        mail_from = conf.get("EMAIL", "mail_from")
        mail_to = conf.get("EMAIL", "mail_to")
        conf_dict['user'] = user
        conf_dict['email_subject'] = subject
        conf_dict['email_to'] = mail_to
        conf_dict['email_from'] = mail_from

        #parse [AUTH]

        auth = conf.getboolean("AUTH", "active")
        if auth and auth == True:
            auth_user = conf.get("AUTH", "auth_user")
            if len(auth_user) == 0:
                if self.logg == True and self.logg_facility == "both":
                    self.logging.error("You have asked for authentication but you have an empty auth_user name. Please update the /etc/systemd-mailify.conf file with a value ")
                    journal.send("systemd-mailify: ERROR You have asked for authentication but you have an empty auth_user name. Please update the /etc/systemd-mailify.conf file with a value ")
                elif self.logg == True and self.logg_facility == "log_file":
                    self.logging.error("You have asked for authentication but you have an empty auth_user name. Please update the /etc/systemd-mailify.conf file with a value ")
                else:
                    journal.send("systemd-mailify: ERROR You have asked for authentication but you have an empty auth_user name. Please update the /etc/systemd-mailify.conf file with a value ")
                sys.exit(1)
            auth_password = conf.get("AUTH", "auth_password")
            if len(auth_password) == 0:
                if self.logg == True and self.logg_facility == "both":
                    self.logging.error("You have asked for authentication but you have an empty auth_password field. Please update the /etc/systemd-mailify.conf file with a value ")
                    journal.send("systemd-mailify: ERROR You have asked for authentication but you have an empty auth_password field. Please update the /etc/systemd-mailify.conf file with a value ")
                elif self.logg == True and self.logg_facility == "log_file":
                    self.logging.error("You have asked for authentication but you have an empty auth_password field. Please update the /etc/systemd-mailify.conf file with a value ")
                else:
                    journal.send("systemd-mailify: ERROR You have asked for authentication but you have an empty auth_password field. Please update the /etc/systemd-mailify.conf file with a value ")
                sys.exit(1)
            conf_dict['auth'] = True
            conf_dict['auth_user'] = auth_user
            conf_dict['auth_password'] = auth_password
        else:
            conf_dict['auth'] = False

        #parse [SMTP]
        smtp = conf.getboolean("SMTP", "active")
        if smtp and smtp == True:
            conf_dict['smtp'] = True
        else:
            conf_dict['smtp'] = False
        smtp_host = conf.get("SMTP", "host")
        if len(smtp_host) == 0:
            smtp_host = "localhost"
            if self.logg == True and self.logg_facility == "both":
                self.logging.info("You have asked for smtp connection but you have an empty smtp host field. Please update the /etc/systemd-mailify.conf file with a value. We assume localhost here")
                journal.send("systemd-mailify: INFO You have asked for a smtp connection but you have an empty smtp host field. Please update the /etc/systemd-mailify.conf file with a value. We assume localhost here")
            elif self.logg == True and self.logg_facility == "log_file":
                self.logging.info("You have asked for smtp connection but you have an empty smtp host field. Please update the /etc/systemd-mailify.conf file with a value. We assume localhost here")
            else:
                journal.send("systemd-mailify: INFO You have asked for a smtp  connection but you have an empty smtp host field. Please update the /etc/systemd-mailify.conf file with a value. We assume localhost here")
        conf_dict['smtp_host'] = smtp_host
        smtp_port = conf.getint("SMTP", "port")
        if not smtp_port:
            smtp_port = 25
            if self.logg == True and self.logg_facility == "both":
                self.logging.error("You have asked for smtp connection but you have an empty smtp port field. Please update the /etc/systemd-mailify.conf file with a value. port=25")
                journal.send("systemd-mailify: ERROR You have asked for a smtp connection but you have an empty smtp port  field. Please update the /etc/systemd-mailify.conf file with a value. port=25 ")
            elif self.logg == True and self.logg_facility == "log_file":
                self.logging.error("You have asked for smtp connection but you have an empty smtp port field. Please update the /etc/systemd-mailify.conf file with a value. port=25")
            else:
                journal.send("systemd-mailify: ERROR You have asked for a smtp connection but you have an empty smtp port field. Please update the /etc/systemd-mailify.conf file with a value. port=25 ")

        conf_dict['smtp_port'] = smtp_port

        #parse [SMTPS]
        smtps = conf.getboolean("SMTPS", "active")
        if smtps == True:
            conf_dict['smtps'] = True
            smtps_host = conf.get("SMTPS", "host")
            if len(smtps_host) == 0:
                smtps_host = "localhost"
                if self.logg == True and self.logg_facility == "both":
                    self.logging.info("You have asked for smtps connection but you have an empty smtps host field. Please update the /etc/systemd-mailify.conf file with a value. We assume localhost here")
                    journal.send("systemd-mailify: INFO You have asked for a smtps connection but you have an empty smtps host field. Please update the /etc/systemd-mailify.conf file with a value. We assume localhost here")
                elif self.logg == True and self.logg_facility == "log_file":
                    self.logging.info("You have asked for smtps connection but you have an empty smtps host field. Please update the /etc/systemd-mailify.conf file with a value. We assume localhost here")
                else:
                    journal.send("systemd-mailify: INFO You have asked for a smtps connection but you have an empty smtps host field. Please update the /etc/systemd-mailify.conf file with a value. We assume localhost here")
            conf_dict['smtps_host'] = smtps_host
            smtps_port = conf.getint("SMTPS", "port")
            if not smtps_port:
                smtps_port = 465
                if self.logg == True and self.logg_facility == "both":
                    self.logging.error("You have asked for smtps connection but you have an empty smtps port field. Please update the /etc/systemd-mailify.conf file with a value. port=465 ")
                    journal.send("systemd-mailify: ERROR You have asked for a  smtps connection but you have an empty smtps port field. Please update the /etc/systemd-mailify.conf file with a value. port=465")
                elif self.logg == True and self.logg_facility == "log_file":
                    self.logging.error("You have asked for smtps connection but you have an empty smtps port field. Please update the /etc/systemd-mailify.conf file with a value. port=465")
                else:
                    journal.send("systemd-mailify: ERROR You have asked for a smtps connection but you have an empty smtps port field. Please update the /etc/systemd-mailify.conf file with a value. port=465 ")
            conf_dict['smtps_port'] = smtps_port
            smtps_cert = conf.get("SMTPS", "cert_file")
            conf_dict['smtps_cert'] = smtps_cert
            smtps_key = conf.get("SMTPS", "key_file")
            conf_dict['smtps_key'] = smtps_key
        else:
            conf_dict['smtps'] = False

        #parse [STARTTLS]
        starttls = conf.getboolean("STARTTLS", "active")
        if  starttls == True:
            conf_dict['starttls'] = True
            starttls_host = conf.get("STARTTLS", "host")
            if len(starttls_host) == 0:
                starttls_host = "localhost"
                if self.logg == True and self.logg_facility == "both":
                    self.logging.info("You have asked for starttls connection but you have an empty starttls host field. Please update the /etc/systemd-mailify.conf file with a value. We assume localhost here")
                    journal.send("systemd-mailify: INFO You have asked for a starttls connection but you have an empty starttls host field. Please update the /etc/systemd-mailify.conf file with a value. We assume localhost here")
                elif self.logg == True and self.logg_facility == "log_file":
                    self.logging.info("You have asked for starttls connection but  you have an empty starttls host field. Please update the /etc/systemd-mailify.conf file with a value. We assume localhost here")
                else:
                    journal.send("systemd-mailify: INFO You have asked for a starttls connection but you have an empty starttls host field. Please update the /etc/systemd-mailify.conf file with a value. We assume localhost here")
            conf_dict['starttls_host'] = starttls_host
            starttls_port = conf.getint("STARTTLS", "port")
            if not starttls_port:
                starttls_port = 587
                if self.logg == True and self.logg_facility == "both":
                    self.logging.error("You have asked for starttls connection but you have an empty starttls port field. Please update the /etc/systemd-mailify.conf file with a value. port=587")
                    journal.send("systemd-mailify: ERROR You have asked for a starttls connection but you have an empty starttls port field. Please update the /etc/systemd-mailify.conf file with a value. port=587")
                elif self.logg == True and self.logg_facility == "log_file":
                    self.logging.error("You have asked for starttls connection but you have an empty starttls port field. Please update the /etc/systemd-mailify.conf file with a value. port=587 ")
                else:
                    journal.send("systemd-mailify: ERROR You have asked for a starttls connection but you have an empty starttls port field. Please update the /etc/systemd-mailify.conf file with a value.port= 587")
            conf_dict['starttls_port'] = starttls_port
            starttls_cert = conf.get("STARTTLS", "cert_file")
            conf_dict['starttls_cert'] = starttls_cert
            starttls_key = conf.get("STARTTLS", "key_file")
            conf_dict['starttls_key'] = starttls_key
        else:
            conf_dict['starttls'] = False
        #iter through dict sections and check whether there are empty values
        if self.logg == True and self.logg_facility == "log_file" and\
        self.logg_level == 10:
            for key, val in conf_dict.iteritems():
                self.logging.debug("config_file: entry == " + str(key)+ " value == "+ str(val))
        return conf_dict


    def mail_worker(self, stri, que, dictio):
        """
        mail_worker
        :desc : Function that does the heavy lifting
        :params : The string to be mailed, a queue object to put messages in it
        to notify the parent process about the status of the mail, and a dict
        containing config options necessary for the mail to be delivered.
        """

        if self.logg == True and self.logg_facility == "log_file" and\
        self.logg_level == 10:
            self.logging.debug('Running inside mail_worker()')
        dictionary = dictio
        msg = MIMEMultipart("alternative")
        #get it from the queue?
        stripped = stri.strip()
        part1 = MIMEText(stripped, "plain")
        msg['Subject'] = dictionary['email_subject']
        #http://pymotw.com/2/smtplib/
        msg['To'] = email.utils.formataddr(('Recipient', dictionary['email_to']))
        msg['From'] = email.utils.formataddr((dictionary['email_from'], dictionary['email_from']))
        msg.attach(part1)
        if dictionary['smtp'] == True:
            # no auth
            if dictionary['auth'] == False:
                s = smtplib.SMTP()
                s.connect(host=str(dictionary['smtp_host']), port=dictionary['smtp_port'])
                try:
                    send = s.sendmail(str(dictionary['email_from']), [str(dictionary['email_to'])], msg.as_string())
                    if isinstance(send, dict):
                        que.put([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "SUCCESS"])
                    else:
                        que.put([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "FAILURE"])
                except Exception as ex:
                    template = "An exception of type {0} occured. Arguments:\n{1!r}"
                    message = template.format(type(ex).__name__, ex.args)
                    journal.send("systemd-mailify: "+message)
                    if self.logg == True and self.logg_facility == "log_file" or self.logg_facility == "both":
                        self.logging.error(message)
                finally:
                    s.quit()
                    del s

            # auth
            elif dictionary['auth'] == True:
                s = smtplib.SMTP()
                s.connect(host=str(dictionary['smtp_host']), port=dictionary['smtp_port'])
                s.login(str(dictionary['auth_user']), str(dictionary['auth_password']))
                try:
                    send = s.sendmail(str(dictionary['email_from']), [str(dictionary['email_to'])], msg.as_string().strip())
                    if isinstance(send, dict):
                        que.put([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "SUCCESS"])
                    else:
                        que.put([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "FAILURE"])
                except Exception as ex:
                    template = "An exception of type {0} occured. Arguments:\n{1!r}"
                    message = template.format(type(ex).__name__, ex.args)
                    journal.send("systemd-mailify: "+message)
                    if self.logg == True and self.logg_facility == "log_file" or self.logg_facility == "both":
                        self.logging.error(message)
                finally:
                     s.quit()
                     del s
            else:
                pass
        #smtps
        if dictionary['smtps'] == True:
            # no auth ?
            if  dictionary['auth'] == False:
                try:
                    if len(dictionary['smtps_cert']) >0 and len(dictionary['smtps_key'])>0:
                        s = smtplib.SMTP_SSL(host=str(dictionary['smtps_host']), port=dictionary['smtps_port'], keyfile=dictionary['smtps_key'], certfile=dictionary['smtps_cert'])
                        s.ehlo_or_helo_if_needed()
                        send = s.sendmail(str(dictionary['email_from']), [str(dictionary['email_to'])], msg.as_string())
                        if isinstance(send, dict):
                            que.put([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "SUCCESS"])
                        else:
                            que.put([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "FAILURE"])
                    else:
                        s = smtplib.SMTP_SSL(host=str(dictionary['smtps_host']), port=dictionary['smtps_port'])
                        s.ehlo_or_helo_if_needed()
                        send = s.sendmail(str(dictionary['email_from']), [str(dictionary['email_to'])], msg.as_string())
                        if isinstance(send, dict):
                            que.put([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "SUCCESS"])
                        else:
                            que.put([datetime.datetime.now().strftime("%Y-%m-%d\
                                %H:%M:%S"), "FAILURE"])
                except Exception as ex:
                    template = "An exception of type {0} occured. Arguments:\n{1!r}"
                    message = template.format(type(ex).__name__, ex.args)
                    journal.send("systemd-mailify: "+message)
                    if self.logg == True and self.logg_facility == "log_file" or self.logg_facility == "both":
                        self.logging.error(message)
                finally:
                    s.quit()
                    del s
            # auth
            elif dictionary['auth'] == True:
                try:
                    #check whether it is a real file and pem encoded
                    if len(dictionary['smtps_cert']) >0 and len(dictionary['smtps_key'])>0:
                        s = smtplib.SMTP_SSL(host=str(dictionary['smtps_host']), port=dictionary['smtps_port'], keyfile=dictionary['smtps_key'], certfile=dictionary['smtps_cert'])
                        s.ehlo_or_helo_if_needed()
                        s.login(dictionary['auth_user'], dictionary['auth_password'])
                        send = s.sendmail(str(dictionary['email_from']), [str(dictionary['email_to'])], msg.as_string())
                        if isinstance(send, dict):
                            que.put([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "SUCCESS"])
                        else:
                            que.put([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "FAILURE"])
                    else:
                        s = smtplib.SMTP_SSL(host=str(dictionary['smtps_host']), port=dictionary['smtps_port'])
                        s.ehlo_or_helo_if_needed()
                        s.login(dictionary['auth_user'], dictionary['auth_password'])
                        send = s.sendmail(str(dictionary['email_from']), [str(dictionary['email_to'])], msg.as_string())
                        if isinstance(send, dict):
                            que.put([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "SUCCESS"])
                        else:
                            que.put([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "FAILURE"])
                except Exception as ex:
                    template = "An exception of type {0} occured. Arguments:\n{1!r}"
                    message = template.format(type(ex).__name__, ex.args)
                    journal.send("systemd-mailify: "+message)
                    if self.logg == True and self.logg_facility == "log_file" or self.logg_facility == "both":
                        self.logging.error(message)
                finally:
                    s.quit()
                    del s
            else:
                pass
        #starttls
        if dictionary['starttls'] == True:
            # no auth
            if dictionary['auth'] == False:
                try:
                    s = smtplib.SMTP()
                    s.connect(host=str(dictionary['starttls_host']), port=dictionary['starttls_port'])
                    s.ehlo()
                    #http://pymotw.com/2/smtplib/
                    if s.has_extn("STARTTLS"):
                        #check whether it is a real file and pem encoded
                        if len(dictionary['starttls_cert']) >0 and len(dictionary['starttls_key'])>0:
                            s.starttls(keyfile=dictionary['starttls_key'], certfile=dictionary['starttls_cert'])
                            s.ehlo()
                            send = s.sendmail(str(dictionary['email_from']), [str(dictionary['email_to'])], msg.as_string())
                            if isinstance(send, dict):
                                que.put([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "SUCCESS"])
                            else:
                                que.put([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "FAILURE"])
                        else:
                            s.starttls()
                            s.ehlo()
                            send = s.sendmail(str(dictionary['email_from']), [str(dictionary['email_to'])], msg.as_string())
                            if isinstance(send, dict):
                                que.put([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "SUCCESS"])
                            else:
                                que.put([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "FAILURE"])
                except Exception as ex:
                    template = "An exception of type {0} occured. Arguments:\n{1!r}"
                    message = template.format(type(ex).__name__, ex.args)
                    journal.send("systemd-mailify: "+message)
                    if self.logg == True and self.logg_facility == "log_file" or self.logg_facility == "both":
                        self.logging.error(message)
                finally:
                    s.quit()
                    del s
            # auth
            elif dictionary['auth'] == True:
                try:
                    s = smtplib.SMTP()
                    s.connect(host=str(dictionary['starttls_host']), port=dictionary['starttls_port'])
                    #http://pymotw.com/2/smtplib/
                    s.ehlo()
                    if s.has_extn("STARTTLS"):
                        #check whether it is a real file and pem encoded
                        if len(dictionary['starttls_cert']) >0 and len(dictionary['starttls_key'])>0:
                            s.starttls(keyfile=dictionary['starttls_key'], certfile=dictionary['starttls_cert'])
                            s.ehlo()
                            s.login(str(dictionary['auth_user']).strip(), str(dictionary['auth_password']))
                            send = s.sendmail(str(dictionary['email_from']), [str(dictionary['email_to'])], msg.as_string())
                            if isinstance(send, dict):
                                que.put([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "SUCCESS"])
                            else:
                                que.put([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "FAILURE"])
                        else:
                            s.starttls()
                            s.ehlo()
                            s.login(str(dictionary['auth_user']).strip(), str(dictionary['auth_password']))
                            send = s.sendmail(str(dictionary['email_from']), [str(dictionary['email_to'])], msg.as_string())
                            if isinstance(send, dict):
                                que.put([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "SUCCESS"])
                            else:
                                que.put([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "FAILURE"])
                except Exception as ex:
                    template = "An exception of type {0} occured. Arguments:\n{1!r}"
                    message = template.format(type(ex).__name__, ex.args)
                    journal.send("systemd-mailify: "+message)
                    if self.logg == True and self.logg_facility == "log_file" or self.logg_facility == "both":
                        self.logging.error(message)
                finally:
                    s.quit()
                    del s

            else:
                pass

    def run(self):
        """
        run
        return void
        :desc: function that goes on an infinite loop polling the systemd-journal for failed services
        Helpful API->http://www.freedesktop.org/software/systemd/python-systemd/
        """
        # do setuid, setgid voodo magic

        if self.logg == True and self.logg_facility == "log_file" and\
        self.logg_level == 10:
            self.logging.debug('Running inside run()')
        dictionary = self.parse_config()
        username = dictionary["user"]
        uid = self.get_conf_userid(username)
        self.set_egid()
        self.set_euid(uid)
        queue = Queue()
        if self.logg == True and self.logg_facility == "log_file" and\
        self.logg_level == 10:
            self.logging.debug('Running inside run() '+' is there an init Queue object? '+ str(queue))
        try:
            j_reader = journal.Reader()
        except Exception as ex:
            templa = "An exception of type {0} occured. Arguments:\n{1!r}"
            messa = templa.format(type(ex).__name__, ex.args)
            journal.send("systemd-mailify: "+messa)
        j_reader.log_level(journal.LOG_INFO)
        # j.seek_tail() #faulty->doesn't move the cursor to the end of journal

        # it is questionable whether there is actually a record with the real
        # datetime we provide but we assume it moves the cursor to somewhere
        # near the end of the journal fd
        j_reader.seek_realtime(datetime.datetime.now())
        poller = select.poll()
        try:
            poller.register(j_reader, j_reader.get_events())
        except Exception as ex:
            templa = "An exception of type {0} occured. Arguments:\n{1!r}"
            messa = templa.format(type(ex).__name__, ex.args)
            journal.send("systemd-mailify: "+messa)
        while poller.poll():
            #next is a debugging call
            # if it logs True it is pollable
            if self.logg == True and self.logg_facility == "log_file" and\
            self.logg_level == 10:
                reliable = j_reader.reliable_fd()
                self.logging.debug('Running inside run() '+' poller.poll() and determining whether we a reliable file descriptor to the journal file : '+ str(reliable))
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
                                if self.logg == True and self.logg_facility == "log_file" and\
                                self.logg_level == 10:
                                    self.logging.debug("Running inside run() I caught a pattern: "+string)
                                worker = Thread(target=self.mail_worker, args=(string, queue, dictionary,))
                                worker.start()
                                worker.join()
                                q_list = queue.get()
                                if q_list[1] == "SUCCESS":
                                    if self.logg == True and self.logg_facility == "log_file" or self.logg_facility == "both":
                                        self.logging.info(" at "+str(q_list[0])+" delivered mail with content: " + string)
                                        journal.send("systemd-mailify: at "+str(q_list[0])+" delivered mail with content: " + string)
                                    else:
                                        journal.send("systemd-mailify: at "+str(q_list[0])+" delivered mail with content: " + string)
                                elif q_list[1] == "FAILURE":
                                    if self.logg == True and self.logg_facility == "log_file" or self.logg_facility == "both":
                                        self.logging.info(" at "+str(q_list[0])+" failed to deliver mail with content: " + string)
                                        journal.send("systemd-mailify:" " at "+str(q_list[0])+" failed to deliver mail with content: " + string)
                                    else:
                                        journal.send("systemd-mailify:" " at "+str(q_list[0])+" failed to deliver mail with content: " + string)
                                else:
                                    if self.logg == True and self.logg_facility == "log_file" or self.logg_facility == "both":
                                        self.logging.info(" failed to deliver mail with content " + string)
                                        journal.send("systemd-mailify: failed to deliver mail with content: " + string)
                                    else:
                                        journal.send("systemd-mailify:"+" failed to deliver mail with content " + string)

                            else:
                                continue
                        except Exception as ex:
                            template = "An exception of type {0} occured. Arguments:\n{1!r}"
                            message = template.format(type(ex).__name__, ex.args)
                            journal.send("systemd-mailify: "+message)
                            if self.logg == True and self.logg_facility == "log_file" or self.logg_facility == "both":
                                self.logging.error(message)
                    else:
                        continue
           #back to normal journal reading
            else:
                pass
            continue


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
        lg = LogReader()
        pid = os.getpid()
        try:
            with open('/var/run/systemd-mailify.pid', 'w') as of:
                of.write(str(pid))
        except Exception as ex:
            templated = "An exception of type {0} occured. Arguments:\n{1!r}"
            messaged = templated.format(type(ex).__name__, ex.args)
            journal.send("systemd-mailify: "+messaged)
            if lg.logg == True and lg.logg_facility == "log_file" or lg.logg_facility == "both":
                lg.logging.error(message)
        finally:
            if lg.logg == True and lg.logg_facility == "log_file" or lg.logg_facility == "both":
                lg.logging.info("systemd-mailify started")
            lg.run()
