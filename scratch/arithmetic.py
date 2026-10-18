"""Bounded exact arithmetic in application code, never Python eval."""
import ast
from fractions import Fraction
import re


def calculate(text):
    expression = text.strip().lower().replace('×', '*').replace('÷', '/')
    expression = re.sub(r'^hesapla\s*:?\s*', '', expression)
    expression = re.sub(r'\s*(?:kaç eder|kac eder|kaç|kac)\s*[?!.]*$', '', expression).strip()
    expression = expression.rstrip('?').strip()
    # A number alone may be a clarification choice, never a calculation.
    if not re.fullmatch(r'[0-9.\s+*/()\-]+', expression) or not any(c in expression for c in '+*/-'):
        return None
    if len(expression) > 200:
        return {'source':'application', 'text':'Hesaplama için en fazla 200 karakterlik bir ifade yaz.'}
    try:
        tree = ast.parse(expression, mode='eval')
        if sum(1 for _ in ast.walk(tree)) > 80:
            raise ValueError('İfade fazla karmaşık.')

        def visit(node):
            if isinstance(node, ast.Constant) and type(node.value) in (int,float):
                literal = ast.get_source_segment(expression,node)
                if not re.fullmatch(r'(?:\d+(?:\.\d*)?|\.\d+)',literal) or len(literal) > 50:
                    raise ValueError('Sayı sınırı aşıldı.')
                value = Fraction(literal)
            elif isinstance(node, ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):
                value = visit(node.operand) * (-1 if isinstance(node.op,ast.USub) else 1)
            elif isinstance(node, ast.BinOp) and isinstance(node.op,(ast.Add,ast.Sub,ast.Mult,ast.Div)):
                left, right = visit(node.left), visit(node.right)
                if isinstance(node.op,ast.Add):
                    value = left + right
                elif isinstance(node.op,ast.Sub):
                    value = left - right
                elif isinstance(node.op,ast.Mult):
                    value = left * right
                else:
                    value = left / right
            else:
                raise ValueError('Yalnızca +, -, *, / ve parantez destekleniyor.')
            if value.numerator.bit_length() > 1024 or value.denominator.bit_length() > 1024:
                raise ValueError('Hesaplama sınırı aşıldı.')
            return value

        value = visit(tree.body)
        answer = str(value.numerator) if value.denominator == 1 else f'{value.numerator}/{value.denominator}'
        return {'source':'application', 'calculation':True,
                'text':f'{expression} = {answer}\nYerel uygulama hesaplaması; model yanıtı değildir. Kesirli sonuçlar tam değerleriyle gösterilir.'}
    except ZeroDivisionError:
        return {'source':'application','text':'Sıfıra bölme tanımsızdır.'}
    except (SyntaxError, ValueError, RecursionError):
        return {'source':'application','text':'İfadeyi hesaplayamadım. +, -, *, / ve parantez kullanabilirsin. Ondalıkları noktayla yaz; ifadeyi kısa tut.'}
