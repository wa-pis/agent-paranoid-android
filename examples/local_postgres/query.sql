SELECT
    o.order_id,
    o.customer_id,
    o.state,
    o.amount AS source_amount,
    o.expedited
FROM public.orders AS o
WHERE o.order_id < 999999
