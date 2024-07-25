#!/bin/bash
while read line; do
    tmp=`date -d today +"[%Y-%m-%d %H:%M:%S.%3N]"`
    echo "$tmp $line"
done
