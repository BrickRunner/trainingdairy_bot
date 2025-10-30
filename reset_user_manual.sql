
UPDATE user_settings
SET name = NULL,
    birth_date = NULL,
    gender = NULL,
    height = NULL,
    weight = NULL,
    main_training_types = '[]',
    timezone = 'Europe/Moscow'
WHERE user_id = 1611441720;


SELECT user_id, name, birth_date, gender, height, weight, main_training_types, timezone
FROM user_settings
WHERE user_id = YOUR_USER_ID;
