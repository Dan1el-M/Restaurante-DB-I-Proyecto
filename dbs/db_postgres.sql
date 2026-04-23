CREATE TABLE Roles (
    role_id         SERIAL      PRIMARY KEY,
    role_name       VARCHAR(64) NOT NULL

);

CREATE TABLE Users (
    user_id         SERIAL       PRIMARY KEY,
    user_name       VARCHAR(64)  NOT NULL,
    role_id         INT          NOT NULL,
    keycloak_id     VARCHAR(255) NOT NULL UNIQUE,

    CONSTRAINT FK_Users_Roles FOREIGN KEY (role_id) REFERENCES Roles(role_id)
);

CREATE TABLE Restaurants (
    restaurant_id     SERIAL       PRIMARY KEY,
    restaurant_name   VARCHAR(64)  NOT NULL,
    admin_id          INT          NOT NULL,
    restaurant_status INT          NOT NULL,

    CONSTRAINT FK_Restaurant_Users FOREIGN KEY (admin_id) REFERENCES Users(user_id)
);

CREATE TABLE Menus (
    menu_id             SERIAL          PRIMARY KEY,
    dish_name           VARCHAR(64)     NOT NULL,
    price               NUMERIC(10,2)   NOT NULL,
    restaurant_id       INT             NOT NULL,

    CONSTRAINT FK_Menus_Restaurants       FOREIGN KEY(restaurant_id) REFERENCES Restaurants(restaurant_id),
    CONSTRAINT unique_dish_per_restaurant UNIQUE (restaurant_id, dish_name)
);


CREATE TABLE Tables (
    table_id            SERIAL      PRIMARY KEY,
    table_number        INT         NOT NULL,
    table_status        INT         NOT NULL,
    restaurant_id       INT         NOT NULL,

    CONSTRAINT FK_Tables_Restaurants       FOREIGN KEY (restaurant_id) REFERENCES Restaurants(restaurant_id),
    CONSTRAINT unique_table_per_restaurant UNIQUE (restaurant_id, table_number)
);


CREATE TABLE Orders (
    order_id        SERIAL      PRIMARY KEY,
    table_id        INT         NULL,
    client_id       INT         NOT NULL,
    order_type      VARCHAR(64) NOT NULL,
    restaurant_id   INT         NOT NULL,

    CONSTRAINT FK_Orders_Restaurants FOREIGN KEY (restaurant_id) REFERENCES Restaurants(restaurant_id),
    CONSTRAINT FK_Orders_Table       FOREIGN KEY (table_id)      REFERENCES Tables(table_id),
    CONSTRAINT FK_Orders_Users       FOREIGN KEY (client_id)     REFERENCES Users(user_id)
);

CREATE TABLE Order_Items (
    order_item_id   SERIAL        PRIMARY KEY,
    order_id        INT           NOT NULL,
    menu_id         INT           NOT NULL,
    quantity        INT           NOT NULL,
    price           NUMERIC(10,2) NOT NULL,

    CONSTRAINT FK_Order_Items_Orders FOREIGN KEY (order_id) REFERENCES Orders(order_id),
    CONSTRAINT FK_Order_Items_Menus  FOREIGN KEY (menu_id)  REFERENCES Menus(menu_id)
);

CREATE TABLE Reservations (
    reservation_id     SERIAL      PRIMARY KEY,
    table_id           INT         NOT NULL,
    client_id          INT         NOT NULL,
    reservation_date   TIMESTAMP   NOT NULL,
    reservation_status INT         NOT NULL,

    CONSTRAINT FK_Reservations_Tables FOREIGN KEY (table_id)  REFERENCES Tables(table_id),
    CONSTRAINT FK_Reservations_Users  FOREIGN KEY (client_id) REFERENCES Users(user_id)
);

