from hoaxy.sns.twitter.parsers import Parser
from hoaxy.database import ENGINE
from hoaxy.database import Session
from hoaxy.database.models import TwitterUserUnion
from hoaxy.database.models import TwitterNetworkEdge
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)


def init_tables(engine, drop_first=False):
    if drop_first is True:
        TwitterUserUnion.__table__.drop(engine, checkfirst=True)
        TwitterNetworkEdge.__table__.drop(engine, checkfirst=True)
    TwitterUserUnion.__table__.create(engine, checkfirst=True)
    TwitterNetworkEdge.__table__.create(engine, checkfirst=True)


def main_test(engine,
              session,
              min_id=None,
              max_id=10000,
              window_size=1000,
              drop_first=False):
    parser = Parser(session, platform_id=1, saved_tweet=True)
    # init tables
    init_tables(engine, drop_first)
    if min_id is None:
        q = """ SELECT tw.id
                FROM tweet AS tw
                JOIN  twitter_network_edge AS te ON te.tweet_raw_id=tw.raw_id
                ORDER BY te.id DESC LIMIT 1"""
        min_id = engine.execute(text(q)).scalar()
        if min_id is None:
            min_id = 0
    if max_id is None:
        q = """ SELECT MAX(id) FROM tweet"""
        max_id = engine.execute(text(q)).scalar()
        if max_id is None:
            max_id = 0
            logger.error('No data in tweet table!')
            return None
    w_open_left = 0
    w_close_right = window_size
    counter = 0
    while True:
        logger.info('Paring counter is %s ...', counter)
        q = """
            SELECT tw.json_data
            FROM tweet AS tw
            WHERE tw.id>:l AND tw.id<=:r
            ORDER BY tw.id
            """
        if w_close_right > max_id:
            w_close_right = max_id
        if w_open_left >= max_id:
            logger.info('Max tweet id reached, Done!')
            break
        for jd, in engine.execute(
                text(q).bindparams(l=w_open_left, r=w_close_right)):
            parser.parse(jd)
            counter += 1
        w_open_left = w_close_right
        w_close_right += window_size


if __name__ == '__main__':
    # setting sqlalchemy logging
    # logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    logger = logging.getLogger()
    logging.basicConfig(level='INFO')
    session = Session()
    main_test(ENGINE, session, window_size=1000, drop_first=True)