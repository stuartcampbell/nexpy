#!/bin/bash -eu

NEXPYRO=$( cd $( dirname $0 ) ; /bin/pwd )
DAEMON=${NEXPYRO}/nxfileremote.py
CLIENT=${NEXPYRO}/client.py

NEXPY_SRC=$( cd ${NEXPYRO}/.. ; /bin/pwd )

export PYTHONPATH=${NEXPY_SRC}

message()
{
  echo "run.sh: ${*}"
}

# Start daemon
TMPFILE=$( mktemp )
( ${DAEMON} | tee ${TMPFILE} 2>&1 ) &
DAEMON_PID=${!}
message "Daemon running: pid: ${DAEMON_PID}"
# echo "DAEMON_PID: ${DAEMON_PID}"

shutdown_daemon()
{
  PID=$1
  echo "Killing: ${PID}"
  kill ${PID}
  sleep 1
  kill -s KILL ${PID}
}

# Obtain daemon URI
sleep 1
URI=$( grep "URI:" ${TMPFILE} | cut -d ' ' -f 2 )
if [[ ${URI} != PYRO* ]]
then
  echo "Daemon startup failed!"
  shutdown_daemon ${DAEMON_PID}
  exit 1
fi
echo "URI: ${URI}"

# Start client
if ! ${CLIENT} ${URI} f2.nxs 
then 
  message "Client failed!"
fi

rm ${TMPFILE}
wait
exit 0
