CREATE TABLE IF NOT EXISTS `ece792-db`.`vm_table` (
  `vmId` int(11) NOT NULL AUTO_INCREMENT,
  `vmName` varchar(45) NOT NULL,
  `macAddr` varchar(45) NOT NULL,
  `ipAddr` varchar(45) DEFAULT NULL,
  `subnetId` int(11) NOT NULL,
  `vpcId` int(11) NOT NULL,
  PRIMARY KEY (`vmId`),
  UNIQUE KEY `vmId_UNIQUE` (`vmId`),
  KEY `subnetId_idx` (`subnetId`),
  KEY `vpcId_idx` (`vpcId`),
  foreign key (subnetId) references subnet_table(subnetId),
  foreign key(vpcId) references vpc_table(vpcId)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;