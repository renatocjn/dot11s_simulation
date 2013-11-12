#!/bin/sh

minimumNumberOfLinks=$1
shift

valForReturn=1
for mpReport in $@; do
	linksCounted=`cat $mpReport | grep peerMeshPointAddress | sort | uniq | wc -l`
# 	echo Testing "$mpReport", result: $linksCounted
	if [ "$linksCounted" -lt "$minimumNumberOfLinks" ]; then
# 		echo Testing "$mpReport", too few connections...
		echo astonished $linksCounted
		valForReturn=0
		break
	fi
done
rm $@
return $valForReturn
