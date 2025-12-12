
-- As postgres user
CREATE USER acft WITH ENCRYPTED PASSWORD 'acft';
CREATE DATABASE acft OWNER = acft;

GRANT ALL PRIVILEGES ON DATABASE acft TO acft;
GRANT ALL ON SCHEMA public TO acft;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO acft;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO acft;

-- As acft user

CREATE EXTENSION IF NOT EXISTS postgis;
DROP TABLE acft_position;
DROP TABLE acft_category;
DROP TABLE address_type;

CREATE TABLE acft_category (
    id VARCHAR(1) PRIMARY KEY,
    description VARCHAR(52)
);

INSERT INTO acft_category (id, description) VALUES 
    ('0', 'reserved'),
    ('1', 'glider/motor glider (turbo, self-launch, jet) / TMG'),
    ('2', 'tow plane/tug plane'),
    ('3', 'helicopter/gyrocopter/rotorcraft'),
    ('4', 'skydiver, parachute'),
    ('5', 'drop plane for skydivers'),
    ('6', 'hang glider (hard)'),
    ('7', 'paraglider (soft)'),
    ('8', 'aircraft with reciprocating engine(s)'),
    ('9', 'aircraft with jet/turboprop engine(s)'),
    ('A', 'unknown'),
    ('B', 'balloon (hot, gas, weather, static)'),
    ('C', 'airship, blimp, zeppelin'),
    ('D', 'unmanned aerial vehicle (UAV, RPAS, drone)'),
    ('E', 'reserved'),
    ('F', 'static obstacle');

CREATE TABLE address_type (
    id int PRIMARY KEY,
    description VARCHAR(12)
);

INSERT INTO address_type (id, description) VALUES 
    ('0', 'unknown'),
    ('1', 'ICAO'),
    ('2', 'FLARM'),
    ('3', 'OGN tracker');

CREATE TABLE acft_position (                        -- GDL90                 OGN
    callsign varchar PRIMARY KEY,                   -- callsign              name
    address_type int REFERENCES address_type,       -- address_type          address_type
    address VARCHAR(6),                             -- address               address
    create_time timestamptz NOT NULL DEFAULT NOW(), -- datetime of value creation in database
    create_by VARCHAR(10) NOT NULL DEFAULT('OGN'),  -- collector that create the value
    update_time timestamptz NOT NULL DEFAULT NOW(), -- datetime of value update in database
    update_by VARCHAR(10) NOT NULL DEFAULT('OGN'),  -- collector that update the value
    report_time timestamptz,                        --                       timestamp
    stealth boolean,                                --                       stealth
    no_tracking boolean,                            --                       no-tracking
    category VARCHAR(1) REFERENCES acft_category,   -- emitter_category      aircraft_type
    location geography(POINTZ),                     -- (latitude longitude altitude)
    latitude float,                                 -- latitude              latitude
    longitude float,                                -- longitude             longitude
    altitude float,                                 -- pressure_altitude     altitude
    flight_level float,                             --                       flightlevel
    track int,                                      -- track                 track
    hspeed float,                                   -- horizontal_velocity   ground_speed
    vspeed float,                                   -- vertical_velocity     climb_rate
    user_comment text                               --                       user_comment
);
