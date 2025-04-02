# Simple Order

## Description:
This is a simple order management system built with Flask and SQLAlchemy. It allows users to register, log in, and upload Excel files containing order data. The system processes the data and stores it in a database, which can then be viewed on the main page.

## Features:
- User registration and login
- Excel file upload for order data
- Data processing and storage in a database
- Display of processed data on the main page

## Installation:

### Prerequisites:
- Python 3.12
- Flask
- SQLAlchemy
- Pandas
- Openpyxl

### set up domestic sources:
```
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
```

### Installation Steps:
1. Clone the repository to your local machine.
2. Open a terminal and navigate to the cloned repository directory.
3. Create a virtual environment:
    ```python -m venv .venv```
4. Activate the virtual environment:
    ```.\.venv\Scripts\Activate.ps1```
5. Upgrade the pip (if you need):
    ```python.exe -m pip install --upgrade pip```
6. Install the required packages:
    ```pip install -r .\requirements.txt```
7. Create a database:
    ```python app.py db create```
8. Run the application:
    ```python app.py```


## Running the Application:
1. Make sure you have installed all requirements: pip install -r requirements.txt
2. Navigate to the simple_order directory in your terminal.
3. Activate the virtual environment:
   ```.\.venv\Scripts\Activate.ps1```
5. Run the Flask app:
   ```python app.py```

## Usage:
Open your web browser and go to http://127.0.0.1:5000 (or the address shown in the terminal).

You should see the login page (or register page if you navigate there). The first time you run it, a default user admin with password password will be created (you should change this immediately via the profile page).

Register or log in.

Go to the "upload" page to upload your Excel file.

The main page will display the processed data from the database.

Sample Excel File (data.xlsx):

Make sure your Excel file has headers matching the expected names (or adjust expected_columns in app.py).

供应商名称	客户名称	金额	发放时间	电话
供应商A	刘中强	63.41	2024-08-06 10:12:07	18312347159
供应商B	刘影丽	29.38	2024-08-06 10:12:07	18912344926
供应商C	吕晓辉	28.87	2024/08/06 10:12:07	15112349599

## Common Use
```
cd simple_order
.\.venv\Scripts\Activate.ps1
python app.py
```
