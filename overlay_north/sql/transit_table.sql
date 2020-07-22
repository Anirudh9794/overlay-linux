CREATE TABLE IF NOT EXISTS `ece792-db`.`transit_table` (
  `transit_id` int(11) NOT NULL AUTO_INCREMENT,
  `customer_id` int(11) NOT NULL,
  `host` varchar(45) NOT NULL,
  `reliability_factor` int(45) NOT NULL,
  PRIMARY KEY (`transit_id`),
  FOREIGN KEY (`customer_id`) REFERENCES `ece792-db`.`customer_table`(`customerId`),
  UNIQUE KEY `transit_idUNIQUE` (`transit_id`)
);
