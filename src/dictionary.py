import psycopg2
import pandas as pd

import config as cfg


def connect(chat_id: str
            ) -> tuple[
                psycopg2.extensions.connection, 
                psycopg2.extensions.cursor]:
    """
    connection to table. uses in every action

    Args:
        chat_id (str): user2bot id which used to access user assigned table

    Returns:
        tuple[psycopg2.extensions.connection, psycopg2.extensions.cursor]: 
        connection and cursor objects to use after connection
    """    """"""
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
                    where table_name='{cfg.postgre['datatable']}_{chat_id}'""")
        is_exists = cur.fetchone()
        if not is_exists:
            cfg.logger.info("таблица ещё не существует, создаю...")
            cur.execute(f"""
                        create table {cfg.postgre['datatable']}_{chat_id}
                        (word varchar, translate varchar, 
                        tries int, success_cnt int);""")
        return conn, cur

    except psycopg2.Error as e:
        cfg.logger.info(f"ошибка обращения к таблице: {e}")
        if conn:
            conn.close()
        return (None, None)


def get_info_by(chat_id: str, **kwargs: dict) -> pd.DataFrame:
    """
    get row by word or translate

    Args:
        chat_id (str): user2bot id which used to access user assigned table
        kwargs['word'] (str): word or transaltion
        kwargs['col_name'] (str): column name {'word', 'translate'}

    Returns:
        pd.DataFrame: found row as dataframe
    """    
    conn, cur = connect(chat_id)
    if conn is None:
        return None

    cfg.logger.info(f"""getting word {kwargs['word']} 
                    by column kwargs['col_name']""")
    cur.execute(f"""
                select * 
                from {cfg.postgre['datatable']}_{chat_id}
                where {kwargs['col_name']} = '{kwargs['word']}'""")
    df = pd.DataFrame(cur.fetchall(), columns=['word', 'translation', 
                                               'tries', 'success_cnt'])
    conn.close()
    return df


def add_row(word_dict: dict, chat_id: str) -> int:
    """
    add row in dictionary table

    Args:
        word_dict (dict): 'word' and 'translation' params
        chat_id (str): user2bot id which used to access user assigned table

    Returns:
        int: 1 if row is already exists, esle 0
    """    
    conn, cur = connect(chat_id)
    if conn is None:
        return None

    cfg.logger.info(f"adding new word to table")
    cfg.logger.info(f"""checking if word {word_dict['word']} or translations 
                    {word_dict['translation']} is already exists""")
    check_word = get_info_by(chat_id, col_name='word', word=word_dict['word'])
    check_translation = get_info_by(chat_id, col_name='translate', 
                                    word=word_dict['translation'])
    if len(check_word.index) == 0 and len(check_translation.index) == 0:
        cur.execute(f"""
                    insert into {cfg.postgre['datatable']}_{chat_id} 
                    (word, translate, tries, success_cnt)
                    values('{word_dict['word']}', 
                    '{word_dict['translation']}', 0, 0)""")
    else:
        cfg.logger.info(f"successfully added")
        conn.close()
        return 1
    cfg.logger.info(f"error: word is already exists")
    conn.close()
    return 0


def del_row(word: str, chat_id: str) -> int:
    """
    delete row by word or its translation

    Args:
        word (str): word or tralsation to search by
        chat_id (str): user2bot id which used to access user assigned table

    Returns:
        int: 0 if word is not found, else - 1
    """    
    conn, cur = connect(chat_id)
    if conn is None:
        return None

    cfg.logger.info(f"deleting row by {word}")
    cur.execute(f"""
                select count(*)
                from {cfg.postgre['datatable']}_{chat_id}
                where word = '{word}' or translate = '{word}'""")
    df = pd.DataFrame(cur.fetchall(), columns=['word_cnt'])
    if df.word_cnt[0] == 0:
        cfg.logger.info(f"word {word} not found")
        conn.close()
        return 0
    
    cur.execute(f"""
                delete from {cfg.postgre['datatable']}_{chat_id}
                where word = '{word}' or translate = '{word}'""")
    cfg.logger.info(f"word {word} successfully deleted")

    conn.close()
    return 1


def get_datatable(chat_id: str) -> pd.DataFrame:
    """
    return full dictionary

    Args:
        chat_id (str): user2bot id which used to access user assigned table

    Returns:
        pd.DataFrame: dictionary table as pandas data frame
    """    
    conn, cur = connect(chat_id)
    if conn is None:
        return None

    cfg.logger.info(f"getting table")
    cur.execute(f"select * from {cfg.postgre['datatable']}_{chat_id}")
    df = pd.DataFrame(cur.fetchall(), columns=['word', 'translation', 
                                               'tries', 'success_cnt'])
    conn.close()
    return df


def get_random_word(chat_id: str, word_cnt: int=8) -> pd.DataFrame:
    """
    getting random words from dictionary

    Args:
        chat_id (str): user2bot id which used to access user assigned table
        word_cnt (int, optional): number of words to sample. Defaults to 8.

    Returns:
        pd.DataFrame: sampled rows as pandas data frame
    """    
    conn, cur = connect(chat_id)
    if conn is None:
        return None

    cfg.logger.info(f"couting rows in table")
    cur.execute(f"""
                select count(*) as exact_count
                from {cfg.postgre['datatable']}_{chat_id}""")
    row_num = cur.fetchall()[0][0]

    cfg.logger.info(f"getting random rows from table")
    cur.execute(f"""
                select * from {cfg.postgre['datatable']}_{chat_id}
                order by random() 
                limit {row_num if row_num <= word_cnt else word_cnt}""")
    df = pd.DataFrame(cur.fetchall(), columns=['word', 'translation', 
                                               'tries', 'success_cnt'])
    conn.close()
    return df


def update_stats(word :str, succ: int, chat_id: str) -> None:
    """
    update number of tries / successes in word's quiz

    Args:
        word (str): word from quiz
        succ (int): 1 - if user win 0 elsewhere
        chat_id (str): user2bot id which used to access user assigned table

    Returns:
        None
    """    
    conn, cur = connect(chat_id)
    if conn is None:
        return None

    cur.execute(f"""
                update {cfg.postgre['datatable']}_{chat_id}
                set tries = tries + 1, success_cnt = success_cnt + {succ}
                where word = '{word}' or translate = '{word}'""")
    conn.close()


if __name__ == "__main__":
    # view current table
    df = get_datatable()
    print(df)
