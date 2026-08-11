CREATE TABLE public.customers (
    customer_id BIGINT PRIMARY KEY,
    status TEXT NOT NULL CHECK (status IN ('active', 'paused')),
    joined_on DATE NOT NULL
);

CREATE TABLE public.orders (
    order_id BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES public.customers(customer_id),
    state TEXT NOT NULL CHECK (state IN ('new', 'paid', 'shipped')),
    amount DOUBLE PRECISION,
    expedited BOOLEAN NOT NULL
);

INSERT INTO public.customers VALUES
    (1, 'active', '2026-01-10'),
    (2, 'paused', '2026-02-11'),
    (3, 'active', '2026-03-12');

INSERT INTO public.orders VALUES
    (101, 1, 'new', 12.5, FALSE),
    (102, 1, 'paid', 25.0, TRUE),
    (103, 2, 'shipped', NULL, FALSE),
    (104, 3, 'paid', 17.75, FALSE);

GRANT CONNECT ON DATABASE apa_source TO apa_reader;
GRANT USAGE ON SCHEMA public TO apa_reader;
GRANT SELECT ON public.customers, public.orders TO apa_reader;
