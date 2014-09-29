#!/bin/bash

if [[ ! -d results ]]; then
	cd ..
fi

len=$(ls -1 results|wc -l)
i=1
for d in results/*; do
	echo progress: $i / $len
	./scripts/flow_statistics.py $d
	./scripts/node_statistics.py $d
	i=$(($i+1))
done

