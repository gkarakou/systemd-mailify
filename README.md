# systemd-mailify

GENERAL
-------------------
systemd-mailify is a slightly modified stripped down version of systemd-denotify with a minimum set of dependencies. Its use is server oriented as opposed to systemd-denotify which is aiming at desktops. You can get mail notifications on systemd service failures on a production machine.

SOURCE DISTRIBUTION
---------------------

<pre>
git clone https://github.com/gkarakou/systemd-mailify.git

cd systemd-mailify

python2 setup.py sdist


</pre>

BUILD FOR FEDORA
------------------
<pre>
git clone https://github.com/gkarakou/systemd-mailify.git

cd systemd-mailify

sudo python setup.py bdist_rpm --requires "python, systemd-python, systemd, systemd-libs " --build-requires="python-setuptools" --vendor="gkarakou@gmail.com"

sudo yum --nogpgcheck localinstall dist/systemd-mailify-1.0-1.noarch.rpm

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


