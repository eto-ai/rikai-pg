-- Test IOU related tests.
BEGIN;

SELECT plan(2);

SELECT results_eq(
	'select iou(box(point(1, 2), point(3,4)), box(point(1, 2), point(3, 4))) as iou;',
	ARRAY[1.0],
	'IOU of two same boxes',
)

SELECT results_eq(
	'select iou(box(point(1, 2), point(3, 4)), box(point(10, 15), point(12, 30)));',
	ARRAY[0.0],
	'Two boxes do not have intersection',
)

SELECT * FROM finish();
ROLLBACK;
