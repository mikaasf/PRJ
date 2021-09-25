-- phpMyAdmin SQL Dump
-- version 5.1.0
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Sep 25, 2021 at 11:46 AM
-- Server version: 10.4.18-MariaDB
-- PHP Version: 8.0.3

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `projeto`
--

-- --------------------------------------------------------

--
-- Table structure for table `annotation`
--

CREATE TABLE `annotation` (
  `emotionType` varchar(50) NOT NULL,
  `emotion` tinyint(1) DEFAULT NULL,
  `icon` mediumblob DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `annotation`
--

INSERT INTO `annotation` (`emotionType`, `emotion`, `icon`) VALUES
('afraid', 1, NULL),
('angry', 1, NULL),
('custom', 2, NULL),
('disgusted', 1, NULL),
('happy', 1, NULL),
('other', 3, NULL),
('sad', 1, NULL),
('surprised', 1, NULL);

-- --------------------------------------------------------

--
-- Table structure for table `currentannotationid`
--

CREATE TABLE `currentannotationid` (
  `idAnnotation` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

--
-- Dumping data for table `currentannotationid`
--

INSERT INTO `currentannotationid` (`idAnnotation`) VALUES
(55);

-- --------------------------------------------------------

--
-- Table structure for table `currentsensordataid`
--

CREATE TABLE `currentsensordataid` (
  `idData` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

--
-- Dumping data for table `currentsensordataid`
--

INSERT INTO `currentsensordataid` (`idData`) VALUES
(1);

-- --------------------------------------------------------

--
-- Table structure for table `currentvideoid`
--

CREATE TABLE `currentvideoid` (
  `idVideo` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

--
-- Dumping data for table `currentvideoid`
--

INSERT INTO `currentvideoid` (`idVideo`) VALUES
(66);

-- --------------------------------------------------------

--
-- Table structure for table `person`
--

CREATE TABLE `person` (
  `username` varchar(20) NOT NULL,
  `password` varchar(250) NOT NULL,
  `email` varchar(40) NOT NULL,
  `adm` tinyint(1) NOT NULL
) ;

--
-- Dumping data for table `person`
--

INSERT INTO `person` (`username`, `password`, `email`, `adm`) VALUES
('admin', 'pbkdf2:sha256:150000$LTQPdETe$ae6c08a59429b79a62893309a5e3698b91359fd0153868df6970213e87a4c01d', 'admin@admin.com', 1);

-- --------------------------------------------------------

--
-- Table structure for table `sensordata`
--

CREATE TABLE `sensordata` (
  `dataType` varchar(50) DEFAULT NULL,
  `iniTime` tinytext DEFAULT NULL,
  `idVideo` int(11) DEFAULT NULL,
  `valueData` varchar(80) DEFAULT NULL,
  `duration` tinytext DEFAULT NULL,
  `idData` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `sensordata`
--

INSERT INTO `sensordata` (`dataType`, `iniTime`, `idVideo`, `valueData`, `duration`, `idData`) VALUES
('BPM', '50.02', 1, '94', '0.02', 1),
('BPM', '50.040000000000006', 1, '94', '0.02', 2),
('BPM', '50.06000000000001', 1, '94', '0.02', 3),
('BPM', '50.08000000000001', 1, '94', '0.02', 4),
('BPM', '50.100000000000016', 1, '94', '0.02', 5),
('BPM', '50.12000000000002', 1, '91', '0.02', 6),
('BPM', '50.14000000000002', 1, '91', '0.02', 7),
('BPM', '50.02', 1, '94', '0.02', 8),
('BPM', '50.040000000000006', 1, '94', '0.02', 9),
('BPM', '50.06000000000001', 1, '94', '0.02', 10),
('BPM', '50.08000000000001', 1, '94', '0.02', 11),
('BPM', '50.100000000000016', 1, '94', '0.02', 12),
('BPM', '50.12000000000002', 1, '91', '0.02', 13),
('BPM', '50.14000000000002', 1, '91', '0.02', 14);

-- --------------------------------------------------------

--
-- Table structure for table `thumbnail`
--

CREATE TABLE `thumbnail` (
  `idVideo` int(11) NOT NULL,
  `imagePath` varchar(150) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Table structure for table `video`
--

CREATE TABLE `video` (
  `idVideo` int(11) NOT NULL,
  `uploadDate` datetime NOT NULL,
  `title` varchar(70) NOT NULL,
  `username` varchar(20) NOT NULL,
  `pathName` varchar(150) NOT NULL,
  `recTime` datetime DEFAULT NULL,
  `location` varchar(70) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Table structure for table `videoannotation`
--

CREATE TABLE `videoannotation` (
  `emotionType` varchar(50) DEFAULT NULL,
  `iniTime` tinytext DEFAULT NULL,
  `idVideo` int(11) DEFAULT NULL,
  `customText` varchar(80) DEFAULT NULL,
  `duration` tinytext DEFAULT NULL,
  `idAnnotation` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `annotation`
--
ALTER TABLE `annotation`
  ADD PRIMARY KEY (`emotionType`);

--
-- Indexes for table `person`
--
ALTER TABLE `person`
  ADD PRIMARY KEY (`username`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Indexes for table `sensordata`
--
ALTER TABLE `sensordata`
  ADD PRIMARY KEY (`idData`),
  ADD KEY `fk_video_rel` (`idVideo`);

--
-- Indexes for table `thumbnail`
--
ALTER TABLE `thumbnail`
  ADD PRIMARY KEY (`idVideo`);

--
-- Indexes for table `video`
--
ALTER TABLE `video`
  ADD PRIMARY KEY (`idVideo`),
  ADD KEY `fk_video` (`username`);

--
-- Indexes for table `videoannotation`
--
ALTER TABLE `videoannotation`
  ADD PRIMARY KEY (`idAnnotation`),
  ADD KEY `fk_video_annotated` (`idVideo`),
  ADD KEY `fk_videoAnnotation_annotation` (`emotionType`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `sensordata`
--
ALTER TABLE `sensordata`
  MODIFY `idData` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=15;

--
-- AUTO_INCREMENT for table `video`
--
ALTER TABLE `video`
  MODIFY `idVideo` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=65;

--
-- AUTO_INCREMENT for table `videoannotation`
--
ALTER TABLE `videoannotation`
  MODIFY `idAnnotation` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=55;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `sensordata`
--
ALTER TABLE `sensordata`
  ADD CONSTRAINT `fk_video_rel` FOREIGN KEY (`idVideo`) REFERENCES `video` (`idVideo`) ON DELETE CASCADE;

--
-- Constraints for table `thumbnail`
--
ALTER TABLE `thumbnail`
  ADD CONSTRAINT `fk_frame` FOREIGN KEY (`idVideo`) REFERENCES `video` (`idVideo`) ON DELETE CASCADE;

--
-- Constraints for table `video`
--
ALTER TABLE `video`
  ADD CONSTRAINT `fk_video` FOREIGN KEY (`username`) REFERENCES `person` (`username`);

--
-- Constraints for table `videoannotation`
--
ALTER TABLE `videoannotation`
  ADD CONSTRAINT `fk_videoAnnotation_annotation` FOREIGN KEY (`emotionType`) REFERENCES `annotation` (`emotionType`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_video_annotated` FOREIGN KEY (`idVideo`) REFERENCES `video` (`idVideo`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
