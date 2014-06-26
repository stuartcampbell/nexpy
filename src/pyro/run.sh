#!/bin/bash -eux

NEXPYRO=$( cd $( dirname $0 ) ; /bin/pwd )
DAEMON=${NEXPYRO}/nxfileremote.py
CLIENT=${NEXPYRO}/client.py

# Start daemon
TMPFILE=$( mktemp )
( ${DAEMON} | tee ${TMPFILE} 2>&1 ) &
DAEMON_PID=${!}
echo "Daemon running: pid: ${DAEMON_PID}"
disown ${DAEMON_PID}

shutdown()
{
  PID=$1
  echo "Killing: ${PID}"
  # kill ${PID}
  sleep 1
  # kill -s KILL ${PID}
}

# Obtain daemon URI
sleep 1
URI=$( grep "URI:" ${TMPFILE} | cut -d ' ' -f 2 )
if [[ ${URI} != PYRO* ]]
then
  echo "Daemon startup failed!"
  shutdown ${DAEMON_PID}
  exit 1
fi
echo "URI: ${URI}"

exit 0

# Start client
${CLIENT} ${URI} file.nxs

# Shut down
shutdown ${DAEMON_PID}
exit 0
