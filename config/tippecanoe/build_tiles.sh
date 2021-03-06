set -e

inputdir=$1
outputdir=$2

mkdir -p ${outputdir}/tilejson

# Build unified tileset where each layer has different settings - e.g. zoom info.

# Build pedestrian network layer
tippecanoe -f -Z 6 -z 14 -B 14 -r 2.5 -ad \
    -L transportation:${inputdir}/transportation.geojson \
    -e ${outputdir}/pedestrian

cp /home/tippecanoe/pedestrian.json ${outputdir}/tilejson/pedestrian.json
sed -i s,HOSTNAME,${HOST},g ${outputdir}/tilejson/pedestrian.json

# Build regions layer
tippecanoe -f -Z 0 -z 14 -B 14 -r 2.5 -ad \
    -L region:${inputdir}/regions.geojson \
    -e ${outputdir}/regions

cp /home/tippecanoe/regions.json ${outputdir}/tilejson/regions.json
sed -i s,HOSTNAME,${HOST},g ${outputdir}/tilejson/regions.json

# Build tasks layers
tippecanoe -f -Z 0 -z 14 -B 14 -r 2.5 -ad \
    -L crossing_tasks:${inputdir}/crossing_tasks.geojson \
    -L sidewalk_tasks:${inputdir}/sidewalk_tasks.geojson \
    -e ${outputdir}/tasks

cp /home/tippecanoe/tasks.json ${outputdir}/tilejson/tasks.json
sed -i s,HOSTNAME,${HOST},g ${outputdir}/tilejson/tasks.json
