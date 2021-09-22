use projeto;
SET GLOBAL max_allowed_packet = 64 * 1048576; # 64 MB

drop table if exists person, video, annotation, videoAnnotation, thumbnail, currentVideoID, currentAnnotationID, currentSensorDataID;

CREATE TABLE IF NOT EXISTS person (
    username VARCHAR(20) PRIMARY KEY,
    password VARCHAR(250) NOT NULL,
    email VARCHAR(40) NOT NULL UNIQUE,
    adm boolean NOT NULL,
    CONSTRAINT chk_username CHECK (NOT username REGEXP '[^a-z] \'àáãâéêíóõôúçñ-]'),
    CONSTRAINT chk_password CHECK (CHAR_LENGTH(password) > 5)
) ENGINE=InnoDB default CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS video (
	idVideo bigint primary key auto_increment,
    uploadDate DATETIME NOT NULL,
    title VARCHAR(70) NOT NULL,
    username VARCHAR(20) NOT NULL,
    pathName VARCHAR(150) NOT NULL,
    recTime DATETIME,
    location VARCHAR(70),
    CONSTRAINT fk_video FOREIGN KEY (username)
        REFERENCES person (username)
) ENGINE=InnoDB default CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS thumbnail (
    idVideo int PRIMARY KEY,
    imagePath VARCHAR(150) NOT NULL,
	CONSTRAINT fk_frame FOREIGN KEY (idVideo)
        REFERENCES video (idVideo) ON DELETE CASCADE
) ENGINE=InnoDB default CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS annotation (
    emotionType VARCHAR(50) primary key,
    emotion boolean not null,
    icon MEDIUMBLOB
) ENGINE=InnoDB default CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS videoAnnotation (
    emotionType VARCHAR(50),
	iniTime tinytext,
	idVideo int,
    customText VARCHAR(80),
    duration tinytext,
	idAnnotation bigint PRIMARY KEY AUTO_INCREMENT,
    CONSTRAINT fk_video_annotated FOREIGN KEY (idVideo)
        REFERENCES video (idVideo) ON DELETE CASCADE,
	CONSTRAINT fk_videoAnnotation_annotation FOREIGN KEY (emotionType)
        REFERENCES annotation (emotionType) ON DELETE CASCADE
) ENGINE=InnoDB default CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS sensorData (
    dataType VARCHAR(50),
	iniTime tinytext,
	idVideo int,
    valueData VARCHAR(80),
    duration tinytext,
    idData bigint PRIMARY KEY AUTO_INCREMENT,
    CONSTRAINT fk_video_rel FOREIGN KEY (idVideo)
        REFERENCES video (idVideo) ON DELETE CASCADE
) ENGINE=InnoDB default CHARSET=utf8mb4;

create table if not exists currentVideoID (
 idVideo int not null
);

create table if not exists currentAnnotationID (
 idAnnotation bigint not null
);

create table if not exists currentSensorDataID (
 idData bigint not null
);

#if never created previous main tables
insert into currentVideoID set idVideo=1;
insert into currentannotationid set idAnnotation = 1;
insert into currentSensorDataID set idData = 1;

#else
#insert into currentVideoID set idVideo=(select max(idVideo) from video) + 1;
#insert into currentannotationid set idAnnotation=(select max(idAnnotation) from videoAnnotation) + 1;
#insert into currentSensorDataID set idData=(select max(idData) from sensorData) + 1;

INSERT INTO annotation VALUES ("happy", Null, 1);
INSERT INTO annotation VALUES ("sad", Null, 1);
INSERT INTO annotation VALUES ("afraid", Null, 1);
INSERT INTO annotation VALUES ("angry", Null, 1);
INSERT INTO annotation VALUES ("surprised", Null, 1);
INSERT INTO annotation VALUES ("disgusted", Null, 1);
INSERT INTO annotation VALUES ("custom", Null, 2);
INSERT INTO annotation VALUES ("other", Null, 3);

