SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `messages`;
DROP TABLE IF EXISTS `conversations`;

CREATE TABLE `conversations` (
  `id`          int NOT NULL AUTO_INCREMENT,
  `user_id`     int NOT NULL,
  `title`       varchar(200) DEFAULT '',
  `summary`     text,
  `round_count` int DEFAULT 0,
  `is_active`   tinyint(1) DEFAULT 1,
  `created_at`  datetime NOT NULL DEFAULT (now()),
  `updated_at`  datetime NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_active` (`user_id`, `is_active`),
  CONSTRAINT `fk_conversations_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `messages` (
  `id`              bigint NOT NULL AUTO_INCREMENT,
  `conversation_id` int NOT NULL,
  `role`            enum('user','assistant','system','tool') NOT NULL,
  `content`         text NOT NULL,
  `created_at`      datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `idx_conversation` (`conversation_id`, `created_at`),
  CONSTRAINT `fk_messages_conversation` FOREIGN KEY (`conversation_id`) REFERENCES `conversations` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;
