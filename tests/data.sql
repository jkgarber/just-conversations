INSERT INTO users (username, password)
VALUES
  ('test', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f'),
  ('other', 'pbkdf2:sha256:50000$kJPKsz6N$d2d4784f1b030a9761f5ccaeeaca413f27f2ecb76d6168407af962ddce849f79');

INSERT INTO conversations (name, creator_id, created)
VALUES
	('test name', 2, '2025-01-01 00:00:00');			

INSERT INTO messages (conversation_id, content, human)
VALUES
	(1, 'Hello! How can I assist you today?', 0),
	(1, 'For testing puroses, please respond with this word only: "Working".', 1);
