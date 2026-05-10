DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS books;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    customer_name TEXT NOT NULL,
    city TEXT NOT NULL
);

CREATE TABLE books (
    book_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    genre TEXT NOT NULL,
    price REAL NOT NULL
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    order_date TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE order_items (
    order_id INTEGER NOT NULL,
    book_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (book_id) REFERENCES books(book_id)
);

INSERT INTO customers (customer_id, customer_name, city) VALUES
(1, 'Анна Соколова', 'Москва'),
(2, 'Илья Морозов', 'Казань'),
(3, 'Мария Волкова', 'Москва'),
(4, 'Артем Иванов', 'Санкт-Петербург'),
(5, 'Елена Орлова', 'Екатеринбург'),
(6, 'Денис Смирнов', 'Казань');

INSERT INTO books (book_id, title, genre, price) VALUES
(1, 'Python для начинающих', 'programming', 1100),
(2, 'SQL на практике', 'programming', 950),
(3, 'Статистика без паники', 'education', 780),
(4, 'Городские истории', 'fiction', 520),
(5, 'Маркетинг продукта', 'business', 890),
(6, 'Введение в аналитику', 'education', 840),
(7, 'Короткие рассказы', 'fiction', 430);

INSERT INTO orders (order_id, customer_id, order_date) VALUES
(101, 1, '2024-01-12'),
(102, 2, '2024-01-18'),
(103, 3, '2024-02-03'),
(104, 1, '2024-02-15'),
(105, 4, '2024-02-21'),
(106, 5, '2024-03-02'),
(107, 2, '2024-03-10'),
(108, 6, '2024-03-15'),
(109, 3, '2024-03-22'),
(110, 1, '2024-04-01');

INSERT INTO order_items (order_id, book_id, quantity) VALUES
(101, 1, 1),
(101, 3, 1),
(102, 4, 2),
(102, 7, 1),
(103, 2, 1),
(103, 6, 1),
(104, 5, 1),
(104, 3, 1),
(105, 1, 1),
(106, 6, 2),
(107, 2, 1),
(107, 4, 1),
(108, 7, 3),
(109, 5, 1),
(109, 6, 1),
(110, 2, 1),
(110, 3, 1);
