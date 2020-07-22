CREATE TABLE IF NOT EXISTS `ece792-db`.`vpc_table` (
  `vpcId` int(11) NOT NULL AUTO_INCREMENT,
  `vpcName` varchar(45) NOT NULL,
  `customerId` int(11) NOT NULL,
  `host` varchar(45) NOT NULL,
  `scaleFactor` int(45) NOT NULL,
  PRIMARY KEY (`vpcId`),
  FOREIGN KEY (`customerId`) REFERENCES `ece792-db`.`customer_table`(`customerId`),
  UNIQUE KEY `vpcId_UNIQUE` (`vpcId`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
