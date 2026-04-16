CREATE TABLE Roles (
    role_id         SERIAL      PRIMARY KEY,
    nombre          VARCHAR(64) NOT NULL

);

CREATE TABLE Users (
    user_id         SERIAL      PRIMARY KEY,
    nombre          VARCHAR(64) NOT NULL,
    role_id         INT         NOT NULL,

    CONSTRAINT FK_Users_Roles FOREIGN KEY (role_id) REFERENCES Roles(role_id)
);

CREATE TABLE Restaurant (
    restaurant_id   SERIAL      PRIMARY KEY,
    nombre          VARCHAR(64)  NOT NULL,
    admin_id        INT          NOT NULL,
    estado          INT          NOT NULL,

    CONSTRAINT FK_Restaurant_Users FOREIGN KEY (admin_id) REFERENCES Users(user_id)
);

CREATE TABLE Menu (
    menu_id             SERIAL          PRIMARY KEY,
    dish_name           VARCHAR(64)     NOT NULL,
    price               NUMERIC(10,2)   NOT NULL,
    restaurant_id       INT             NOT NULL,

    CONSTRAINT FK_Menu_Restaurant FOREIGN KEY(restaurant_id) REFERENCES Restaurant(restaurant_id),
    CONSTRAINT unique_dish_per_restaurant UNIQUE (restaurant_id, dish_name)
);


CREATE TABLE Tables(
    table_id            SERIAL      PRIMARY KEY,
    table_number        INT         NOT NULL,
    estado              INT         NOT NULL,
    restaurant_id       INT         NOT NULL,

    CONSTRAINT FK_Tables_Restaurant FOREIGN KEY (restaurant_id) REFERENCES Restaurant(restaurant_id),
    CONSTRAINT unique_table_per_restaurant UNIQUE (restaurant_id, table_number)
);


CREATE TABLE Orders (
    orders_id       SERIAL      PRIMARY KEY,
    table_id        INT         NULL,
    client_id       INT         NOT NULL,
    orders_type     VARCHAR(64) NOT NULL,
    restaurant_id   INT         NOT NULL,

    CONSTRAINT FK_Orders_Restaurant FOREIGN KEY (restaurant_id) REFERENCES Restaurant(restaurant_id),
    CONSTRAINT FK_Orders_Table FOREIGN KEY (table_id) REFERENCES Tables(table_id),
    CONSTRAINT FK_Orders_Users FOREIGN KEY (client_id) REFERENCES Users(user_id)
);

CREATE TABLE Orders_Items (
    orders_item_id  SERIAL        PRIMARY KEY,
    orders_id       INT           NOT NULL,
    menu_id         INT           NOT NULL,
    quantity        INT           NOT NULL,
    price           NUMERIC(10,2) NOT NULL,

    CONSTRAINT FK_Orders_Items_Orders FOREIGN KEY (orders_id) REFERENCES Orders(orders_id),
    CONSTRAINT FK_Orders_Items_Menu FOREIGN KEY (menu_id) REFERENCES Menu(menu_id)
);

CREATE TABLE Reservation (
    reservation_id  SERIAL      PRIMARY KEY,
    table_id        INT         NOT NULL,
    client_id       INT         NOT NULL,
    fecha           TIMESTAMP   NOT NULL,
    estado          INT         NOT NULL,

    CONSTRAINT FK_Reservation_Table FOREIGN KEY (table_id) REFERENCES Tables(table_id),
    CONSTRAINT FK_Reservation_Users FOREIGN KEY (client_id) REFERENCES Users(user_id)
);

