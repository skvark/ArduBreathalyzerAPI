import os
import binascii
import psycopg2
import urlparse
import datetime
import time

# init Heroku postgresql
urlparse.uses_netloc.append("postgres")
url = urlparse.urlparse(os.environ["HEROKU_POSTGRESQL_AQUA_URL"])

conn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)

def create_tables():
    """ Creates tables when the app is started for the first time """

    cur = conn.cursor()
    cur.execute('\
                CREATE TABLE IF NOT EXISTS users (\
                id SERIAL UNIQUE,\
                name TEXT NOT NULL,\
                authtoken TEXT NOT NULL,\
                twitter_access_token_key TEXT,\
                twitter_access_token_secret TEXT,\
                facebook_access_token TEXT,\
                foursquare_access_token TEXT,\
                created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW());\
                ')

    cur.execute('\
                CREATE TABLE IF NOT EXISTS services (\
                id SERIAL UNIQUE,\
                service TEXT NOT NULL,\
                consumer_token_key TEXT NOT NULL,\
                consumer_token_secret TEXT NOT NULL,\
                created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW());\
                ')

    cur.execute('\
                CREATE TABLE IF NOT EXISTS bacdata (\
                id SERIAL UNIQUE NOT NULL,\
                user_id INTEGER REFERENCES users(id),\
                bac FLOAT NOT NULL,\
                latitude FLOAT,\
                longitude FLOAT,\
                service TEXT,\
                timestamp TIMESTAMP NOT NULL DEFAULT NOW(),\
                date DATE NOT NULL,\
                created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW());\
                ')

    conn.commit()

    cur.close()

# insert functions
def insert_service_data(service, key, secret):
    """ Inserts service data to the database """

    cur = conn.cursor()
    cur.execute("""INSERT INTO services (service, consumer_token_key, consumer_token_secret)
                       VALUES (%s, %s, %s);""", (service, key, secret))
    conn.commit()
    cur.close()


def update_user(authtoken, tw_key='', tw_secret='', fb_token='', fq_token=''):
    """ Updates user service tokens """

    cur = conn.cursor()

    if tw_key != '':
        SQL = """UPDATE users SET (twitter_access_token_key,
                                   twitter_access_token_secret) = (%s, %s) WHERE authtoken=%s;"""
        data = (tw_key, tw_secret, authtoken)

    elif fb_token != '':
        SQL = """UPDATE users SET (facebook_access_token) = (%s) WHERE authtoken=%s;"""
        data = (fb_token, authtoken)

    elif fq_token != '':
        SQL = """UPDATE users SET (foursquare_access_token) = (%s) WHERE authtoken=%s;"""
        data = (fq_token, authtoken)

    else:
        SQL = ''

    cur.execute(SQL, data)
    conn.commit()
    cur.close()

def add_user(name):
    """ Adds user and returns authtoken"""

    authtoken = binascii.b2a_hex(os.urandom(15))
    cur = conn.cursor()
    cur.execute("""INSERT INTO users (name,
                                     authtoken,
                                     twitter_access_token_key,
                                     twitter_access_token_secret,
                                     facebook_access_token,
                                     foursquare_access_token)
                    VALUES (%s, %s, %s, %s, %s, %s);""",
                    (name, authtoken, None, None, None, None))
    conn.commit()
    cur.close()
    return authtoken

def insert_bac_data(user_id, bac, latitude=None, longitude=None, service=None):
    """ Inserts a bac entry for a user """

    cur = conn.cursor()

    date = datetime.datetime.now()

    try:
        bac_query = cur.mogrify("""INSERT INTO bacdata (id,
                                                        user_id,
                                                        bac, latitude,
                                                        longitude,
                                                        service,
                                                        timestamp,
                                                        date)
                                   VALUES (DEFAULT, %s, %s, %s, %s, %s, %s, %s);""",
                                   (user_id, bac, latitude, longitude, service, 'NOW()', date.date()))
        cur.execute(bac_query)
        conn.commit()
        cur.close()
        return True

    except:
        conn.rollback()
        return False

# fetch functions
def check_authtoken(authtoken):
    """ Checks given authtoken against the user table """

    cur = conn.cursor()
    cur.execute("SELECT authtoken FROM users WHERE authtoken=%s;", (authtoken,))
    token = cur.fetchone()[0]
    conn.commit()
    cur.close()

    if token == authtoken:
        return True
    return False

def get_user_id(username):
    """ Gets user id by name """

    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE name=%s;", (username,))
    user_id = cur.fetchone()[0]
    conn.commit()
    cur.close()

    return user_id

def get_user_data(authtoken):
    """ Gets user data """

    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE authtoken=%s;", (authtoken,))
    data = cur.fetchone()
    conn.commit()
    cur.close()

    return data

def get_service_tokens(service):
    """ Gets service tokens """

    cur = conn.cursor()
    cur.execute("SELECT consumer_token_key, consumer_token_secret\
                 FROM services WHERE service=%s LIMIT 1;", (service,))
    key, secret = cur.fetchone()
    conn.commit()
    cur.close()

    return key, secret

def get_user_bacs(user, year, week, day):
    """ The user data for the API (this function needs to enchanced) """

    user_data = {}
    user_data[user] = {}

    date = time.strptime('%s %s %s' % (year, week, day), '%Y %W %w')
    date = '%s-%s-%s' % (date[0], date[1], date[2])
    print date

    #SQL = """SELECT timestamp, bac, latitude, longitude
    #         FROM bacdata
    #         WHERE date = %s
    #         AND user_id = %s;"""

    SQL = """SELECT timestamp, bac, latitude, longitude, date
             FROM bacdata
             WHERE user_id = %s;"""

    user_id = get_user_id(user)
    data = (user_id)
    cur = conn.cursor()

    try:
        cur.execute(SQL, data)
        rows = cur.fetchall()
        conn.commit()
    except Exception as e:
        print e
        conn.rollback()
        return {}

    cur.close()

    for row in rows:
        data = {'bac': row[1], 'lat': row[2], 'lon': row[3]}
        user_data[user][row[0]] = data

    return user_data

def get_available_services():
    """ Gets services which are available (== added) """

    services = []
    cur = conn.cursor()

    try:
        cur.execute("SELECT service FROM services")
        rows = cur.fetchall()
        conn.commit()
    except:
        conn.rollback()

    cur.close()

    for row in rows:
        services.append(row[0])

    return services
