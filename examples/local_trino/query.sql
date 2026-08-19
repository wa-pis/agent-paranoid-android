SELECT
    n.nationkey,
    upper(n.name) AS nation_name,
    n.regionkey
FROM tpch.tiny.nation AS n
WHERE n.nationkey < 999999
