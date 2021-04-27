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
    CONSTRAINT fk_video FOREIGN KEY (username)
        REFERENCES person (username)
) ENGINE=InnoDB default CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS frame (
	idFrame int primary key auto_increment,
    idVideo int,
    image MEDIUMBLOB,
	CONSTRAINT fk_frame FOREIGN KEY (idVideo)
        REFERENCES video (idVideo)
) ENGINE=InnoDB default CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS annotation (
    emotionType tinyint primary key,
    feeling VARCHAR(50) NOT NULL,
    icon MEDIUMBLOB
) ENGINE=InnoDB default CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS videoAnnotation (
    emotionType tinyint,
	idFrame int,
    customText VARCHAR(80),
	CONSTRAINT fk_videoAnnotation_frame FOREIGN KEY (idFrame)
        REFERENCES frame (idFrame),
	CONSTRAINT fk_videoAnnotation_annotation FOREIGN KEY (emotionType)
        REFERENCES annotation (emotionType)
) ENGINE=InnoDB default CHARSET=utf8mb4;

INSERT INTO annotation VALUES (1, "happiness", Null);
INSERT INTO annotation VALUES (2, "sadness", Null);
INSERT INTO annotation VALUES (3, "sleepiness", Null);
INSERT INTO annotation VALUES (4, "anger", Null);
INSERT INTO annotation VALUES (5, "surprised", Null);
INSERT INTO annotation VALUES (6, "thinking", Null);
INSERT INTO annotation VALUES (7, "custom", Null);
