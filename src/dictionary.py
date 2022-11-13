import psycopg2
import config as cfg


def connect() -> psycopg2.extensions.cursor:
    try:
        conn = psycopg2.connect(host=cfg.postgre["host"], port=cfg.postgre["port"],
                            database=cfg.postgre["default_database"], user=cfg.postgre["user"],
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
        conn = psycopg2.connect(host=cfg.postgre["host"], port=cfg.postgre["port"],
                            database=cfg.postgre["database"], user=cfg.postgre["user"],
                            password=cfg.postgre["password"])
        conn.autocommit = True
        with conn.cursor() as cur:
            cfg.logger.info("проверка существования таблицы")
            cur.execute(f"select 1 from information_schema.tables where table_name='{cfg.postgre['datatable']}'")
            is_exists = cur.fetchone()
            if not is_exists:
                cfg.logger.info("таблица ещё не существует, создаю...")
                cur.execute(f"CREATE TABLE {cfg.postgre['datatable']} (word varchar, translate varchar);")
            return cur
    except psycopg2.Error as e:
        cfg.logger.info(f"ошибка обращения к таблице: {e}")
        return None
    finally:
        if conn:
            conn.close()


def add_row() -> int:
    cur = connect()

