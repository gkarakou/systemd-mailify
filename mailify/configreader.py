#!/usr/bin/python2
#encoding=utf-8
from systemd import journal
import ConfigParser
import sys
from pwd import getpwnam
from .logreader import LogReader
from .loggger import Loggger

class ConfigReader():

    def __init__(self):
        pass

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


    def parse_config(self):
        """
        parse_config
        :desc : Function that returns a dictionary containing all the values
        from the /etc/systemd-mailify.conf file (minus the global section)
        return dict
        """
        log_ger = Loggger()
        conf = ConfigParser.RawConfigParser()
        conf.read('/etc/systemd-mailify.conf')
        conf_dict = {}
        #parse patterns section
        conf_dict['conf_pattern_matcher_start'] = conf.getboolean("JournalPatternMatcher", "start")
        conf_dict['conf_pattern_patts'] = conf.get("JournalPatternMatcher", "patterns")
        conf_dict['conf_pattern_patterns'] = conf_dict['conf_pattern_patts'].split(",")
        #parse [EMAIL]

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
                if log_ger.logg == True and log_ger.logg_facility == "both":
                    log_ger.logging.error("You have asked for authentication but you have an empty auth_user name. Please update the /etc/systemd-mailify.conf file with a value ")
                    journal.send("systemd-mailify: ERROR You have asked for authentication but you have an empty auth_user name. Please update the /etc/systemd-mailify.conf file with a value ")
                elif log_ger.logg == True and log_ger.logg_facility == "log_file":
                    log_ger.logging.error("You have asked for authentication but you have an empty auth_user name. Please update the /etc/systemd-mailify.conf file with a value ")
                else:
                    journal.send("systemd-mailify: ERROR You have asked for authentication but you have an empty auth_user name. Please update the /etc/systemd-mailify.conf file with a value ")
                sys.exit(1)
            auth_password = conf.get("AUTH", "auth_password")
            if len(auth_password) == 0:
                if log_ger.logg == True and log_ger.logg_facility == "both":
                    log_ger.logging.error("You have asked for authentication but you have an empty auth_password field. Please update the /etc/systemd-mailify.conf file with a value ")
                    journal.send("systemd-mailify: ERROR You have asked for authentication but you have an empty auth_password field. Please update the /etc/systemd-mailify.conf file with a value ")
                elif log_ger.logg == True and log_ger.logg_facility == "log_file":
                    log_ger.logging.error("You have asked for authentication but you have an empty auth_password field. Please update the /etc/systemd-mailify.conf file with a value ")
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
            if log_ger.logg == True and log_ger.logg_facility == "both":
                log_ger.logging.info("You have asked for smtp connection but you have an empty smtp host field. Please update the /etc/systemd-mailify.conf file with a value. We assume localhost here")
                journal.send("systemd-mailify: INFO You have asked for a smtp connection but you have an empty smtp host field. Please update the /etc/systemd-mailify.conf file with a value. We assume localhost here")
            elif log_ger.logg == True and log_ger.logg_facility == "log_file":
                log_ger.logging.info("You have asked for smtp connection but you have an empty smtp host field. Please update the /etc/systemd-mailify.conf file with a value. We assume localhost here")
            else:
                journal.send("systemd-mailify: INFO You have asked for a smtp  connection but you have an empty smtp host field. Please update the /etc/systemd-mailify.conf file with a value. We assume localhost here")
        conf_dict['smtp_host'] = smtp_host
        smtp_port = conf.getint("SMTP", "port")
        if not smtp_port:
            smtp_port = 25
            if log_ger.logg == True and log_ger.logg_facility == "both":
                log_ger.logging.error("You have asked for smtp connection but you have an empty smtp port field. Please update the /etc/systemd-mailify.conf file with a value. port=25")
                journal.send("systemd-mailify: ERROR You have asked for a smtp connection but you have an empty smtp port  field. Please update the /etc/systemd-mailify.conf file with a value. port=25 ")
            elif log_ger.logg == True and log_ger.logg_facility == "log_file":
                log_ger.logging.error("You have asked for smtp connection but you have an empty smtp port field. Please update the /etc/systemd-mailify.conf file with a value. port=25")
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
                if log_ger.logg == True and log_ger.logg_facility == "both":
                    log_ger.logging.info("You have asked for smtps connection but you have an empty smtps host field. Please update the /etc/systemd-mailify.conf file with a value. We assume localhost here")
                    journal.send("systemd-mailify: INFO You have asked for a smtps connection but you have an empty smtps host field. Please update the /etc/systemd-mailify.conf file with a value. We assume localhost here")
                elif log_ger.logg == True and log_ger.logg_facility == "log_file":
                    log_ger.logging.info("You have asked for smtps connection but you have an empty smtps host field. Please update the /etc/systemd-mailify.conf file with a value. We assume localhost here")
                else:
                    journal.send("systemd-mailify: INFO You have asked for a smtps connection but you have an empty smtps host field. Please update the /etc/systemd-mailify.conf file with a value. We assume localhost here")
            conf_dict['smtps_host'] = smtps_host
            smtps_port = conf.getint("SMTPS", "port")
            if not smtps_port:
                smtps_port = 465
                if log_ger.logg == True and log_ger.logg_facility == "both":
                    log_ger.logging.error("You have asked for smtps connection but you have an empty smtps port field. Please update the /etc/systemd-mailify.conf file with a value. port=465 ")
                    journal.send("systemd-mailify: ERROR You have asked for a  smtps connection but you have an empty smtps port field. Please update the /etc/systemd-mailify.conf file with a value. port=465")
                elif log_ger.logg == True and log_ger.logg_facility == "log_file":
                    log_ger.logging.error("You have asked for smtps connection but you have an empty smtps port field. Please update the /etc/systemd-mailify.conf file with a value. port=465")
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
                if log_ger.logg == True and log_ger.logg_facility == "both":
                    log_ger.logging.info("You have asked for starttls connection but you have an empty starttls host field. Please update the /etc/systemd-mailify.conf file with a value. We assume localhost here")
                    journal.send("systemd-mailify: INFO You have asked for a starttls connection but you have an empty starttls host field. Please update the /etc/systemd-mailify.conf file with a value. We assume localhost here")
                elif log_ger.logg == True and log_ger.logg_facility == "log_file":
                    log_ger.logging.info("You have asked for starttls connection but  you have an empty starttls host field. Please update the /etc/systemd-mailify.conf file with a value. We assume localhost here")
                else:
                    journal.send("systemd-mailify: INFO You have asked for a starttls connection but you have an empty starttls host field. Please update the /etc/systemd-mailify.conf file with a value. We assume localhost here")
            conf_dict['starttls_host'] = starttls_host
            starttls_port = conf.getint("STARTTLS", "port")
            if not starttls_port:
                starttls_port = 587
                if log_ger.logg == True and log_ger.logg_facility == "both":
                    log_ger.logging.error("You have asked for starttls connection but you have an empty starttls port field. Please update the /etc/systemd-mailify.conf file with a value. port=587")
                    journal.send("systemd-mailify: ERROR You have asked for a starttls connection but you have an empty starttls port field. Please update the /etc/systemd-mailify.conf file with a value. port=587")
                elif log_ger.logg == True and log_ger.logg_facility == "log_file":
                    log_ger.logging.error("You have asked for starttls connection but you have an empty starttls port field. Please update the /etc/systemd-mailify.conf file with a value. port=587 ")
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
        if log_ger.logg == True and log_ger.logg_facility == "log_file" and\
        log_ger.logg_level == 10:
            for key, val in conf_dict.iteritems():
                log_ger.logging.debug("config_file: entry == " + str(key)+ " value == "+ str(val))
        return conf_dict
