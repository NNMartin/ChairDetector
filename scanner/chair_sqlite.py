import sqlite3 as sql


def sqlfstr(s):
    return s.replace('"', '""')


def open_conn(db_name = "chairs.db"):
    """
    Opens connection to the expenses database. Returns a cursor object and
    connection object so that interactions with the database can occur.
    """
    conn = sql.connect(db_name)
    c = conn.cursor()
    return c, conn


def init_db(db="chairs.db", table_name="chairs"):
    """
    Include Try, Except to catch already created db errors.
    """
    c, conn = open_conn(db_name = db)
    c.execute("""CREATE TABLE {table}(
        id integer,
        date text,
        prob real,
        price real,
        filename text
        )""".format(table = sqlfstr(table_name)))
    conn.commit()
    conn.close()


def insert(db_conn, item_dict, item_names, table="chairs"):
    """
    Inserts the Week object, <data>, into the expenses database. <data> is a
    single week's worth of data regarding expenses.
    """
    c, conn = db_conn
    with conn:
        c.execute(
            "INSERT INTO {table} VALUES {item_names}"\
            .format(table = sqlfstr(table), item_names = sqlfstr(item_names)), item_dict
            )

def close_db(db_conn):
    c, conn = db_conn
    conn.close()


def is_in_db(db_conn, item, var, db = "chairs"):
    c, _ = db_conn
    c.execute(
        "SELECT * FROM {} WHERE :var = :item".format(sqlfstr(db)),
        {"var": var, "item": item}
        )
    result = c.fetchone()
    return result is not None
