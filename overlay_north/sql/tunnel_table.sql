CREATE TABLE IF NOT EXISTS `ece792-db`.`tunnel_table` (
  `tunnel_id` int(11) NOT NULL AUTO_INCREMENT,
  `transit_id` int(45) NOT NULL,
  `vpc_id` int(45) NOT NULL,
  `tunnel_type` varchar(45) NOT NULL,
  PRIMARY KEY (`tunnel_id`),
  FOREIGN KEY (`transit_id`) REFERENCES `ece792-db`.`transit_table`(`transit_id`),
  FOREIGN KEY (`vpc_id`) REFERENCES `ece792-db`.`vpc_table`(`vpcId`),
  UNIQUE KEY `tunnel_idUNIQUE` (`tunnel_id`)
);