import requests
import logging
import logging.config
import psycopg2
from psycopg2.extras import LoggingConnection
from datetime import datetime
import configparser
import time

# https://openskynetwork.github.io/opensky-api/rest.html
# The API endpoint
url = "https://opensky-network.org/api/states/all?lamin=42.3&lomin=-5.24&lamax=51.2&lomax=8.3"

logging.config.fileConfig('logging.conf')
logger = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read('parameters.conf')

conn = psycopg2.connect(connection_factory=LoggingConnection, **config['database'])
conn.initialize(logger)
cur = conn.cursor()

while True:
    # A GET request to the API
    response = requests.get(url)
    print(response.status_code)

    # Print the response
    for state in response.json()['states']:
        if (state[1] != ''):
            icao = state[0].upper()
            callsign = state[1]
            time_position = datetime.fromtimestamp(state[3])
            longitude = state[5]
            latitude = state[6]
            baro_altitude = state[7]
            if (state[7] is None):
                baro_altitude = 0
            velocity = state[9]
            true_track = state[10]
            vertical_rate = state[11]
            sensors = state[12]
            position_source = state[16]
            category = state[16]
            logger.debug(icao, callsign,time_position,latitude, longitude, baro_altitude, velocity, true_track, vertical_rate, position_source,category)
            cur.execute(
                "INSERT INTO acft_position (callsign, address_type, address, report_time, " \
                "stealth, no_tracking, category, " \
                "location, latitude, longitude,altitude, flight_level, track, hspeed, vspeed, " \
                "user_comment, create_by, update_by) " \
                "VALUES (%s, %s, %s, %s," \
                "%s, %s, %s, " \
                "'POINT(%s %s %s)', %s, %s, %s, %s, %s, %s, %s," \
                "%s,'OPENSKY','OPENSKY') " \
                "ON CONFLICT(callsign) DO " \
                "UPDATE SET address_type = %s, address = %s, update_time = %s, report_time = %s," \
                "stealth = %s, no_tracking = %s, category = %s, " \
                "location = 'POINT(%s %s %s)', latitude = %s, longitude = %s, altitude = %s, flight_level = %s, track = %s, hspeed = %s, vspeed = %s, "
                "user_comment = %s, update_by='OPENSKY';",
                (callsign, 0, icao, time_position, 
                False, False, 0,
                latitude,longitude, baro_altitude,latitude,longitude, baro_altitude,0, true_track, velocity, vertical_rate,
                '',
                0, icao, datetime.now(), time_position, 
                False, False, 0,
                latitude,longitude,baro_altitude,latitude,longitude,baro_altitude,0,true_track, velocity, vertical_rate,
                ''
                ))
            conn.commit()
    time.sleep(60)
    logger.info("Paused for 60 seconds")
