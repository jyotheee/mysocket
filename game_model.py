from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.sqlite import DATETIME
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import sessionmaker, scoped_session
import random

global game_board

engine = create_engine("sqlite:///gameinfo.db", echo=False, connect_args={'timeout': 5})
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
    return board[move] == ''

def makeMove(board, letter, move):
    board[move] = letter

def chooseRandomMoveFromList(board, movesList):
    # Returns a valid move from the passed list on the passed board.
    # Returns None if there is no valid move.
    possibleMoves = []
    for i in movesList:
        if isSpaceFree(board, i):
            possibleMoves.append(i)
    if len(possibleMoves) != 0:
        return random.choice(possibleMoves)
    else:
        return None

def getBoardCopy(board):
    # Make a duplicate of the board list and return it the duplicate.
    dupeBoard = []
    for i in board:
        dupeBoard.append(i)
    return dupeBoard


def isWinner(b, l):
    return ((b[1] == l and b[2] == l and b[3] == l) or
            (b[4] == l and b[5] == l and b[6] == l) or
            (b[7] == l and b[8] == l and b[9] == l) or
            (b[1] == l and b[4] == l and b[7] == l) or
            (b[2] == l and b[5] == l and b[8] == l) or
            (b[3] == l and b[6] == l and b[9] == l) or
            (b[1] == l and b[5] == l and b[9] == l) or
            (b[3] == l and b[5] == l and b[7] == l))

def getWinningloc(b,l):
    loclist = []

    if (b[1] == l and b[2] == l and b[3] == l): loclist = [1,2,3]
    elif (b[4] == l and b[5] == l and b[6] == l): loclist = [4,5,6]
    elif (b[7] == l and b[8] == l and b[9] == l): loclist = [7,8,9]
    elif (b[1] == l and b[4] == l and b[7] == l): loclist = [1,4,7]
    elif (b[2] == l and b[5] == l and b[8] == l): loclist = [2,5,8]
    elif (b[3] == l and b[6] == l and b[9] == l): loclist = [3,6,9]
    elif (b[1] == l and b[5] == l and b[9] == l): loclist = [1,5,9]
    elif (b[3] == l and b[5] == l and b[7] == l): loclist = [3,5,7]
    else: loclist = [0,0,0]

    return loclist

def isFull(b):
    return (b[1] != '' and b[2] != '' and b[3] != '' and b[4] != '' and
            b[5] != '' and b[6] != '' and b[7] != '' and b[8] != '' and b[9] != '')


def compMove(board):
    completter = "O"

    checkb = getBoardCopy(board);

    # check if comp can win the next turn
    for i in range(1, 10):
        if isSpaceFree(checkb, i):
            makeMove(checkb, "O", i)
            if isWinner(checkb, "O"):
                return i

    checkb = getBoardCopy(board);

    # check if player can win and then block him
    for i in range(1, 10):
        print "checking players move"
        if isSpaceFree(checkb, i):
            print "inside the isSpaceFree"
            makeMove(checkb, "X", i)
            if isWinner(checkb, "X"):
                print "found winner"
                return i

    # choose from corners 1, 3, 7, 9
    move = chooseRandomMoveFromList(board, [1, 3, 7, 9])
    print "Random corner move is %d", move
    if move != None:
        return move

    # Try to take the center, if it is free.
    if isSpaceFree(board, 5):
        return 5

    # Move on one of the sides.
    return chooseRandomMoveFromList(board, [2, 4, 6, 8])

def create_results_dict(results):
    results_dict = {}
    for eachgame in results:
            if eachgame.winner in results_dict:
                results_dict[eachgame.winner] += 1
            else:
                results_dict[eachgame.winner] = 1
    return results_dict

def main():
    """In case we need this for something"""
    pass

if __name__ == "__main__":
    main()