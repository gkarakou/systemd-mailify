#!/usr/bin/python2
#encoding=utf-8
import datetime
import select
from systemd import journal
import multiprocessing
from Queue import Queue
from threading import Thread
import ConfigParser
import smtplib
import email.utils
import os
from pwd import getpwnam
import sys
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

    def get_logger(self):
        conf = ConfigParser.RawConfigParser()
        conf.read('/etc/systemd-mailify.conf')
        conf_log_dict = {}
        log = conf.get("LOGGING", "log")
        log_level = conf.get("LOGGING", "log_level")
        conf_log_dict['log'] = log
        conf_log_dict['log_level'] = log_level
        if conf_log_dict['log'] == "log_file" or conf_log_dict['log'] == "both":
            logger = logging.getLogger('systemd-mailify')
            #create log file and chown/chmod
            hdlr = logging.FileHandler('/var/log/systemd-mailify.log')
            formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
            hdlr.setFormatter(formatter)
            logger.addHandler(hdlr)
            logger.setLevel(logging.WARNING)
        else:
            #journal logging
            logger = None
        return logger

    def get_euid(self):
        """
        get_euid_
        :desc : Function that returns effective user id as int
        return int
        """
        uid = os.geteuid()
        pid = os.getpid()
        #print "getting uid: "+ str(uid)
        #print "getting pid: "+ str(pid)
        #journal.send("systemd-mailify in get_euid: "+str(uid))
        #journal.send("systemd-mailify pid in get_euid: "+str(pid))
        return uid

    def get_user(self, name):
        """
        get_user
        :desc : Function that returns user id as int from config
        return int
        """
        username_to_id = getpwnam(name).pw_uid
        #journal.send("systemd-mailify in get_user: "+str(username_to_id))
        #print "getting uid: "+ str(username_to_id)
        return username_to_id

    def set_euid(self, uid):
        """set_euid
        return int
        :param *args:
        """
        euid = int(uid)
        setuid = os.seteuid(euid)
        #if setuid == None:
        #    journal.send("systemd-mailify in set_euid: "+str(self.get_euid()))

    def parse_config(self):
        conf = ConfigParser.RawConfigParser()
        conf.read('/etc/systemd-mailify.conf')

        #parse [EMAIL]

        conf_dict = {}
        user = conf.get("SYSTEMD-MAILIFY", "user")
        subject = conf.get("EMAIL", "subject")
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
            auth_password = conf.get("AUTH", "auth_password")
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
        conf_dict['smtp_host'] = smtp_host
        smtp_port = conf.getint("SMTP", "port")
        if not smtp_port:
            smtp_port = 25
        conf_dict['smtp_port'] = smtp_port

        #parse [SMTPS]
        smtps = conf.getboolean("SMTPS", "active")
        if smtps and smtps == True:
            conf_dict['smtps'] = True
            smtps_host = conf.get("SMTPS", "host")
            if len(smtps_host) == 0:
                smtps_host = "localhost"
            conf_dict['smtps_host'] = smtps_host
            smtps_port = conf.getint("SMTPS", "port")
            if smtps_port:
                smtps_port = 465
            conf_dict['smtps_port'] = smtps_port
            smtps_cert = conf.get("SMTPS", "cert_file")
            conf_dict['smtps_cert'] = smtps_cert
            smtps_key = conf.get("SMTPS", "key_file")
            conf_dict['smtps_key'] = smtps_key
        else:
            conf_dict['smtps'] = False

        #parse [STARTTLS]
        starttls = conf.getboolean("STARTTLS", "active")
        if starttls and starttls == True:
            conf_dict['starttls'] = True
            starttls_host = conf.get("STARTTLS", "host")
            if len(starttls_host) == 0:
                starttls_host = "localhost"
            conf_dict['starttls_host'] = starttls_host
            starttls_port = conf.getint("STARTTLS", "port")
            if starttls_port:
                starttls_port = 587
            conf_dict['starttls_port'] = starttls_port
            starttls_cert = conf.get("STARTTLS", "cert_file")
            conf_dict['starttls_cert'] = starttls_cert
            starttls_key = conf.get("STARTTLS", "key_file")
            conf_dict['starttls_key'] = starttls_key
        else:
            conf_dict['starttls'] = False
        return conf_dict


    def mail_worker(self, stri, que):

        #print 'In %s' % self.name
        dictionary = self.parse_config()
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
                        que.put([self.name, datetime.datetime.now(), "SUCCESS"])
                    else:
                        que.put([self.name, datetime.datetime.now(), "FAILURE"])
                except Exception as ex:
                    template = "An exception of type {0} occured. Arguments:\n{1!r}"
                    message = template.format(type(ex).__name__, ex.args)
                    journal.send("systemd-mailify: "+message)
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
                        que.put([self.name, datetime.datetime.now()[:19], "SUCCESS"])
                    else:
                        que.put([self.name, datetime.datetime.now()[:19], "FAILURE"])
                except Exception as ex:
                    template = "An exception of type {0} occured. Arguments:\n{1!r}"
                    message = template.format(type(ex).__name__, ex.args)
                    journal.send("systemd-mailify: "+message)
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
                            que.put([self.name, datetime.datetime.now()[:19], "SUCCESS"])
                        else:
                            que.put([self.name, datetime.datetime.now()[:19], "FAILURE"])
                    else:
                        s = smtplib.SMTP_SSL(host=str(dictionary['smtps_host']), port=dictionary['smtps_port'])
                        s.ehlo_or_helo_if_needed()
                        send = s.sendmail(str(dictionary['email_from']), [str(dictionary['email_to'])], msg.as_string())
                        if isinstance(send, dict):
                            que.put([self.name, datetime.datetime.now()[:19], "SUCCESS"])
                        else:
                            que.put([self.name, datetime.datetime.now()[:19], "FAILURE"])
                except Exception as ex:
                    template = "An exception of type {0} occured. Arguments:\n{1!r}"
                    message = template.format(type(ex).__name__, ex.args)
                    journal.send("systemd-mailify: "+message)
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
                            que.put([self.name, datetime.datetime.now()[:19], "SUCCESS"])
                        else:
                            que.put([self.name, datetime.datetime.now()[:19], "FAILURE"])
                    else:
                        s = smtplib.SMTP_SSL(host=str(dictionary['smtps_host']), port=dictionary['smtps_port'])
                        s.ehlo_or_helo_if_needed()
                        s.login(dictionary['auth_user'], dictionary['auth_password'])
                        send = s.sendmail(str(dictionary['email_from']), [str(dictionary['email_to'])], msg.as_string())
                        if isinstance(send, dict):
                            que.put([self.name, datetime.datetime.now()[:19], "SUCCESS"])
                        else:
                            que.put([self.name, datetime.datetime.now()[:19], "FAILURE"])
                except Exception as ex:
                    template = "An exception of type {0} occured. Arguments:\n{1!r}"
                    message = template.format(type(ex).__name__, ex.args)
                    journal.send("systemd-mailify: "+message)
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
                                que.put([self.name, datetime.datetime.now()[:19], "SUCCESS"])
                            else:
                                que.put([self.name, datetime.datetime.now()[:19], "FAILURE"])
                        else:
                            s.starttls()
                            s.ehlo()
                            send = s.sendmail(str(dictionary['email_from']), [str(dictionary['email_to'])], msg.as_string())
                            if isinstance(send, dict):
                                que.put([self.name, datetime.datetime.now()[:19], "SUCCESS"])
                            else:
                                que.put([self.name, datetime.datetime.now()[:19], "FAILURE"])
                except Exception as ex:
                    template = "An exception of type {0} occured. Arguments:\n{1!r}"
                    message = template.format(type(ex).__name__, ex.args)
                    journal.send("systemd-mailify: "+message)
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
                                que.put([self.name, datetime.datetime.now()[:19], "SUCCESS"])
                            else:
                                que.put([self.name, datetime.datetime.now(), "FAILURE"])
                        else:
                            s.starttls()
                            s.ehlo()
                            s.login(str(dictionary['auth_user']).strip(), str(dictionary['auth_password']))
                            send = s.sendmail(str(dictionary['email_from']), [str(dictionary['email_to'])], msg.as_string())
                            if isinstance(send, dict):
                                que.put([self.name, datetime.datetime.now()[:19], "SUCCESS"])
                            else:
                                que.put([self.name, datetime.datetime.now()[:19], "FAILURE"])
                except Exception as ex:
                    template = "An exception of type {0} occured. Arguments:\n{1!r}"
                    message = template.format(type(ex).__name__, ex.args)
                    journal.send("systemd-mailify: "+message)
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
        dictionary = self.parse_config()
        username = dictionary["user"]
        uid = self.get_user(username)
        self.set_euid(uid)
        queue = Queue()
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
                                #queue.put(string)
                                #http://pymotw.com/2/smtplib/
                                worker = Thread(target=self.mail_worker, args=(string, queue))
                                worker.start()
                                worker.join()
                                q_list = queue.get()
                                if q_list[2] == "SUCCESS":
                                    journal.send("systemd-mailify:"+str(q_list[0])+
                                            " at "+str(q_list[1])+" delivered mail with content: " + string)
                                elif q_list[2] == "FAILURE":
                                    journal.send("systemd-mailify:"+str(q_list[0])+
                                            " at "+str(q_list[1])+" failed to deliver mail with content: " + string)
                                else :
                                    journal.send("systemd-mailify:"+" failed to deliver mail with content " + string)

                            else:
                                continue
                        except Exception as ex:
                            template = "An exception of type {0} occured. Arguments:\n{1!r}"
                            message = template.format(type(ex).__name__, ex.args)
                            journal.send("systemd-mailify: "+message)
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
        config_logreader_start = config.getboolean("SYSTEMD-MAILIFY", "start")
    except Exception as ex:
        template = "An exception of type {0} occured. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        journal.send("systemd-mailify: "+message)

    if isinstance(config_logreader_start, bool) and config_logreader_start == True:
        lg = LogReader()
        lg.daemon = True
        pid = os.getpid()
        try:
            with open('/var/run/systemd-mailify.pid', 'w') as of:
                of.write(str(pid))
        except Exception as ex:
            templated = "An exception of type {0} occured. Arguments:\n{1!r}"
            messaged = templated.format(type(ex).__name__, ex.args)
            journal.send("systemd-mailify: "+messaged)
        finally:
            lg.run()
            lg.start()
