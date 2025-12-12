from ogn.client import AprsClient
from ogn.parser import parse, AprsParseError
import logging
import logging.config
import psycopg2
from psycopg2.extras import LoggingConnection
import datetime
import configparser

logging.config.fileConfig('logging.conf')
logger = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read('parameters.conf')

conn = psycopg2.connect(connection_factory=LoggingConnection, **config['database'])
conn.initialize(logger)
cur = conn.cursor()

def process_beacon(raw_message):
    try:
        beacon = parse(raw_message)
        logger.debug('Received {aprs_type}: {raw_message}'.format(**beacon))
        if(beacon["aprs_type"] == "position"):
            try:
                logger.info('Position received for %s', beacon["name"])
                if (beacon.get("user_comment")== None):
                    beacon["user_comment"]=""
                if (beacon.get("track")== None):
                    beacon["track"]=""
                if (beacon.get("flightlevel")== None):
                    beacon["flightlevel"]=0
            
                cur.execute(
                    "INSERT INTO acft_position (callsign, address_type, address, report_time, " \
                    "stealth, no_tracking, category, " \
                    "location, latitude, longitude,altitude, flight_level, track, hspeed, vspeed, " \
                    "user_comment) " \
                    "VALUES (%s, %s, %s, %s," \
                    "%s, %s, %s, " \
                    "'POINT(%s %s %s)', %s, %s, %s, %s, %s, %s, %s," \
                    "%s) " \
                    "ON CONFLICT(callsign) DO " \
                    "UPDATE SET address_type = %s, address = %s, update_time = %s, report_time = %s," \
                    "stealth = %s, no_tracking = %s, category = %s, " \
                    "location = 'POINT(%s %s %s)', latitude = %s, longitude = %s, altitude = %s, flight_level = %s, track = %s, hspeed = %s, vspeed = %s, "
                    "user_comment = %s;",
                    (beacon["name"], beacon["address_type"], beacon["address"], beacon["timestamp"], 
                    beacon["stealth"], beacon["no-tracking"], beacon["aircraft_type"],
                    beacon["latitude"],beacon["longitude"],beacon["altitude"],beacon["latitude"],beacon["longitude"],beacon["altitude"],beacon["flightlevel"], beacon["track"], beacon["ground_speed"], beacon["climb_rate"],
                    beacon["user_comment"],
                    beacon["address_type"], beacon["address"], datetime.datetime.now(), beacon["timestamp"], 
                    beacon["stealth"], beacon["no-tracking"], beacon["aircraft_type"],
                    beacon["latitude"],beacon["longitude"],beacon["altitude"],beacon["latitude"],beacon["longitude"],beacon["altitude"],beacon["flightlevel"], beacon["track"], beacon["ground_speed"], beacon["climb_rate"],
                    beacon["user_comment"]
                 ))
                conn.commit()
            except KeyError as e:
                logger.warn('Missing Key %s for  %s', format(e), beacon["name"])
                pass

    except AprsParseError as e:
        logger.error('Error, {}'.format(e.message))

# 500 NM autours de Paris
client = AprsClient(aprs_user=config['ogn']['aprs_user'], aprs_filter=config['ogn']['aprs_filter'])
client.connect()

try:
    
    client.run(callback=process_beacon, autoreconnect=True)
except KeyboardInterrupt:
    logger.info('Stop ogn gateway')
    client.disconnect()
    cur.close()
    conn.close()