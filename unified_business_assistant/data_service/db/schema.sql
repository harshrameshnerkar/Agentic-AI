-- ==============================================================================
-- UNIFIED BUSINESS ASSISTANT - ROLE B: DATA SERVICE
-- Enterprise Relational Business Schema (SQLite & PostgreSQL Compatible)
-- 6 Interconnected Tables, Strict Foreign Keys, Check Constraints & Indexes
-- ==============================================================================

PRAGMA foreign_keys = ON;

-- 1. DEPARTMENTS
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS departments;

CREATE TABLE departments (
    department_id INTEGER PRIMARY KEY AUTOINCREMENT,
    department_name TEXT NOT NULL UNIQUE,
    code TEXT NOT NULL UNIQUE,
    budget REAL NOT NULL,
    location TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (DATE('now'))
);

-- 2. EMPLOYEES
CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    department_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    salary REAL NOT NULL,
    hire_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('Active', 'On Leave', 'Terminated')),
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

-- 3. CUSTOMERS
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL UNIQUE,
    contact_name TEXT NOT NULL,
    contact_email TEXT NOT NULL,
    industry TEXT NOT NULL,
    region TEXT NOT NULL,
    country TEXT NOT NULL,
    tier TEXT NOT NULL CHECK(tier IN ('Enterprise', 'Mid-Market', 'Startup')),
    created_at TEXT NOT NULL DEFAULT (DATE('now'))
);

-- 4. PRODUCTS
CREATE TABLE products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    unit_price REAL NOT NULL,
    cost_price REAL NOT NULL,
    stock_quantity INTEGER NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('Active', 'Discontinued'))
);

-- 5. ORDERS
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,
    order_date TEXT NOT NULL,
    order_status TEXT NOT NULL CHECK(order_status IN ('Completed', 'Processing', 'Cancelled', 'Refunded')),
    payment_status TEXT NOT NULL CHECK(payment_status IN ('Paid', 'Pending', 'Failed')),
    total_amount REAL NOT NULL DEFAULT 0.0,
    channel TEXT NOT NULL CHECK(channel IN ('Direct Sales', 'Online Portal', 'Partner Referral')),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

-- 6. ORDER ITEMS
CREATE TABLE order_items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    unit_price REAL NOT NULL,
    discount_pct REAL NOT NULL DEFAULT 0.0,
    line_total REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- INDEXES FOR PERFORMANCE & QUERY ACCELERATION
CREATE INDEX idx_employees_department ON employees(department_id);
CREATE INDEX idx_customers_region ON customers(region);
CREATE INDEX idx_customers_industry ON customers(industry);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_employee ON orders(employee_id);
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);
