# simple_order

##Before:

python -m venv .venv

.\.venv\Scripts\Activate.ps1

python.exe -m pip install --upgrade pip

pip install -r .\requirements.txt

## Running the Application:
Make sure you have installed all requirements: pip install -r requirements.txt
Navigate to the simple_order_display directory in your terminal.
Run the Flask app: python app.py
Open your web browser and go to http://127.0.0.1:5000 (or the address shown in the terminal).

You should see the login page (or register page if you navigate there). The first time you run it, a default user admin with password password will be created (you should change this immediately via the profile page).

Register or log in.

Go to the "上传数据" page to upload your Excel file.

The main page will display the processed data from the database.

Sample Excel File (data.xlsx):

Make sure your Excel file has headers matching the expected names (or adjust expected_columns in app.py).

供应商名称	客户名称	金额	发放时间	电话
供应商A	刘中强	63.41	2024-08-06 10:12:07	18312347159
供应商B	刘影丽	29.38	2024-08-06 10:12:07	18912344926
供应商C	吕晓辉	28.87	2024/08/06 10:12:07	15112349599
周丽玲	48.97	2024-8-6 10:12	15912341105
供应商E	康晓红	85.02	2024-08-06	15612343188
供应商F	张晓荣	12.24		13812347665
