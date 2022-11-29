#!/bin/bash

# version 1.0 
# Clean up unused images, containers and bridges
docker kill scheduler_sequencer dbproxy0 dbproxy1 load_generator
docker container prune
docker image prune
docker network rm db-in-k8s

# Create the bridge
docker network create --subnet=172.25.0.0/16 db-in-k8s

# Build the images
docker build ./ -t systems
docker build ./load_generator -t load_generator -f load_generator/Dockerfile

# Run the system
echo Starting dbproxies...
docker run -d -it --rm --ip 172.25.0.66 --name dbproxy0 --net db-in-k8s systems cargo run 0 --dbproxy -c ./o2versioner/conf_dbproxy0.toml
docker run -d -it --rm --ip 172.25.0.67 --name dbproxy1 --net db-in-k8s systems cargo run 0 --dbproxy -c ./o2versioner/conf_dbproxy1.toml
echo Done
echo Starting scheduler and sequencer...
docker run -d -it --rm --ip 172.25.0.65 --name scheduler_sequencer --net db-in-k8s systems ./systems_start.sh   # need to modify conf_scheduler.toml for just docker runs, now it fits for kubernetes
echo Done
sleep 3 # Need time for system to establish connection
echo Starting TPC-W...
docker run -d -it --rm --name load_generator --net db-in-k8s load_generator python3 ./client.py --port 2077 --c_id 0 --ip scheduler_sequencer --path /usr/src/
echo Done
docker attach scheduler_sequencer # monitor the process


# # version 2.0 
# # Clean up unused images, containers and bridges
# docker kill systems load_generator
# docker container prune
# docker image prune
# docker network rm db-in-k8s

# # Create the bridge
# docker network create db-in-k8s

# # Build the images
# docker build ./ -t systems
# docker build ./load_generator -t load_generator -f load_generator/Dockerfile

# # Run the system
# echo Starting systems...
# docker run -d -it --rm --name systems --net db-in-k8s systems
# echo Done
# sleep 3 # Need time for system to establish connection
# echo Starting TPC-W...
# docker run -d -it --rm --name load_generator --net db-in-k8s load_generator python3 ./client.py --port 2077 --c_id 0 --ip systems --path /usr/src/
# echo Done
# docker attach systems # monitor the process

# # for monitoring
# # docker run -it --rm --name systems --net db-in-k8s systems
# # docker run -it --rm --name load_generator --net db-in-k8s load_generator python3 ./client.py --port 2077 --c_id 0 --ip systems --path /usr/src/