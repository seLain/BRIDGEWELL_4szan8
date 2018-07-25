import time
import sqlite3
import random

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String,  create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql import bindparam

Base = declarative_base()
DBSession = scoped_session(sessionmaker())
engine = None
UPDATE_PORTION = 0.1 # portion of update actions. 
                     # for example, update_portion = 0.1
                     # means there will be around 10% update 
                     # actions and 90% insert actions

class Customer(Base):
    __tablename__ = "customer"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))


def init_sqlalchemy(dbname='sqlite:///sqlalchemy.db'):
    global engine
    engine = create_engine(dbname, echo=False)
    DBSession.remove()
    DBSession.configure(bind=engine, autoflush=True, expire_on_commit=False)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

def update_or_create(n, **kwargs):
    '''
    To get an added customer object or create a new Customer object
    @param: int n: the n-th test run in loop
    @param: **kwargs: key-value params for creating Customer object
    '''
    created = True
    if n != 0 and random.random() <= UPDATE_PORTION:
        query = DBSession.query(Customer)
        row_count = int(query.count())
        customer = query.offset(int(row_count*random.random())).first()
        customer.name = 'UPDATED ' + str(n)
        created = False
    else:
        customer = Customer(**kwargs)
        customer.name = 'NAME ' + str(n)

    return customer, created

def test_sqlalchemy_orm(n=100000):
    init_sqlalchemy()
    t0 = time.time()
    for i in xrange(n):
        customer, created = update_or_create(i)
        if created is True:
            DBSession.add(customer)
        if i % 1000 == 0:
            DBSession.flush()
    DBSession.commit()
    print(
        "SQLAlchemy ORM: Total time for " + str(n) +
        " records " + str(time.time() - t0) + " secs")


def test_sqlalchemy_orm_pk_given(n=100000):
    init_sqlalchemy()
    t0 = time.time()
    for i in xrange(n):
        #customer = Customer(id=i + 1, name="NAME " + str(i))
        customer, created = update_or_create(i, id=i + 1, name="NAME " + str(i))
        if created is True:
            DBSession.add(customer)
        if i % 1000 == 0:
            DBSession.flush()
    DBSession.commit()
    print(
        "SQLAlchemy ORM pk given: Total time for " + str(n) +
        " records " + str(time.time() - t0) + " secs")


def test_sqlalchemy_core(n=100000):
    init_sqlalchemy()
    t0 = time.time()
    num_insert = int(n*(1-UPDATE_PORTION))
    engine.execute(
        Customer.__table__.insert(),
        [{"name": 'NAME ' + str(i)} for i in xrange(num_insert)]
    )
    update_stmt = Customer.__table__.update().\
                    where(Customer.__table__.c.name == bindparam('oldname')).\
                    values(name=bindparam('newname'))
    engine.execute(
        update_stmt,
        [{"oldname": 'NAME ' + str(random.randint(0, num_insert)),
          "newname": 'UPDATED ' + str(i)} for i in xrange(n-num_insert)]
    )
    print(
        "SQLAlchemy Core: Total time for " + str(n) +
        " records " + str(time.time() - t0) + " secs")


def init_sqlite3(dbname):
    conn = sqlite3.connect(dbname)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS customer")
    c.execute(
        "CREATE TABLE customer (id INTEGER NOT NULL, "
        "name VARCHAR(255), PRIMARY KEY(id))")
    conn.commit()
    return conn


def test_sqlite3(n=100000, dbname='sqlite3.db'):
    conn = init_sqlite3(dbname)
    c = conn.cursor()
    t0 = time.time()
    name_counter = 0
    for i in xrange(n):
        if random.random() <= UPDATE_PORTION:
            target = random.randint(0, name_counter-1)
            row = ('UPDATED ' + str(target), 'NAME ' + str(target),)
            c.execute("UPDATE customer SET name = (?) WHERE name = (?)", row)
        else:
            row = ('NAME ' + str(name_counter),)
            c.execute("INSERT INTO customer (name) VALUES (?)", row)
            name_counter += 1
    conn.commit()
    print(
        "sqlite3: Total time for " + str(n) +
        " records " + str(time.time() - t0) + " sec")

if __name__ == '__main__':
    test_sqlalchemy_orm(100000)
    test_sqlalchemy_orm_pk_given(100000)
    test_sqlalchemy_core(100000)
    test_sqlite3(100000)