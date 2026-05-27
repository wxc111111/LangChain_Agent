SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `image_uploads`;
CREATE TABLE `image_uploads` (
  `id`          int NOT NULL AUTO_INCREMENT,
  `user_id`     int NOT NULL,
  `filename`    varchar(255) NOT NULL,
  `stored_path` varchar(500) NOT NULL,
  `url`         varchar(500) NOT NULL,
  `size`        int NOT NULL,
  `created_at`  datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  CONSTRAINT `fk_image_uploads_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;
