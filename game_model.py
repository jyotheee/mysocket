from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.sqlite import DATETIME
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import sessionmaker, scoped_session

global game_board

engine = create_engine("sqlite:///gameinfo.db", echo=False)
dbsession = scoped_session(sessionmaker(bind=engine, autocommit=False, autoflush=False))

Base = declarative_base()
Base.query = dbsession.query_property()

### Class declarations go here
class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key = True)
    usr1 = Column(String(64), nullable = True)
    usr2 = Column(String(64), nullable = True)
    winner = Column(String(64), nullable = True)
    date = Column(Integer)    

class Move(Base):
    __tablename__ = "moves"

    moveid = Column(Integer, primary_key = True)
    gameid = Column(Integer, ForeignKey('games.id'), nullable = False)
    board_loc = Column(Integer, nullable = False)
    user = Column(String(64), nullable = False)

    usermove = relationship("Game", backref=backref("moves", order_by=moveid))

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key = True)
    socketid = Column(Integer)
    username = Column(String)

def createTable():
    Base.metadata.create_all(engine)

def createBoard():
    global game_board
    game_board = ['', '', '', '', '', '', '', '', '', '']

def updateGameBoard(letter, pos):
    global game_board
    game_board[pos] = letter
    return game_board

def isSpaceFree(board, move):
    return board[move] == ' '

def makeMove(board, letter, move):
    board[move] = letter

def isWinner(b, l):
    return ((b[1] == l and b[2] == l and b[3] == l) or
            (b[4] == l and b[5] == l and b[6] == l) or
            (b[7] == l and b[8] == l and b[9] == l) or
            (b[1] == l and b[4] == l and b[7] == l) or
            (b[2] == l and b[5] == l and b[8] == l) or
            (b[3] == l and b[6] == l and b[9] == l) or
            (b[1] == l and b[5] == l and b[9] == l) or
            (b[3] == l and b[5] == l and b[7] == l))

def isFull(b):
    return (b[1] != '' and b[2] != '' and b[3] != '' and b[4] != '' and
            b[5] != '' and b[6] != '' and b[7] != '' and b[8] != '' and b[9] != '')


def compMove(board):
    completter = "O"

    checkb = board;

    # check if comp can win the next turn
    for i in range(1, 10):
        if isSpaceFree(checkb, i):
            makeMove(checkb, "O", i)
            if isWinner(checkb, i):
                return i
    # check if player can win and then block him
    for i in range(1, 10):
        if isSpaceFree(checkb, i):
            makeMove(checkb, "X", i)
            if isWinner(checkb, i):
                return i

    # choose from corners 1, 3, 7, 9 


def main():
    """In case we need this for something"""
    pass

if __name__ == "__main__":
    main()