from abc import ABC, abstractmethod
from typing import Callable


class Token(ABC):
    @abstractmethod
    def translate(self, translator) -> str:
        pass


Tokenizer = Callable[[str], Token]


class Parser:
    def __init__(self, stream, tokenizer: Tokenizer):
        self.stream = iter(stream)
        self.tokenize = tokenizer
    
    def __iter__(self):
        return self
    
    def __next__(self) -> Token:
        line = next(self.stream).strip()
        while(self.is_ignored(line)):
            line = next(self.stream).strip()
        return self.tokenize(line)
    
    def is_ignored(self, line):
        return line == "" or line.startswith('//')
        
