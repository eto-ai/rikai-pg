-- Test IOU related tests.
BEGIN;

SELECT plan(1);

SELECT results_eq(
	'select iou(box(point(1, 2), point(3,4)), box(point(1, 2), point(3, 4))) as iou;',
	ARRAY[0],
	'IOU of two same boxes',
	)

SELECT * FROM finish();
ROLLBACK;
