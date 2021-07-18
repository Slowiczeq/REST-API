# Computers manufacturers REST API

REST API for computer dealer.

## SETUP

- Clone repository
- Create database
- Rename .env.example to '.env' and set your values

```buildoutcfg
# SQLALCHEMY_DATABASE_URI MySQL template
SQLALCHEMY_DATABASE_URI=mysql+pymysql://<db_user>:<db_password>@<db_host>/<db_name>?charset=utf8mb4
```
- Create a virtual environment
```buildoutcfg
python -m venv venv
```

- Install packages from requirements.txt
```buildoutcfg
pip install -r requirements.txt
```

- Migrate database
```buildoutcfg
flask db upgrade
```

- Run command
```buildoutcfg
flask run
```

**NOTE**

Import / delete example data from Computers_app/samples:
```buildoutcfg
# import
flask db-manage add-data

# remove
flask db-manage remove-data
```

## Technologies/Tools

- Python 3.9
- Flask 2.0.1
- SQLAlchemy 1.4.21
- Alembic 1.6.5
- MySQL
- Postman







