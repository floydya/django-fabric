#!/bin/sh
. ../env/bin/activate
pip install Flask

sudo rm /etc/init/updater.conf
sudo cp /home/local_moving/hooks/updater.conf /etc/init/
service updater start
