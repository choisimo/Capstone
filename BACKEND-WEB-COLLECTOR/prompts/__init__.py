"""
프롬프트 템플릿 모듈
"""
from .base import BasePromptTemplate
from .sentiment import SentimentPromptTemplate
from .absa import ABSAPromptTemplate
from .pension import PensionPromptTemplate
from .news import NewsAnalysisPromptTemplate
from .structure import StructureLearningPromptTemplate
from .change import ChangeAnalysisPromptTemplate

__all__ = [
    'BasePromptTemplate',
    'SentimentPromptTemplate',
    'ABSAPromptTemplate',
    'PensionPromptTemplate',
    'NewsAnalysisPromptTemplate',
    'StructureLearningPromptTemplate',
    'ChangeAnalysisPromptTemplate',
]
