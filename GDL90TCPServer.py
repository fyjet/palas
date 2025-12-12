import binascii
import socket
import struct
import time
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

dbconn = psycopg2.connect(connection_factory=LoggingConnection, **config['database'])
dbconn.initialize(logger)
cur = dbconn.cursor()

from gdl90py.enums import (
    Accuracy,
    AddressType,
    EmergencyPriorityCode,
    EmitterCategory,
    Integrity,
    TrackType,
)

from gdl90py.exceptions import DataTooLong, InvalidCallsign
from gdl90py.messages.heartbeat import HeartbeatMessage
from gdl90py.messages.traffic_report import TrafficReportMessage

def getNow():
    return {
        "hour" : int(datetime.datetime.now(datetime.UTC).strftime('%H')),
        "min" : int(datetime.datetime.now(datetime.UTC).strftime('%M')),
        "sec" : int(datetime.datetime.now(datetime.UTC).strftime('%S'))
    }

def getHeartbeatMessage():
    now = getNow()
    hb = HeartbeatMessage(
        gps_position_valid=True,
        maintenance_required=False,
        ident_talkback=True,
        self_assigned_address_talkback=False,
        gps_battery_low=True,
        RATCS_talkback=False,
        UAT_initialized=True,
        CSA_requested=False,
        CSA_unavailable=True,
        UTC_timing_valid=False,
        timestamp=datetime.time(
            hour=now["hour"], minute=now["min"], second=now["sec"], tzinfo=datetime.timezone.utc
        ),
        uplink_messages_count=234,
        basic_long_messages_count=678,
    )
    logger.debug("heartbeat")
    return binascii.hexlify(hb.serialize(outgoing_lsb=False)).decode("utf-8")

def getTrafficReportMessage(callsign, address_type, address, category, lat, lon, alt, hspeed, vspeed, track):
    tr = TrafficReportMessage(
        traffic_alert=True,
        address_type=AddressType.ads_b_icao,
        address=int(address,16),
        latitude=lat,
        longitude=lon,
        pressure_altitude=alt,
        track_type=TrackType.true_track_angle,
        report_extrapolated=False,
        airborne=True,
        integrity=Integrity.less_than_25_m_hpl_and_37_5_m_vpl,
        accuracy=Accuracy.less_than_30_m_hfom_and_45_m_vfom,
        horizontal_velocity=hspeed,
        vertical_velocity=vspeed,
        track=track,
        emitter_category=EmitterCategory.light,
        callsign=callsign,
        emergency_priority_code=EmergencyPriorityCode.no_emergency,
    )
    """
    tr = TrafficReportMessage(
        traffic_alert=True,
        address_type=AddressType.ads_b_icao,
        address=int("52642511", 8),
        latitude=47.243489,
        longitude=2.065959,
        pressure_altitude=5000,
        track_type=TrackType.true_track_angle,
        report_extrapolated=False,
        airborne=True,
        integrity=Integrity.less_than_25_m_hpl_and_37_5_m_vpl,
        accuracy=Accuracy.less_than_30_m_hfom_and_45_m_vfom,
        horizontal_velocity=123,
        vertical_velocity=64,
        track=45,
        emitter_category=EmitterCategory.light,
        callsign="N825V",
        emergency_priority_code=EmergencyPriorityCode.no_emergency,
    )
    """
    logger.debug("trafic")
    return binascii.hexlify(tr.serialize(outgoing_lsb=False)).decode("utf-8")

def handle_client(conn, addr):
    logger.info('Connected by %s', addr)
    try:
        while True:

            conn.sendall(binascii.unhexlify(getHeartbeatMessage()))
            
            cur.execute("SELECT callsign, address_type, address, category, latitude, longitude, altitude, hspeed, vspeed, track FROM acft_position WHERE update_time >= NOW() - INTERVAL '5 minutes';")
            
            for acft in cur.fetchall():
                conn.sendall(binascii.unhexlify(getTrafficReportMessage(acft[0],acft[1],acft[2],acft[3],acft[4],acft[5],acft[6],acft[7],acft[8],acft[9])))
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Execution interrupted by user.")
    except (ConnectionError, struct.error) as e:
        logger.error("[ERROR] %s", e)
    finally:
        conn.close()
        cur.close()
        dbconn.close()
        logger.info("Disconnected %s", addr)

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((config['gdl90']['host'], int(config['gdl90']['port'])))
        server_socket.listen()
        logger.info("Server listening on %s %s (local IP %s)", config['gdl90']['host'], config['gdl90']['port'], socket.gethostbyname(socket.gethostname()))

        try:
            while True:
                conn, addr = server_socket.accept()
                handle_client(conn, addr)
        except KeyboardInterrupt:
            logger.info('Stop gateway')
        
if __name__ == "__main__":
    start_server()
