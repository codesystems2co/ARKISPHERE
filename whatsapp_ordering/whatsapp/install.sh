rm -r PKG-INFO
rm -r dist
rm -r build
sudo python3 setup.py bdist_egg
sudo python3 setup.py bdist_rpm
sudo python3 setup.py install