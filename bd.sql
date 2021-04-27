use projeto;
SET GLOBAL max_allowed_packet = 64 * 1048576; # 64 MB

drop table if exists person, video, annotation, videoAnnotation, frame;

CREATE TABLE IF NOT EXISTS person (
    username VARCHAR(20) PRIMARY KEY,
    password VARCHAR(250) NOT NULL,
    email VARCHAR(40) NOT NULL UNIQUE,
    adm boolean NOT NULL,
    CONSTRAINT chk_username CHECK (NOT username REGEXP '[^a-z] \'àáãâéêíóõôúçñ-]'),
    CONSTRAINT chk_password CHECK (CHAR_LENGTH(password) > 5)
) ENGINE=InnoDB default CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS video (
	idVideo int primary key auto_increment,
    uploadDate DATETIME NOT NULL,
    title VARCHAR(70) NOT NULL,
    username VARCHAR(20) NOT NULL,
    pathName VARCHAR(150) NOT NULL,
    recTime DATETIME,
    location VARCHAR(70),
    CONSTRAINT fk_video FOREIGN KEY (username)
        REFERENCES person (username)
) ENGINE=InnoDB default CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS frame (
	idFrame int,
    idVideo int,
    image MEDIUMBLOB,
    CONSTRAINT pk_frame PRIMARY KEY(idFrame, idVideo), 
	CONSTRAINT fk_frame FOREIGN KEY (idVideo)
        REFERENCES video (idVideo)
) ENGINE=InnoDB default CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS annotation (
    emotionType VARCHAR(50) primary key,
    icon MEDIUMBLOB
) ENGINE=InnoDB default CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS videoAnnotation (
    emotionType VARCHAR(50),
	idFrame int,
	idVideo int,
    customText VARCHAR(80),
	CONSTRAINT fk_videoAnnotation_frame FOREIGN KEY (idFrame, idVideo)
        REFERENCES frame (idFrame, idVideo),
	CONSTRAINT fk_videoAnnotation_annotation FOREIGN KEY (emotionType)
        REFERENCES annotation (emotionType)
) ENGINE=InnoDB default CHARSET=utf8mb4;

INSERT INTO annotation VALUES ("happy", Null);
INSERT INTO annotation VALUES ("sad", Null);
INSERT INTO annotation VALUES ("sleepy", Null);
INSERT INTO annotation VALUES ("angry", Null);
INSERT INTO annotation VALUES ("surprised", Null);
INSERT INTO annotation VALUES ("thinking", Null);
INSERT INTO annotation VALUES ("custom", Null);
INSERT INTO annotation VALUES ("heartbeat", Null);
INSERT INTO annotation VALUES ("other", Null);
