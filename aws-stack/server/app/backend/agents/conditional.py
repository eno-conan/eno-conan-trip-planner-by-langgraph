from enum import Enum

class ConditionalEdge(Enum):
    '''
    条件付きEdgeのKV
    '''
    FAILED = '__FAILED__'
    SUCCESS = '__SUCCESS__'

class TripStyle(Enum):
    '''
    条件付きEdgeのKV
    '''
    RECOMMEND = '__RECOMMEND__'
    DESIGNATE = '__DESIGNATE__'