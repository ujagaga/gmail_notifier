#!/bin/sh

cd "$(dirname "$0")"
cd ..
ver="1.0"

rm -fr ./linux_build/ujagagaGmailNotify-$ver/opt

# building standalone app
pyinstaller ./ujagagaGmailNotify.py
cp -f ./gmail_new.png dist/ujagagaGmailNotify/
cp -f ./gmail_none.png dist/ujagagaGmailNotify/
cp -f ./logo.png dist/ujagagaGmailNotify/
cp -f ./README.md dist/ujagagaGmailNotify/
cp -f ./client_secret.json dist/ujagagaGmailNotify/

mv dist/ linux_build/ujagagaGmailNotify-$ver/opt

chmod -R 755 linux_build/ujagagaGmailNotify-$ver/DEBIAN/
# removing any leftovers
rm -f *.spec
rm -fr build/
rm -fr __pycache__/
rm -fr ./linux_build/ujagagaGmailNotify-$ver/opt/ujagagaGmailNotify/share

dpkg-deb --build ./linux_build/ujagagaGmailNotify-$ver/
