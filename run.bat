@echo off

echo Activating codeeditor environment...

start "CodePlatform" cmd /k "workon codeeditor && cd /d %~dp0CodePlatform && python manage.py runserver"

start "Redis" cmd /k "cd /d %~dp0Redis && .\memurai"

start "CodePlatform" cmd /k "workon codeeditor && cd /d %~dp0CodePlatform && celery -A CodePlatform worker --pool=solo -l info"

start "Sandbox" cmd /k "workon codeeditor && cd /d %~dp0Sandbox && python manage.py runserver 8080"

echo Servers started.
pause