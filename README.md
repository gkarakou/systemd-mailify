# systemd-mailify


Updated to 1.2



GENERAL
-------------------
systemd-mailify is a slightly modified, stripped down version of its counterpart systemd-denotify with a minimum set of dependencies. Its use is server oriented as opposed to systemd-denotify which is aiming at desktops. You can get mail notifications on systemd service failures and when specific phrases match in the journal, on a production machine.
systemd-mailify is not to be confused with the systemd family of daemons; Its a standalone python program which took half of its name to honour its dependency python-systemd.

Note:  An selinux policy module will also be available later for redhat based distros (still to be done, lol).


WHY SHOULD I INSTALL IT
-------------------------
Lets say you have to administer a lot of vps's simply install systemd-mailify on them and you will notice a failure from your phone email client instead of having to login to each one of them.


DEPENDS
---------------------
python2 systemd-python(or python-systemd on some distros)


SOURCE DISTRIBUTION
---------------------

<pre>
git clone https://github.com/gkarakou/systemd-mailify

cd systemd-mailify

python2 setup.py sdist


</pre>

BUILD FOR FEDORA
------------------
<pre>
git clone https://github.com/gkarakou/systemd-mailify

cd systemd-mailify

sudo python setup.py bdist_rpm --requires "python, systemd-python, systemd, systemd-libs " --build-requires="python-setuptools" --vendor="gkarakou@gmail.com" --no-autoreq
#this will produce an rpm package inside the dist directory, it could be named differently depending on the version
sudo yum --nogpgcheck localinstall dist/systemd-mailify-1.2-1.noarch.rpm
#For fedora 22/23
sudo dnf --nogpgcheck install dist/systemd-mailify-1.2-1.noarch.rpm

</pre>


-------------------------------

DEBIAN/UBUNTU
----------------


<pre>
sudo apt-get install python-stdeb fakeroot python-all

git clone https://github.com/gkarakou/systemd-mailify.git

cd systemd-mailify

sudo python setup.py sdist_dsc --depends "systemd systemd-libs python-systemd " --build-depends "python-setuptools" bdist_deb

#it should produce a .deb package ready to be installed in deb_dist directory (hint:ls -al deb_dist|grep deb):

sudo dpkg -i deb_dist/systemd-mailify-$VERSION.deb

sudo apt-get -f install
</pre>

If you find any troubles you can follow this guide:
http://shallowsky.com/blog/programming/python-debian-packages-w-stdeb.html


USAGE
--------------------
You simply edit the file /etc/systemd-mailify.conf and enable/start systemd-mailify.

<pre>
sudo systemctl enable systemd-mailify
sudo systemctl start systemd-mailify
</pre>

