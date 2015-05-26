#!/bin/bash

usage() { echo "Usage: $0 [-d <database>] [-f <backup-file>]" 1>&2; exit 1; }

while getopts ":d:f:" o; do
    case "${o}" in
        d)
            d=${OPTARG}
            ;;
        f)
            f=${OPTARG}
            ;;
        *)
            usage
            ;;
    esac
done
shift $((OPTIND-1))

if [ -z "${d}" ] || [ -z "${f}" ]; then
    usage
fi

# echo "d = ${d}"
# echo "f = ${f}"

dropdb $d
createdb $d
psql -q $d < $f
