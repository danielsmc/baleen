DROP TABLE IF EXISTS `retweets`;

CREATE TABLE `retweets` (
  `user_id` bigint(11) unsigned NOT NULL,
  `tweet_id` bigint(11) NOT NULL DEFAULT '0',
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`user_id`,`tweet_id`),
  KEY `created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `tweet_urls`;

CREATE TABLE `tweet_urls` (
  `tweet_id` bigint(11) unsigned NOT NULL,
  `url_hash` varchar(255) NOT NULL DEFAULT '',
  PRIMARY KEY (`tweet_id`,`url_hash`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `tweets`;

CREATE TABLE `tweets` (
  `tweet_id` bigint(11) unsigned NOT NULL,
  `text` text CHARACTER SET utf8mb4 NOT NULL,
  `created_at` datetime NOT NULL,
  `user_id` bigint(20) NOT NULL,
  `expanded_text` text CHARACTER SET utf8mb4,
  PRIMARY KEY (`tweet_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `urls`;

CREATE TABLE `urls` (
  `url_hash` varchar(255) NOT NULL DEFAULT '',
  `url` text NOT NULL,
  PRIMARY KEY (`url_hash`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `users`;

CREATE TABLE `users` (
  `user_id` bigint(11) unsigned NOT NULL,
  `screen_name` varchar(255) DEFAULT NULL,
  `profile_image_url` text,
  `impact` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;