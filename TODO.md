Strip milliseconds from datetime

smtps,starttls certfile could have the key in it so do an additional check if the cert_file path is not empty but the key is( for the two sections)

More Config checks

Check whether the mail thread also has setuid user when it runs

OPTIONALLY implent logger in dedicated log file
give the ability to choose whether to log in journal/logfile or both in .conf

Memory testing

optimizations (we are python, hungry for server resources!)
