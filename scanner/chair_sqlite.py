import sqlite3 as sql
import pandas as pd


def sqlfstr(s):
    """Returns the string <s> as string format used for SQL parameter input.

    s: str
    returns: str
    """
    return s.replace('"', '""')


def open_conn(db_name="chairs.db"):
    """
    Opens connection to the database <db_name>. Returns a cursor object and
    connection object so that interactions with the database can occur.

    db_name: str
    returns: (sqlite3.Cursor, sqlite3.Connection)
    """
    conn = sql.connect(db_name)
    c = conn.cursor()
    return c, conn


def close_conn(db_conn):
    """
    Closes the connection to the database with cursor and connection objects
    db_conn

    db_conn: (sqlite3.Cursor, sqlite3.Connection)
    returns: None
    """
    c, conn = db_conn
    conn.close()


def init_db(db="chairs.db", table_name="chairs"):
    """
    Initializes database with name <db> and table <table_name>.

    db: str
    table_name: str
    returns: None
    """
    c, conn = open_conn(db_name=db)
    c.execute("""CREATE TABLE {table}(
        id integer,
        date text,
        prob real,
        price real,
        filename text
        )""".format(table=sqlfstr(table_name)))
    conn.commit()
    conn.close()


def insert(db_conn, item_dict, item_names, table="chairs"):
    """
    Inserts <item_dict> into the <table> corresponding to the <db_conn>
    database. <item_names> are the column names of <table>.

    db_conn: (sqlite3.Cursor, sqlite3.Connection)
    item_dict: dict whose keys match <item_names>
    item_names: str in format "(:item1, :item2, ..., item:n)"
    returns: None
    """
    c, conn = db_conn
    with conn:
        c.execute(
            "INSERT INTO {table} VALUES {item_names}"\
            .format(table=sqlfstr(table), item_names=sqlfstr(item_names)), item_dict
            )


def is_in_db(db_conn, item, var, table="chairs"):
    """
    Returns True if observation <item> belonging to variable <var> is in the
    database with (cursor, connection) <db_conn> and table <table>, returns
    False otherwise.

    db_conn: (sqlite3.Cursor, sqlite3.Connection)
    item: dtype(var)
    var: str
    returns: bool
    """
    c, _ = db_conn
    c.execute(
        "SELECT * FROM {} WHERE :var = :item".format(sqlfstr(table)),
        {"var": var, "item": item}
        )
    result = c.fetchone()
    return result is not None


def table_to_df(col_names, table="chairs"):
    """
    Given the column names <col_names> associated to the database table
    <table>, returns a pandas DataFrame of the table.

    col_names: list(str)
    table: str
    returns: pandas.DataFrame
    """
    c, conn = open_conn()
    with conn:
        data = c.execute(" SELECT * FROM {table}".format(table=sqlfstr(table)))  # retrieve all data
        data = pd.DataFrame(data.fetchall(), columns=col_names)
    return data
