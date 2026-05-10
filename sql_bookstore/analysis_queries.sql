-- 1. Выручка по месяцам
SELECT
    strftime('%Y-%m', o.order_date) AS month,
    ROUND(SUM(oi.quantity * b.price), 2) AS revenue
FROM orders AS o
JOIN order_items AS oi ON o.order_id = oi.order_id
JOIN books AS b ON oi.book_id = b.book_id
GROUP BY month
ORDER BY month;

-- 2. Самые продаваемые книги
SELECT
    b.title,
    b.genre,
    SUM(oi.quantity) AS sold_copies,
    ROUND(SUM(oi.quantity * b.price), 2) AS revenue
FROM order_items AS oi
JOIN books AS b ON oi.book_id = b.book_id
GROUP BY b.book_id, b.title, b.genre
ORDER BY sold_copies DESC, revenue DESC;

-- 3. Средний чек по клиентам
WITH order_totals AS (
    SELECT
        o.order_id,
        o.customer_id,
        SUM(oi.quantity * b.price) AS order_total
    FROM orders AS o
    JOIN order_items AS oi ON o.order_id = oi.order_id
    JOIN books AS b ON oi.book_id = b.book_id
    GROUP BY o.order_id, o.customer_id
)
SELECT
    c.customer_name,
    c.city,
    COUNT(ot.order_id) AS orders_count,
    ROUND(AVG(ot.order_total), 2) AS avg_order_value,
    ROUND(SUM(ot.order_total), 2) AS total_spent
FROM order_totals AS ot
JOIN customers AS c ON ot.customer_id = c.customer_id
GROUP BY c.customer_id, c.customer_name, c.city
ORDER BY total_spent DESC;

-- 4. Клиенты с повторными заказами
SELECT
    c.customer_name,
    COUNT(o.order_id) AS orders_count
FROM customers AS c
JOIN orders AS o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.customer_name
HAVING COUNT(o.order_id) > 1
ORDER BY orders_count DESC;

-- 5. Доля выручки по жанрам
WITH genre_revenue AS (
    SELECT
        b.genre,
        SUM(oi.quantity * b.price) AS revenue
    FROM order_items AS oi
    JOIN books AS b ON oi.book_id = b.book_id
    GROUP BY b.genre
), total_revenue AS (
    SELECT SUM(revenue) AS revenue FROM genre_revenue
)
SELECT
    gr.genre,
    ROUND(gr.revenue, 2) AS revenue,
    ROUND(gr.revenue * 100.0 / tr.revenue, 2) AS revenue_share_percent
FROM genre_revenue AS gr
CROSS JOIN total_revenue AS tr
ORDER BY revenue DESC;
