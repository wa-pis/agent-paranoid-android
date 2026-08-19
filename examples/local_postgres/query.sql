SELECT
    o.order_id,
    o.customer_id,
    o.state,
    o.amount * 2 AS doubled_amount,
    o.expedited
FROM public.orders AS o
WHERE o.order_id < 999999
