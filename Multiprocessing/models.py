from sqlalchemy import create_engine, Column, ForeignKey, Integer, String, Boolean, BLOB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

engine = create_engine('sqlite:///game.db')

Base = declarative_base()
Session = sessionmaker(bind = engine)


class Monster(Base):
    __tablename__ = 'monster'
    id = Column(Integer, primary_key = True)
    name = Column(String(32), nullable = False, unique = True)
    attack = Column(Integer, nullable = False)
    # agro = Column(Integer, nullable = True)
    defense = Column(Integer, nullable = False)
    regen = Column(Integer, nullable = False)
    health = Column(Integer, nullable = False)
    gold = Column(Integer, nullable = False)
    room = Column(Integer, nullable = False)
    description = Column(String(256), nullable = False)

    def __init__(self, name, attack, defense, regen, health, gold, room, description):
        self.name = name
        self.attack = attack
        self.defense = defense
        self.regen = regen
        self.health = health
        # self.agro = agro
        self.gold = gold
        self.room = room
        self.description = description


class Room(Base):
    __tablename__ = 'room'
    id = Column(Integer, primary_key = True)
    name = Column(String(32), nullable = False)
    description = Column(String(256), nullable = False)

    def __init__(self, name, description):
        self.name = name
        self.description = description


class Connection(Base):
    __tablename__ = 'connection'
    id = Column(Integer, primary_key = True)
    room1 = Column(Integer, nullable = False)
    room2 = Column(Integer, nullable = False)
    condition = Column(String(256)) # monster_name: dead, capacity: > 10, capacity == 1 

    def __init__(self, room1, room2):
        self.room1 = room1
        self.room2 = room2
        self.condition = ''
    
    def __repr__(self):
        return f'{self.room1} -> {self.room2}'


class Loot(Base):
    __tablename__ = 'loot'
    id = Column(Integer, primary_key = True)
    room = Column(Integer, nullable = False)
    name = Column(String(32), nullable = False)
    value = Column(Integer, nullable = False)
    rewards = Column(String(256))
    message = Column(String(256))
    condition = Column(String(256)) # monster_name: dead, capacity: > 10, capacity == 1 

    def __init__(self, name, value, rewards, message, condition):
        self.name = name
        self.value = value
        self.rewards = rewards
        self.message = message
        self.condition = condition


Base.metadata.create_all(bind = engine)