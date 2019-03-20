#!/bin/bash

exec &> update.log

PROJECT_NAME="local_moving"
GIT_REMOTE=origin
CLONE_BRANCH="dev"
PROJECT_ROOT_DIR="/home/local_moving/$PROJECT_NAME/server/app"

if [ ! -d "../$PROJECT_NAME" ]; then
  echo "No project directory"
  exit
fi


echo "$(date)"
echo "pulling project from git"

cd ../$PROJECT_NAME

echo "$GIT_REMOTE -b $CLONE_BRANCH"
git pull $GIT_REMOTE $CLONE_BRANCH

echo "activating virtualenv"

. ../env/bin/activate

echo "updating requirements"

pip install -r $PROJECT_ROOT_DIR/requirements.txt


echo "running migrations"
python $PROJECT_ROOT_DIR/manage.py migrate


echo "collecting static"
python $PROJECT_ROOT_DIR/manage.py collectstatic --noinput


echo "making messages"
python $PROJECT_ROOT_DIR/manage.py makemessages --all -e .jinja,.html,.py

echo "restarting server"
kill -HUP `cat /tmp/gunicorn.pid`
service celery restart
