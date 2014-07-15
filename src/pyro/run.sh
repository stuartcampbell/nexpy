#!/bin/bash -eu

NEXPYRO=$( cd $( dirname $0 ) ; /bin/pwd )
DAEMON=${NEXPYRO}/nxfileremote.py
CLIENT=${NEXPYRO}/client.py

NEXPY_SRC=$( cd ${NEXPYRO}/.. ; /bin/pwd )

export PYTHONPATH=${NEXPY_SRC}

FILE=$1

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
  kill ${PID} || true
  sleep 1
  kill -s KILL ${PID} || true
}

# Obtain daemon URI
sleep 1
URI=$( grep "URI:" ${TMPFILE} | cut -d ' ' -f 2 )
if [[ ${URI} != PYRO* ]]
then
  echo "Daemon startup failed!"
  shutdown_daemon ${DAEMON_PID}
  echo "contents of: ${TMPFILE}"
  cat ${TMPFILE}
  exit 1
fi
echo "URI: ${URI}"

# Start client
if ! ( cd /tmp ; ${CLIENT} ${URI} ${FILE} )
then
  message "Client failed!"
fi

rm ${TMPFILE}
wait
exit 0
