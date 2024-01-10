from sqlalchemy import create_engine, Column, Integer, String, select
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base
from sqlalchemy.sql import exists
from contextlib import contextmanager
from collections import defaultdict

from dotenv import load_dotenv
import os
from log_config import setup_logging

logger = setup_logging('database', 'imagenationbot.log')
load_dotenv()
Base = declarative_base()


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    name = Column(String)
    nick = Column(String)
    discriminator = Column(String)

    def __repr__(self):
        return f'<User(user_id={self.user_id}, nick={self.nick}, name={self.name}, discriminator={self.discriminator})>'


class Address(Base):
    __tablename__ = 'addresses'

    user_id = Column(Integer, primary_key=True)
    address = Column(String, primary_key=True)
    stake_address = Column(String)

    def __repr__(self):
        return f"<Address(user_id={self.user_id}, address={self.address}, stake_address={self.stake_address})>"


class Holding(Base):
    __tablename__ = 'holdings'

    role_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, primary_key=True)
    count = Column(Integer, default=0)

    def __repr__(self):
        return f"<Holding(role_id={self.role_id}, user_id={self.user_id}, count={self.count})>"


class RoleAssignment(Base):
    __tablename__ = 'role_assignments'

    user_id = Column(Integer, primary_key=True)
    role_id = Column(Integer, primary_key=True)
    server_id = Column(Integer, primary_key=True)

    def __repr__(self):
        return f"<RoleAssignment(user_id={self.user_id}, role_id={self.role_id}, server_id={self.server_id})>"


class RolesForPolicies(Base):
    __tablename__ = 'roles_policies'

    server_id = Column(Integer, primary_key=True)
    role_id = Column(Integer, primary_key=True)
    policy_id = Column(String, primary_key=True)

    def __repr__(self):
        return f"<RolesForPolicies(server_id={self.server_id}, role_id={self.role_id}, policy_id={self.policy_id})>"


engine = create_engine(os.getenv('DATABASE_URL'))
Base.metadata.create_all(engine)
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)


def add_user(user_id, name, nick, discriminator):
    with session_scope() as session:
        user = session.query(User).filter(User.user_id == user_id).first()

        if user is None:
            user = User(user_id=user_id)
        user.name = name
        user.nick = nick
        user.discriminator = discriminator
        session.add(user)


def add_address(user_id, address, stake_address):
    with session_scope() as session:
        entry = session.query(Address).filter(Address.user_id == user_id,
                                              Address.stake_address == stake_address).first()
        if not entry:
            new_entry = Address(address=address, user_id=user_id, stake_address=stake_address)
            session.add(new_entry)


def get_all_addresses():
    with session_scope() as session:
        addresses = session.query(Address).all()
        grouped = defaultdict(list)
        for a in addresses:
            grouped[a.user_id].append(a.stake_address)
        return grouped


def get_addresses(user_id):
    with session_scope() as session:
        addresses = session.query(Address).filter(Address.user_id == user_id).all()
        logger.debug([(a.address, a.stake_address) for a in addresses])
        return [a.address for a in addresses]


def delete_address(session, user_id, stake_address):
    # Query for the specific record
    address_to_delete = session.query(Address).filter(
        Address.user_id == user_id,
        Address.stake_address == stake_address
    ).first()

    if address_to_delete:
        session.delete(address_to_delete)
        session.commit()
        logger.debug("Address deleted successfully.")
    else:
        logger.debug(f"Address {address_to_delete} not found.")


def remove_address(user_id, address, stake_address):
    with session_scope() as session:  # assuming you have a session context manager
        delete_address(session, user_id, stake_address)


def get_all_roles():
    roles = {}
    with session_scope() as session:
        assignments = session.query(Holding).all()
        for a in assignments:
            if a.user_id not in roles:
                roles[a.user_id] = []
            roles[a.user_id].append(a.role_id)
    return roles


def get_all_policies():
    policies = {}
    with session_scope() as session:
        roles = session.query(RolesForPolicies).all()
        for role in roles:
            if role.policy_id not in policies:
                policies[role.policy_id] = {}
            policies[role.policy_id][role.server_id] = role.role_id
    return policies


def get_managed_roles(server_id):
    with session_scope() as session:
        return [result[0] for result in
                session.query(RolesForPolicies.role_id).filter(RolesForPolicies.server_id == server_id).all()]


def add_holding(user_id, role_id, count):
    logger.debug(f'adding {role_id} to user {user_id}')
    with session_scope() as session:
        entry = session.query(Holding).filter(Holding.user_id == user_id, Holding.role_id == role_id).first()
        if not entry:
            entry = Holding(user_id=user_id, role_id=role_id)
        entry.count = count
        session.add(entry)


def reset_holding(user_id, role_ids):
    if not role_ids:
        return
    logger.debug(f'reset holding {user_id} {role_ids}')
    with session_scope() as session:
        logger.debug(f'reset holding query {session.query(Holding).filter(Holding.user_id == user_id).all()}')
        logger.debug(f'to delete holdings {user_id, role_ids} {session.query(Holding).filter(Holding.user_id == user_id, ~Holding.role_id.in_(role_ids)).all()}')
        session.query(Holding).filter(Holding.user_id == user_id, ~Holding.role_id.in_(role_ids)).delete()


def remove_holding(user_id, role_id):
    with session_scope() as session:
        session.query(Holding).filter_by(user_id=user_id, role_id=role_id).delete()


def clean_up_holdings():
    with session_scope() as session:
        subquery = select(Address.user_id).where(Address.user_id == Holding.user_id)
        not_exists_query = ~exists(subquery)
        session.query(Holding).filter(not_exists_query).delete()
