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

from distutils.core import setup

setup(
name = 'systemd-mailify',
version = '1.0',
description = 'systemd related mail notifications',
long_description = 'A python based app that notifies for failed systemd services',
author = 'George Karakougioumtzis <gkarakou>',
author_email = 'gkarakou@gmail.com',
url = 'https://github.com/gkarakou/systemd-mailify',
platforms = 'linux',
license = 'GPL-3.0',
packages = ['systemd-mailify'],
package_data = {'systemd-mailify': ['conf/*']},
install_requires= [ 'python-systemd'],
classifiers = ['Development Status :: Release Candidate',
'Environment :: server',
'Intended Audience :: System Administrators',
'License :: GPL-3.0 ',
'Operating System :: Linux',
'Programming Language :: Python2.7'],
data_files = [('/etc', ['systemd-mailify/conf/systemd-mailify.conf']), ('/usr/lib/systemd/system', ['systemd-mailify/conf/systemd-mailify.service'])],
scripts = ['scripts/systemd-mailify.py']
)
