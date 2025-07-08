-- 1. 用户表
CREATE TABLE users (
    user_id NUMBER PRIMARY KEY,
    username VARCHAR2(50) NOT NULL,
    password VARCHAR2(100) NOT NULL,
    email VARCHAR2(100) UNIQUE NOT NULL,
    phone VARCHAR2(20),
    register_date DATE DEFAULT SYSDATE,
    status NUMBER(1) DEFAULT 1
);

-- 2. 用户地址表
CREATE TABLE user_addresses (
    address_id NUMBER PRIMARY KEY,
    user_id NUMBER NOT NULL,
    receiver_name VARCHAR2(50) NOT NULL,
    receiver_phone VARCHAR2(20) NOT NULL,
    province VARCHAR2(50) NOT NULL,
    city VARCHAR2(50) NOT NULL,
    district VARCHAR2(50) NOT NULL,
    detail_address VARCHAR2(200) NOT NULL,
    is_default NUMBER(1) DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 3. 商品分类表
CREATE TABLE product_categories (
    category_id NUMBER PRIMARY KEY,
    category_name VARCHAR2(50) NOT NULL,
    parent_id NUMBER,
    category_level NUMBER(1) NOT NULL,
    sort_order NUMBER DEFAULT 0,
    FOREIGN KEY (parent_id) REFERENCES product_categories(category_id)
);

-- 4. 商品表
CREATE TABLE products (
    product_id NUMBER PRIMARY KEY,
    category_id NUMBER NOT NULL,
    product_name VARCHAR2(100) NOT NULL,
    product_desc VARCHAR2(500),
    price NUMBER(10,2) NOT NULL,
    stock NUMBER NOT NULL,
    sales NUMBER DEFAULT 0,
    create_time DATE DEFAULT SYSDATE,
    update_time DATE DEFAULT SYSDATE,
    status NUMBER(1) DEFAULT 1,
    FOREIGN KEY (category_id) REFERENCES product_categories(category_id)
);

-- 5. 商品图片表
CREATE TABLE product_images (
    image_id NUMBER PRIMARY KEY,
    product_id NUMBER NOT NULL,
    image_url VARCHAR2(200) NOT NULL,
    sort_order NUMBER DEFAULT 0,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- 6. 购物车表
CREATE TABLE shopping_cart (
    cart_id NUMBER PRIMARY KEY,
    user_id NUMBER NOT NULL,
    product_id NUMBER NOT NULL,
    quantity NUMBER NOT NULL,
    selected NUMBER(1) DEFAULT 1,
    create_time DATE DEFAULT SYSDATE,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- 7. 订单表
CREATE TABLE orders (
    order_id NUMBER PRIMARY KEY,
    order_no VARCHAR2(50) UNIQUE NOT NULL,
    user_id NUMBER NOT NULL,
    address_id NUMBER NOT NULL,
    total_amount NUMBER(10,2) NOT NULL,
    payment_amount NUMBER(10,2) NOT NULL,
    freight_amount NUMBER(10,2) DEFAULT 0,
    order_status NUMBER(1) DEFAULT 0,
    payment_time DATE,
    delivery_time DATE,
    receive_time DATE,
    create_time DATE DEFAULT SYSDATE,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (address_id) REFERENCES user_addresses(address_id)
);

-- 8. 订单明细表
CREATE TABLE order_items (
    item_id NUMBER PRIMARY KEY,
    order_id NUMBER NOT NULL,
    product_id NUMBER NOT NULL,
    product_name VARCHAR2(100) NOT NULL,
    product_image VARCHAR2(200),
    price NUMBER(10,2) NOT NULL,
    quantity NUMBER NOT NULL,
    total_price NUMBER(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- 9. 支付信息表
CREATE TABLE payment_info (
    payment_id NUMBER PRIMARY KEY,
    order_id NUMBER NOT NULL,
    payment_type NUMBER(1) NOT NULL,
    trade_no VARCHAR2(100),
    payment_amount NUMBER(10,2) NOT NULL,
    payment_status NUMBER(1) DEFAULT 0,
    create_time DATE DEFAULT SYSDATE,
    callback_time DATE,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

-- 10. 评价表
CREATE TABLE product_reviews (
    review_id NUMBER PRIMARY KEY,
    user_id NUMBER NOT NULL,
    product_id NUMBER NOT NULL,
    order_id NUMBER NOT NULL,
    rating NUMBER(1) NOT NULL,
    content VARCHAR2(500),
    review_time DATE DEFAULT SYSDATE,
    is_anonymous NUMBER(1) DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);