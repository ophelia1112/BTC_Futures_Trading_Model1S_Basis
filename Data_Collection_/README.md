## Data Collection of All❤️‍🔥 (Sample Scripts)  

### 1.Note🔥:   

#### The scripts uploaded in this repository are partial components of a larger project and are provided **❗️for learning and reference purposes only❗️**.   

#### These scripts require private data sources, configuration files, and core models to run properly.  

#### The core trading models and strategy logic are private and not included in this repository.  

### 2.Overview of Uploaded Files👀:    

### (1).Data_collection_ documents:  

#### 1M_Realtime_BTC_Futures_data.py: Monitors Binance BTCUSDT futures 1-minute K-line data and stores it in a database in real time. 

#### 1M_Realtime_BTC_Futures_data.py: Collect Binance BTCUSDT futures 1-minute K-line of specific time period.

### (2).Data_check_ documents:  

#### return_newest_kline_data(realtime).py: Returns the latest K-line data via real-time API.    

#### original_data_to_check(realtime).py: Retrieves and prints one complete historical K-line data for verification.  

#### RealtimedataCheck_specificdata.py: Fetches specific K-line data by timestamp for debugging and validation.    

### (3).PostgreSQL_Tables:  

#### realtime_btc_futures_1mdata.sql: PostgreSQL table for BTC realtime 1m klines data collection.  

#### historical_btc_futures_1mdata.sql: PostgreSQL table for BTC historical 1m klines data collection.


### 3.Environment Requirements👾: 

#### Python 3.10 or higher  

#### Install dependencies listed in `requirements.txt`   

#### Proper PostgreSQL database configuration (local or remote)

### 4.Security Notice⚠️:  

#### All sensitive data such as API keys and database credentials are **not included** in this repository.  

#### This project is for educational purposes only and **‼️does not constitute financial or investment advice‼️**.
