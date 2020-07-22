CREATE TABLE IF NOT EXISTS `ece792-db`.`subnet_table` (
  `subnetId` int(11) NOT NULL AUTO_INCREMENT,
  `ipAddress` varchar(45) NOT NULL,
  `subnetName` varchar(45) NOT NULL,
  `vpcId` int(11) NOT NULL,
  PRIMARY KEY (`subnetId`),
  UNIQUE KEY `subnetId_UNIQUE` (`subnetId`),
  KEY `vpcId_idx` (`vpcId`),
  CONSTRAINT `vpcId` FOREIGN KEY (`vpcId`) REFERENCES `vpc_table` (`vpcId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=latin1;