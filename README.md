# rpi-htu21-to-prom
Python script in docker container to get data from htu21 sensor to a prometheus endpoint.

Will use port 8000 but can map it to whatever you want. Will collect data every 60 seconds, but can be changed with ENV variables RUN_INTERVAL_SECONDS. 

It will collect humidity and temperature from the sensor aswell as CPU temperature from the PI. 

Just clone the repo, adjust if docker-copose.yml if needed and run 'docker-compose up -d' and off you go. The metrics will be available at http://<ip/dns>:<port>/metrics. 