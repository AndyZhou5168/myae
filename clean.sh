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
rm -fr /tmp/qemu.*
find /opt "/home/$LOGUSER/myae" -type f -name 'andygood.log' | xargs -I [] rm []

for table in "${tables[@]}"; do
    echo "truncating table: $table"
    psql -h "$PGHOST" -p "$PGPORT" -d "$PGDATABASE" -U "$PGUSER" -c "truncate table $table cascade;"
done

rm -fr "/tmp/18ce86af.sh /tmp/f8fe6ef5.sh"
