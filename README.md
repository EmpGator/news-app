# news-app
clone 
```
    git clone https://github.com/EmpGator/news-app.git
    cd news-app
```
then create virtual env with 
```
    python -m venv .\venv
    .\venv\Scripts\activate
```
To run you need to install requirements with
```
    pip install -r .\requirements.txt
```
Then you should create .env file with
```
    SECRET_KEY=...
    SESSION_COOKIE_NAME=...
```
then you can run with 
```
    python wsgi.py
```
