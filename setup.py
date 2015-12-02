#!/usr/bin/python2

# Copyright (C) 2015 George Karakou (gkarakou)
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You can get a copy of the GNU General Public License at
# <http://www.gnu.org/licenses/>.

#http://stackoverflow.com/questions/11536764/attempted-relative-import-in-non-package-even-with-init-py
#if __package__ is None:
#    import sys
#    from os import path
#    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
#    from install_script import Installer
#else:
#    from .install_script import Installer
from distutils.core import setup

setup(
name = 'systemd-mailify',
version = '1.1',
description = 'Provides mailing notifications for failed systemd services',
long_description = 'A python based service that mail-ifies on failed systemd services and on specific phrases found in the journal',
author = 'George Karakougioumtzis <gkarakou>',
author_email = 'gkarakou@gmail.com',
url = 'https://github.com/gkarakou/systemd-mailify',
platforms = 'linux',
license = 'GPL-3.0',
packages = ['mailify'],
package_data = {'mailify': ['conf/*']},
install_requires= ['python-systemd'],
classifiers = ['Development Status :: 1.1 - Stable',
'Environment :: Server',
'Intended Audience :: System Administrators',
'License :: GPL-3.0 ',
'Operating System :: Linux',
'Programming Language :: Python2.7'],
data_files = [('/etc', ['mailify/conf/systemd-mailify.conf']), ('/usr/lib/systemd/system', ['mailify/conf/systemd-mailify.service'])],
scripts = ['scripts/systemd-mailify.py']
)
