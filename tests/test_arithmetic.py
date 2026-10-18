import unittest
from unittest.mock import Mock
from scratch.arithmetic import calculate
from scratch.dialogue import Dialogue


class ArithmeticTests(unittest.TestCase):
    def test_precedence_parentheses_negatives_and_exact_decimals(self):
        for query,answer in [('2+3*4','14'),('(2+3)*4','20'),('-7/2','-7/2'),
                             ('0.1+0.2','3/10'),('hesapla: 8÷2 kaç eder?','4')]:
            result = calculate(query)
            self.assertIn('= '+answer+'\n',result['text'])
            self.assertEqual(result['source'],'application')

    def test_no_code_or_arbitrary_language_execution(self):
        for query in ['__import__("os").system("cmd")','open("x")','x+2',
                      '2+3 yanlış mı','2','2e999+1','float(1)+1']:
            self.assertIsNone(calculate(query))

    def test_invalid_unsupported_and_large_expressions(self):
        for query in ['1/0','2**1000','2//3','2+','('+ '2+'*100+'1)', '9'*51+'+1']:
            self.assertNotIn('calculation',calculate(query))

    def test_dialogue_calculation_never_calls_neural_model(self):
        model = Mock()
        session = Dialogue(model, {'conversation_pairs':[]})
        result = session.reply('(8+4)/3 kaç eder')
        self.assertTrue(result['calculation'])
        model.generate.assert_not_called()

    def test_number_selects_pending_question_before_calculator(self):
        pair = {'question':'liste nedir','answer':'Bir dizi değer.'}
        model = Mock()
        model.generate.return_value = pair['answer']
        session = Dialogue(model, {'conversation_pairs':[pair]})
        session.pending = [pair['question']]
        self.assertEqual(session.reply('1')['source'],'model')

    def test_taught_math_is_still_produced_by_model(self):
        pair = {'question':'2+3','answer':'Beş.'}
        model = Mock()
        model.generate.return_value = pair['answer']
        session = Dialogue(model,{'conversation_pairs':[pair]})
        self.assertEqual(session.reply('2+3')['source'],'model')
