#!/bin/bash
clear

PGHOST="127.0.0.1"
PGPORT="5432"
PGDATABASE="firmware"
PGUSER="firmadyne"
LOGUSER="andy"
PGPASSWORD="firmadyne"
export PGPASSWORD="$PGPASSWORD"
tables=(
    "brand"
    "image"
    "object"
    "object_to_image"
    "product"
)

rm -fr /opt/myae/scratch
rm -fr /opt/myae/images
find /opt "/home/$LOGUSER/myae" -type f -name 'andygood.log' | xargs -I [] rm []
rm -fr /var/tmp/18ce86af.sh
rm -fr /var/tmp/f8fe6ef5.sh
rm -fr /var/tmp/ae-lock
rm -fr /tmp/qemu.*

for table in "${tables[@]}"; do
    echo "truncating table: $table"
    psql -h "$PGHOST" -p "$PGPORT" -d "$PGDATABASE" -U "$PGUSER" -c "truncate table $table cascade;"
done

if [ -d "/home/andy/myae/myae_scratch" ]; then
    umount /home/andy/myae/myae_scratch
    rm -fr /home/andy/myae/myae_scratch
fi
if [ -d "/home/andy/myae/myae_images" ]; then
    umount /home/andy/myae/myae_images
    rm -fr /home/andy/myae/myae_images
fi
