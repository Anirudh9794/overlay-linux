CREATE TABLE IF NOT EXISTS `ece792-db`.`customer_table` (
  `customerId` int(11) NOT NULL AUTO_INCREMENT,
  `customerName` varchar(45) NOT NULL,
  PRIMARY KEY (`customerId`),
  UNIQUE KEY `customerId_UNIQUE` (`customerId`)
);