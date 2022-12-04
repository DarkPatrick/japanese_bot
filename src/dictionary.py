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
            cur.execute(f"""
                        select 1
                        from pg_catalog.pg_database
                        where datname = '{cfg.postgre['database']}'""")
            is_exists = cur.fetchone()
            if not is_exists:
                cfg.logger.info("бд ещё не существует, создаю...")
                cur.execute(f"CREATE DATABASE {cfg.postgre['database']}")
    except psycopg2.Error as e:
        cfg.logger.info(f"ошибка первичного подключения: {e}")
        return (None, None)
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
        cur.execute(f"""
                    select 1
                    from information_schema.tables
                    where table_name='{cfg.postgre['datatable']}'""")
        is_exists = cur.fetchone()
        if not is_exists:
            cfg.logger.info("таблица ещё не существует, создаю...")
            cur.execute(f"""
                        create table {cfg.postgre['datatable']}
                        (word varchar, translate varchar, tries int, success_cnt int);""")
        return conn, cur
    except psycopg2.Error as e:
        cfg.logger.info(f"ошибка обращения к таблице: {e}")
        if conn:
            conn.close()
        return (None, None)


def get_info_by(**kwargs: dict) -> pd.DataFrame:
    conn, cur = connect()
    if conn is None:
        return None
    cur.execute(f"""
                select * 
                from {cfg.postgre['datatable']}
                where {kwargs['col_name']} = '{kwargs['word']}'""")
    df = pd.DataFrame(cur.fetchall(), columns=['word', 'translation', 'tries', 'success_cnt'])
    conn.close()
    return df


def add_row(word_dict: dict) -> int:
    conn, cur = connect()
    if conn is None:
        return None
    check_word = get_info_by(col_name='word', word=word_dict['word'])
    check_translation = get_info_by(col_name='translate', word=word_dict['translation'])
    if len(check_word.index) == 0 and len(check_word.index) == 0:
        cur.execute(f"""
                    insert into {cfg.postgre['datatable']} 
                    (word, translate, tries, success_cnt)
                    values('{word_dict['word']}', '{word_dict['translation']}', 0, 0)""")
    else:
        # log here that word already exists
        conn.close()
        return 1
    conn.close()
    return 0


def del_row(word: str) -> int:
    conn, cur = connect()
    if conn is None:
        return None

    cur.execute(f"""
                select count(*)
                from {cfg.postgre['datatable']}
                where word = '{word}' or translate = '{word}'""")
    df = pd.DataFrame(cur.fetchall(), columns=['word_cnt'])
    if df.word_cnt[0] == 0:
        conn.close()
        return 0
    
    cur.execute(f"""
                delete from {cfg.postgre['datatable']}
                where word = '{word}' or translate = '{word}'""")

    conn.close()
    return 1


def get_datatable() -> pd.DataFrame:
    conn, cur = connect()
    if conn is None:
        return None
    cur.execute(f"select * from {cfg.postgre['datatable']}")
    df = pd.DataFrame(cur.fetchall(), columns=['word', 'translation', 'tries', 'success_cnt'])
    conn.close()
    return df


def get_random_word(word_cnt: int=8) -> pd.DataFrame:
    conn, cur = connect()
    if conn is None:
        return None
    cur.execute(f"""
                select count(*) as exact_count
                from {cfg.postgre['datatable']}""")
    row_num = cur.fetchall()[0][0]
    cur.execute(f"""
                select * from {cfg.postgre['datatable']}
                order by random() 
                limit {row_num if row_num <= word_cnt else word_cnt}""")
    df = pd.DataFrame(cur.fetchall(), columns=['word', 'translation', 'tries', 'success_cnt'])
    conn.close()
    return df


def update_stats(word :str, succ: int) -> None:
    conn, cur = connect()
    if conn is None:
        return None

    cur.execute(f"""
                update {cfg.postgre['datatable']}
                set tries = tries + 1, success_cnt = success_cnt + {succ}
                where word = '{word}' or translate = '{word}'""")
    conn.close()


if __name__ == "__main__":
    df = get_datatable()
    print(df)
