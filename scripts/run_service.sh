#!/firmadyne/sh

BUSYBOX=/firmadyne/busybox
${BUSYBOX} echo -e `date +'%Y-%m-%d %H:%M:%S'`" $0 begin..." >> /opt/service.out

BINARY=`${BUSYBOX} cat /firmadyne/service`
BINARY_NAME=`${BUSYBOX} basename ${BINARY}`

if (${FIRMAE_ETC}); then
    ${BUSYBOX} sleep 120
    $BINARY &

    while (true); do
        ${BUSYBOX} sleep 10
        if ( ! (${BUSYBOX} ps | ${BUSYBOX} grep -v grep | ${BUSYBOX} grep -sqi ${BINARY_NAME}) ); then
            $BINARY &
        fi
    done
fi
${BUSYBOX} echo -e `date +'%Y-%m-%d %H:%M:%S'`" $0 end\n" >> /opt/service.out
