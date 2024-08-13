#!/bin/bash
clear

PGHOST="127.0.0.1"
PGPORT="5432"
PGDATABASE="firmware"
PGUSER="firmadyne"
LOGUSER="andy"
export PGPASSWORD="firmadyne"
tables=(
    "brand"
    "image"
    "object"
    "object_to_image"
    "product"
)
cur_dir=$(pwd)
cd /opt/myae
source ./myae.config
MYAE_SCRATCH="$MYAEP1PREFIX/data/myae_scratch"
MYAE_IMAGES="$MYAEP1PREFIX/data/myae_images"
MYAE_BINARYS="$MYAEP1PREFIX/binaries"

if [ -e "$MYAE_SCRATCH" ]; then
    for i in `myls ${MYAE_SCRATCH}`; do
        echo -e "clean proj=> $i..."
    done
fi
cd $cur_dir

if [ -d "$MYAE_SCRATCH" ]; then
    umount -qln "$MYAE_SCRATCH"
fi
if [ -d "$MYAE_IMAGES" ]; then
    umount -qln "$MYAE_IMAGES"
fi
if [ -d "$MYAE_BINARYS" ]; then
    umount -qln "$MYAE_BINARYS"
fi

#myfind /opt "/home/$LOGUSER/myae" -type f -name 'andygood.log' | xargs -I @ rm -fr @
rm -fr /var/tmp/*.mysh
rm -fr /var/tmp/ae-lock
rm -fr /tmp/qemu.*

for table in "${tables[@]}"; do
    echo "truncating table: $table"
    psql -h "$PGHOST" -p "$PGPORT" -d "$PGDATABASE" -U "$PGUSER" -c "truncate table $table cascade;"
done

rm -fr "$MYAE_SCRATCH" "$MYAE_IMAGES" "$MYAE_BINARYS"
sleep 2
rm -fr "$MYAEP2PREFIX/scratch" "$MYAEP2PREFIX/images"

#supervisorctl clear all