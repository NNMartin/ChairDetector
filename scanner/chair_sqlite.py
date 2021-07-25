import sqlite3 as sql
from pandas import DataFrame


def sqlfstr(s: str):
    """
    Returns the string <s> as string format used for SQL parameter input.

    :param s: String to reformat.
    :return: str
    """
    return s.replace('"', '""')


def open_conn(db_name="chairs.db"):
    """
    Opens connection to the database <db_name>. Returns a cursor object and
    connection object so that interactions with the database can occur.

    :param db_name: Name of database.
    :return: tuple[sqlite3.Cursor, sqlite3.Connection]
    """
    conn = sql.connect(db_name)
    c = conn.cursor()
    return c, conn


def close_conn(db_conn: tuple[sql.Cursor, sql.Connection]):
    """
    Closes the connection to the database with cursor and connection objects
    <db_conn>.

    :param db_conn: Cursor and connection to database.
    :return: None
    """
    c, conn = db_conn
    conn.close()


def init_db(db="chairs.db", table_name="chairs"):
    """
    Initializes database with name <db> and table <table_name>.

    :param db: Name of database.
    :param table_name: Name of table in database.
    :return: None
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


def insert(db_conn: tuple[sql.Cursor, sql.Connection], item_dict: dict,
           item_names: str, table="chairs"):
    """
    Inserts <item_dict> into the <table> corresponding to the <db_conn>
    database. <item_names> are the column names of <table>.

    :param db_conn: Cursor and connection to database.
    :param item_dict: Dictionary whose keys match <item_names>.
    :param item_names: String in format "(:item1, :item2, ..., item:n)"
    :param table: Name of table in database
    :return: None
    """
    c, conn = db_conn
    with conn:
        c.execute(
            "INSERT INTO {table} VALUES {item_names}"\
            .format(table=sqlfstr(table), item_names=sqlfstr(item_names)),
            item_dict
            )


def is_in_db(db_conn: tuple[sql.Cursor, sql.Connection], item, var: str,
             table="chairs"):
    """
    Returns True if observation <item> belonging to variable <var> is in the
    database with (cursor, connection) <db_conn> and table <table>, returns
    False otherwise.

    :param db_conn: Cursor and connection to database.
    :param item: Item to check if in database.
    :param var: Variable that <item> corresponds to.
    :param table: Name of table in database.
    :return: bool
    """
    c, _ = db_conn
    c.execute(
        "SELECT {} FROM {} WHERE {}=?".format(
            sqlfstr(var), sqlfstr(table), sqlfstr(var)
            ),
        (item,)
        )
    result = c.fetchone()
    return result is not None


def table_to_df(col_names: list[str], table="chairs"):
    """
    Given the column names <col_names> associated to the database table
    <table>, returns a pandas DataFrame of the table.

    :param col_names: Names of columns in <table>
    :param table: Name of database table.
    :return: DataFrame
    """
    c, conn = open_conn()
    with conn:
        data = c.execute(" SELECT * FROM {table}".format(table=sqlfstr(table)))
        data = DataFrame(data.fetchall(), columns=col_names)
    return data
