/*
 Navicat Premium Dump SQL

 Source Server         : 59.110.225.35(root)
 Source Server Type    : MySQL
 Source Server Version : 80027 (8.0.27)
 Source Host           : 59.110.225.35:3306
 Source Schema         : langchain_01

 Target Server Type    : MySQL
 Target Server Version : 80027 (8.0.27)
 File Encoding         : 65001

 Date: 27/05/2026 15:22:17
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for users
-- ----------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `hashed_password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `role` enum('admin','user') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `username`(`username` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 5 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of users
-- ----------------------------
INSERT INTO `users` VALUES (1, 'admin', '$2b$12$cWePI.hZSaCzMn7wlF9X/ux9tC8hnHiSb4sh5bQ30K9vsQqeN8Gy2', 'admin', 1, '2026-05-24 10:14:14');
INSERT INTO `users` VALUES (2, 'test_user_1', '$2b$12$k1lMQNXLqRgw56MUiFfsSukBHXvgncNmiFyAuARr9AcRptccOZOsy', 'user', 1, '2026-05-24 10:14:24');
INSERT INTO `users` VALUES (3, 'normal_user', '$2b$12$vtmO7819w.y9vs1Y6YI6yunrGC9WhFpUNozLgp0gtJI1V3r4KSP4W', 'user', 1, '2026-05-24 10:14:28');
INSERT INTO `users` VALUES (4, '11', '$2b$12$TZlV2CJB3pmodFWd9Mfm7e7/LiR621.o0k5cXaHH5ay0oMKa9hy2C', 'user', 1, '2026-05-24 10:34:18');

SET FOREIGN_KEY_CHECKS = 1;
