# Personal Aircrafts Locations Aggregator Service

## Server components

PALAS is composed of collectors, a spatial database and a GDL90 TCP server.

- Python3 and ogn module
- postgresql database with postgis

### OGNFlowCollector.py

Daemon that collects informations from OGN Network, centralized in France

### OPENSKYFlowCollector.py

Daemon that collects informations from OpenSky Network, centralized in France

### GDL90TCPServer.py

TCP GDL90 server, on port 1234 (can be configured in parameters.conf)

### Install & run

#### On server

1. Clone git repository
2. Copy parameters_template.conf to parameters.conf and adapt configuration.
3. Create database aud user with database.sql script (execute commands as postgres user, and then as acft user as explained in comments)
4. run collectors as detached process

#### On android devices

Install Communication bridge pro, and configure it:

Device A: TCP Client

- Server IP: PALAS TCP Server IP
- Remote port: 1234

Device B: UDP Socket

- Local: 4001
- Remote IP: 127.0.0.1
- Remote port: 4000

Run application that use GDL90 flow (like SDVFR Next)

#### On grafana map

Install grafana and Geomap plugin. Configure postgresql database as datasource.

Create a dashboard and add geomap panel. Select aircrafts:

```sql
SELECT
  callsign,
  address_type,
  altitude,
  track,
  hspeed,
  vspeed,
  latitude,
  longitude,
  update_time
FROM
  acft_position
WHERE
  $__timeFilter(update_time)
LIMIT
  50
```

In geomap properties, slect layer type "Markers", Symbol "Plane", Rotation angle "track", text label "callsign"

## TODO

- Database cleaning daemon

## Resources
* OGN client: https://github.com/glidernet/python-ogn-client
* OGN APRS format: http://wiki.glidernet.org/wiki:ogn-flavoured-aprs
* sender format: https://github.com/svoop/ogn_client-ruby/wiki/SenderBeacon
* GDL90 python library : https://github.com/NathanVaughn/gdl90py
* PostGIS: https://postgis.net/workshops/postgis-intro/geometries.html

## Data Specifications
Categories:
Aircraft Category Type table Hexadecimal valueas assigned by FLARM. Range: from 0 to F:

- 0 = reserved
- 1 = glider/motor glider (turbo, self-launch, jet) / TMG
- 2 = tow plane/tug plane
- 3 = helicopter/gyrocopter/rotorcraft
- 4 = skydiver, parachute (Do not use for drop plane!)
- 5 = drop plane for skydivers
- - 6 = hang glider (hard)
- 7 = paraglider (soft)
- 8 = aircraft with reciprocating engine(s)
- 9 = aircraft with jet/turboprop engine(s)
- A = unknown
- B = balloon (hot, gas, weather, static)
- C = airship, blimp, zeppelin
- D = unmanned aerial vehicle (UAV, RPAS, drone)
- E = (reserved)
- F = static obstacle

Address type:

- 1 = ICAO
- 2 = FLARM
- 3 = OGN tracker
