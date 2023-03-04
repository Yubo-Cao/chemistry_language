from chemistry_lang.ch_tokenizer import tokenize
from chemistry_lang.ch_token import Token, TokenType
from chemistry_lang.ch_number import CHNumber


def test_expression():
    assert tokenize('1 + 2') == [
        Token(TokenType.NUM, CHNumber('1')),
        Token(TokenType.ADD),
        Token(TokenType.NUM, CHNumber('2')),
        Token(TokenType.SEP),
        Token(TokenType.EOF),
    ]

    assert tokenize('1.2 + 2.3') == [
        Token(TokenType.NUM, CHNumber('1.2')),
        Token(TokenType.ADD),
        Token(TokenType.NUM, CHNumber('2.3')),
        Token(TokenType.SEP),
        Token(TokenType.EOF),
    ]
