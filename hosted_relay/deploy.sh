#!/bin/sh

exec rsync -rv --exclude=venv . ubuntu@54.161.203.83:~/hosted_relay

