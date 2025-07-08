-- 1. 用户表触发器
CREATE OR REPLACE TRIGGER trg_users_id
BEFORE INSERT ON users
FOR EACH ROW
BEGIN
    IF :NEW.user_id IS NULL THEN
        SELECT seq_users_id.NEXTVAL INTO :NEW.user_id FROM dual;
    END IF;
END;
/

-- 2. 用户地址表触发器
CREATE OR REPLACE TRIGGER trg_addresses_id
BEFORE INSERT ON user_addresses
FOR EACH ROW
BEGIN
    IF :NEW.address_id IS NULL THEN
        SELECT seq_addresses_id.NEXTVAL INTO :NEW.address_id FROM dual;
    END IF;
END;
/

-- 3. 商品分类表触发器
CREATE OR REPLACE TRIGGER trg_categories_id
BEFORE INSERT ON product_categories
FOR EACH ROW
BEGIN
    IF :NEW.category_id IS NULL THEN
        SELECT seq_categories_id.NEXTVAL INTO :NEW.category_id FROM dual;
    END IF;
END;
/

-- 4. 商品表触发器
CREATE OR REPLACE TRIGGER trg_products_id
BEFORE INSERT ON products
FOR EACH ROW
BEGIN
    IF :NEW.product_id IS NULL THEN
        SELECT seq_products_id.NEXTVAL INTO :NEW.product_id FROM dual;
    END IF;
END;
/

-- 5. 商品图片表触发器
CREATE OR REPLACE TRIGGER trg_images_id
BEFORE INSERT ON product_images
FOR EACH ROW
BEGIN
    IF :NEW.image_id IS NULL THEN
        SELECT seq_images_id.NEXTVAL INTO :NEW.image_id FROM dual;
    END IF;
END;
/

-- 6. 购物车表触发器
CREATE OR REPLACE TRIGGER trg_cart_id
BEFORE INSERT ON shopping_cart
FOR EACH ROW
BEGIN
    IF :NEW.cart_id IS NULL THEN
        SELECT seq_cart_id.NEXTVAL INTO :NEW.cart_id FROM dual;
    END IF;
END;
/

-- 7. 订单表触发器
CREATE OR REPLACE TRIGGER trg_orders_id
BEFORE INSERT ON orders
FOR EACH ROW
BEGIN
    IF :NEW.order_id IS NULL THEN
        SELECT seq_orders_id.NEXTVAL INTO :NEW.order_id FROM dual;
    END IF;
END;
/

-- 8. 订单明细表触发器
CREATE OR REPLACE TRIGGER trg_items_id
BEFORE INSERT ON order_items
FOR EACH ROW
BEGIN
    IF :NEW.item_id IS NULL THEN
        SELECT seq_items_id.NEXTVAL INTO :NEW.item_id FROM dual;
    END IF;
END;
/

-- 9. 支付信息表触发器
CREATE OR REPLACE TRIGGER trg_payment_id
BEFORE INSERT ON payment_info
FOR EACH ROW
BEGIN
    IF :NEW.payment_id IS NULL THEN
        SELECT seq_payment_id.NEXTVAL INTO :NEW.payment_id FROM dual;
    END IF;
END;
/

-- 10. 评价表触发器
CREATE OR REPLACE TRIGGER trg_reviews_id
BEFORE INSERT ON product_reviews
FOR EACH ROW
BEGIN
    IF :NEW.review_id IS NULL THEN
        SELECT seq_reviews_id.NEXTVAL INTO :NEW.review_id FROM dual;
    END IF;
END;
/