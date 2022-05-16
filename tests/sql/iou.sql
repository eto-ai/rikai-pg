-- IOU related tests.
BEGIN;

SELECT plan(3);

SELECT set_eq(
	'select iou(box(point(1, 2), point(3,4)), box(point(1, 2), point(3, 4)));',
	ARRAY[1],
	'IOU of two same boxes'
);

SELECT set_eq(
	'select iou(box(point(1, 2), point(3, 4)), box(point(10, 15), point(12, 30)));',
	ARRAY[0],
	'Two boxes do not have intersection'
);

SELECT ok(
	abs(t.iou - (1.0 / 7)) < 0.0000001,
	'approx equality of ious'
) FROM (
	SELECT iou(box(point(0, 0), point(20, 20)), box(point(10, 10), point(30, 30)))
) AS t;

SELECT * FROM finish();
ROLLBACK;
