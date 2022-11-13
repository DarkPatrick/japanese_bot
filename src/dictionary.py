import psycopg2
import config as cfg
import pandas as pd


def connect() -> tuple[psycopg2.extensions.connection, psycopg2.extensions.cursor]:
    try:
        conn = psycopg2.connect(host=cfg.postgre["host"],
                                port=cfg.postgre["port"],
                                database=cfg.postgre["default_database"],
                                user=cfg.postgre["user"],
                                password=cfg.postgre["password"])
        conn.autocommit = True
        with conn.cursor() as cur:
            cfg.logger.info("проверка существования бд")
            cur.execute(f"select 1 from pg_catalog.pg_database WHERE datname = '{cfg.postgre['database']}'")
            is_exists = cur.fetchone()
            if not is_exists:
                cfg.logger.info("бд ещё не существует, создаю...")
                cur.execute(f"CREATE DATABASE {cfg.postgre['database']}")
    except psycopg2.Error as e:
        cfg.logger.info(f"ошибка первичного подключения: {e}")
        return None
    finally:
        if conn:
            conn.close()
    
    try:
        conn = psycopg2.connect(host=cfg.postgre["host"],
                                port=cfg.postgre["port"],
                                database=cfg.postgre["database"],
                                user=cfg.postgre["user"],
                                password=cfg.postgre["password"])
        conn.autocommit = True
        cur = conn.cursor()
        cfg.logger.info("проверка существования таблицы")
        cur.execute(f"select 1 from information_schema.tables where table_name='{cfg.postgre['datatable']}'")
        is_exists = cur.fetchone()
        if not is_exists:
            cfg.logger.info("таблица ещё не существует, создаю...")
            cur.execute(f"CREATE TABLE {cfg.postgre['datatable']} (word varchar, translate varchar);")
        return conn, cur
    except psycopg2.Error as e:
        cfg.logger.info(f"ошибка обращения к таблице: {e}")
        if conn:
            conn.close()
        return None



def add_row(word_dict: dict) -> None:
    conn, cur = connect()
    cur.execute(f"insert into {cfg.postgre['datatable']} values('{word_dict['word']}', '{word_dict['translation']}')")
    conn.close()

def get_datatable() -> pd.DataFrame:
     conn, cur = connect()
     cur.execute(f"select * from {cfg.postgre['datatable']}")
     df = pd.DataFrame(cur.fetchall(), columns=['word', 'translation'])
     conn.close()
     return df


if __name__ == "__main__":
    # add_row(dict(word="test1", translation="test2"))
    df = get_datatable()
    print(df)
