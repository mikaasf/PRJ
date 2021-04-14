use projeto;
SET GLOBAL max_allowed_packet = 64 * 1048576; # 64 MB

drop table if exists person, video, annotation, videoAnnotation, frame;

CREATE TABLE person (
    username VARCHAR(100) PRIMARY KEY,
    password VARCHAR(30) NOT NULL,
    adm BIT NOT NULL,
    CONSTRAINT chk_username CHECK (NOT username REGEXP '[^a-z] \'àáãâéêíóõôúçñ-]'),
    CONSTRAINT chk_password CHECK (CHAR_LENGTH(password) > 5)
);

CREATE TABLE video (
	idVideo int primary key auto_increment,
    uploadDate DATETIME NOT NULL,
    title VARCHAR(70) NOT NULL,
    username VARCHAR(100) NOT NULL,
    CONSTRAINT fk_video FOREIGN KEY (username)
        REFERENCES person (username)
);

CREATE TABLE frame (
	idFrame int primary key auto_increment,
    idVideo int,
    image MEDIUMBLOB,
	CONSTRAINT fk_frame FOREIGN KEY (idVideo)
        REFERENCES video (idVideo)
);

CREATE TABLE annotation (
    emotionType tinyint primary key,
    feeling VARCHAR(100) NOT NULL,
    icon MEDIUMBLOB
);

CREATE TABLE videoAnnotation (
    emotionType tinyint,
	idFrame int,
    custonText VARCHAR(80) NOT NULL,
    heartbeatRate int,
	CONSTRAINT fk_videoAnnotation_frame FOREIGN KEY (idFrame)
        REFERENCES frame (idFrame),
	CONSTRAINT fk_videoAnnotation_annotation FOREIGN KEY (emotionType)
        REFERENCES annotation (emotionType)
);

