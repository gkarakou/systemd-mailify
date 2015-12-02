#!/usr/bin/python2
#encoding=utf-8
from datetime import datetime
import select
from systemd import journal
from Queue import Queue
from threading import Thread
from multiprocessing import Process
from .configreader import ConfigReader
from .systemfuncs import SystemFuncs
from .mailer import Mailer
from .loggger import Loggger

class LogReader(Process):
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
        self.loggger = Loggger()

    def run(self):
        """
        run
        return void
        :desc: function that goes on an infinite loop polling the systemd-journal for failed services
        Helpful API->http://www.freedesktop.org/software/systemd/python-systemd/
        """
        # do setuid, setgid voodo magic

        if self.loggger.logg == True and self.loggger.logg_facility == "log_file" and\
        self.loggger.logg_level == 10:
            self.loggger.logging.debug('Running inside run()')
        conf_reader = ConfigReader()
        dictionary = conf_reader.parse_config()
        patterns = []
        if isinstance(dictionary['conf_pattern_matcher_start'], bool) and  dictionary['conf_pattern_matcher_start'] == True:
            for p in dictionary['conf_pattern_patterns']:
                patterns.append(p)
        patterns.append("entered failed state")
        username = dictionary["user"]
        uid = conf_reader.get_conf_userid(username)
        sys_funcs = SystemFuncs()
        sys_funcs.set_egid()
        sys_funcs.set_euid(uid)
        queue = Queue()
        mailler = Mailer()
        if self.loggger.logg == True and self.loggger.logg_facility == "log_file" and\
        self.loggger.logg_level == 10:
            self.loggger.logging.debug('Running inside run() '+' is there an init Queue object: '+ str(queue))
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
        j_reader.seek_realtime(datetime.now())
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
            #if self.loggger.logg == True and self.loggger.logg_facility == "log_file" and\
            #self.loggger.logg_level == 10:
            #    reliable = j_reader.reliable_fd()
            #    self.loggger.logging.debug('Running inside run method I called poller.poll() and try now to determine whether we have a reliable file descriptor to the journal file : '+ str(reliable))
            waiting = j_reader.process()
            # if JOURNAL append or JOURNAL logrotate
            if waiting == 1 or waiting == 2:
                j_reader.get_next()
                for entry in j_reader:
                    if 'MESSAGE' in entry:
                        for pattern in patterns:
                            try:
                                string = entry['MESSAGE']
                                if string and pattern in string:
                                    if self.loggger.logg == True and self.loggger.logg_facility == "log_file" and self.loggger.logg_level == 10:
                                        self.loggger.logging.debug("Running inside run() I caught a pattern: "+string)
                                    worker = Thread(target=mailler.mail_worker, args=(string, queue, dictionary,))
                                    worker.start()
                                    worker.join()
                                    q_list = queue.get()
                                    if q_list[1] == "SUCCESS":
                                        if self.loggger.logg == True and self.loggger.logg_facility == "log_file" or self.loggger.logg_facility == "both":
                                            self.loggger.logging.info(" Thread "+str(q_list[0])+" delivered mail with content: " + string)
                                            journal.send("systemd-mailify: Thread "+str(q_list[0])+" delivered mail with content: " + string)
                                        else:
                                            journal.send("systemd-mailify: Thread "+str(q_list[0])+" delivered mail with content: " + string)
                                    elif q_list[1] == "FAILURE":
                                        if self.loggger.logg == True and self.loggger.logg_facility == "log_file" or self.loggger.logg_facility == "both":
                                            self.loggger.logging.info(" at "+str(q_list[0])+" failed to deliver mail with content: " + string)
                                            journal.send("systemd-mailify: Thread "+str(q_list[0])+" failed to deliver mail with content: " + string)
                                        else:
                                            journal.send("systemd-mailify: Thread "+str(q_list[0])+" failed to deliver mail with content: " + string)
                                    else:
                                        if self.loggger.logg == True and self.loggger.logg_facility == "log_file" or self.loggger.logg_facility == "both":
                                            self.loggger.logging.info(" failed to deliver mail with content " + string)
                                            journal.send("systemd-mailify: failed to deliver mail with content: " + string)
                                        else:
                                            journal.send("systemd-mailify: failed to deliver mail with content " + string)
                                else:
                                    continue
                            except Exception as ex:
                                templatede = "An exception of type {0} occured. Arguments:\n{1!r}"
                                messagede = templatede.format(type(ex).__name__, ex.args)
                                journal.send("systemd-mailify: "+messagede)
                            if self.loggger.logg == True and self.loggger.logg_facility == "log_file" or self.loggger.logg_facility == "both":
                                self.loggger.logging.error(messagede)
                    else:
                        continue
           #back to normal journal reading
            else:
                pass
            continue
