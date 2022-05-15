BEGIN;

SELECT plan(4);

SELECT set_eq(
	'SELECT name FROM ml.models',
	ARRAY['ssd']
);

INSERT INTO ml.models (name, flavor, model_type)
VALUES ('new_ssd', 'pytorch', 'ssd');

SELECT has_function('ml', 'new_ssd', 'test UDF is created for new_ssd');

SELECT set_eq(
	'SELECT name FROM ml.models',
ARRAY['ssd', 'new_ssd']);

-- DELETE model and remove UDF
DELETE FROM ml.models WHERE name = 'new_ssd';

SELECT hasnt_function(
	'ml',
	'new_ssd',
	'ml.new_ssd should be deleted via trigger'
);

SELECT * FROM finish();
ROLLBACK;
