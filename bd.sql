use projeto;
SET GLOBAL max_allowed_packet = 64 * 1048576; # 64 MB

drop table if exists person, video, annotation, videoAnnotation, thumbnail, currentVideoID;

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
        REFERENCES video (idVideo)
) ENGINE=InnoDB default CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS annotation (
    emotionType VARCHAR(50) primary key,
    emotion boolean not null,
    icon MEDIUMBLOB
) ENGINE=InnoDB default CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS videoAnnotation (
    emotionType VARCHAR(50),
	idFrame bigint,
	idVideo int,
    customText VARCHAR(80),
    duration tinytext,
	idAnnotation bigint PRIMARY KEY AUTO_INCREMENT,
	# CONSTRAINT fk_videoAnnotation_frame FOREIGN KEY (idFrame, idVideo)
       # REFERENCES frame (idFrame, idVideo),
	CONSTRAINT fk_videoAnnotation_annotation FOREIGN KEY (emotionType)
        REFERENCES annotation (emotionType)
) ENGINE=InnoDB default CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS sensorData (
    dataType VARCHAR(50),
	idFrame bigint,
	idVideo int,
    valueData VARCHAR(80),
    duration tinytext
) ENGINE=InnoDB default CHARSET=utf8mb4;


create table if not exists currentVideoID (
 idVideo int
);

insert into currentvideoid set idVideo=(select max(idVideo) from video) + 1;

INSERT INTO annotation VALUES ("happy", Null, 1);
INSERT INTO annotation VALUES ("sad", Null, 1);
INSERT INTO annotation VALUES ("sleepy", Null, 1);
INSERT INTO annotation VALUES ("angry", Null, 1);
INSERT INTO annotation VALUES ("surprised", Null, 1);
INSERT INTO annotation VALUES ("thinking", Null, 1);
INSERT INTO annotation VALUES ("custom", Null, 2);
INSERT INTO annotation VALUES ("other", Null, 3);

