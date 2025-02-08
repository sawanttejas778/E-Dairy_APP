create database dairy_db;
use dairy_db;

CREATE TABLE farmer_details (
    farmer_id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(255),
    account_no VARCHAR(20) NOT NULL,
    ifsc_code VARCHAR(20) NOT NULL,
    bank_name VARCHAR(100) NOT NULL,
    aadhar_no VARCHAR(12) NOT NULL,
    ufarmid VARCHAR(50) NOT NULL,
    mobile VARCHAR(15),
    village VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    PRIMARY KEY (farmer_id),
    KEY (email)
);

CREATE TABLE milk_collection (
    id INT NOT NULL AUTO_INCREMENT,
    farmer_id INT NOT NULL,
    snf FLOAT NOT NULL,
    fat FLOAT NOT NULL,
    milk FLOAT NOT NULL,
    animal_type VARCHAR(50) NOT NULL,
    total_rate FLOAT NOT NULL,
    collection_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    collection_time_of_day TINYINT(1) NOT NULL,
    rate FLOAT NOT NULL,
    email VARCHAR(255),
    PRIMARY KEY (id),
    KEY (farmer_id),
    FOREIGN KEY (farmer_id) REFERENCES farmer_details(farmer_id) ON DELETE CASCADE
);

CREATE TABLE user (
    First_name VARCHAR(50) NOT NULL,
    Last_name VARCHAR(50) NOT NULL,
    mobile BIGINT NOT NULL,
    email VARCHAR(200) NOT NULL,
    Password VARCHAR(255) NOT NULL,
    PRIMARY KEY (email)
);

CREATE TABLE transactions (
    transaction_id INT NOT NULL AUTO_INCREMENT,
    farmer_id INT NOT NULL,
    transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    transaction_type ENUM('Deposit', 'Withdraw') NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    notes TEXT,
    email VARCHAR(200) NOT NULL,
    PRIMARY KEY (transaction_id),
    KEY (farmer_id),
    FOREIGN KEY (farmer_id) REFERENCES farmer_details(farmer_id) ON DELETE CASCADE
);
