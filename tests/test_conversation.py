import unittest
from unittest.mock import Mock
from scratch.conversation import normalize, respond, prompt_for


class ConversationTests(unittest.TestCase):
    def setUp(self):
        self.model = Mock()
        self.info = {'conversation_pairs': [{'question': 'merhaba', 'answer': 'Merhaba!'}]}

    def test_normalization(self):
        self.assertEqual(normalize('  MERHABA!!!  '), 'merhaba')
        self.assertEqual(normalize('İnternet gerekli mi?'), 'internet gerekli mi')

    def test_math_operators_are_not_conflated(self):
        self.assertNotEqual(normalize('2 + 3 kaç eder'), normalize('2 - 3 kaç eder'))
        self.assertNotEqual(normalize('2 * 3 kaç eder'), normalize('2 / 3 kaç eder'))
        self.assertNotEqual(normalize('2.5 + 3'), normalize('25 + 3'))

    def test_answer_really_comes_from_model(self):
        self.model.generate.return_value = 'Merhaba!'
        result = respond(self.model, self.info, 'MERHABA!')
        self.assertEqual(result, {'source': 'model', 'text': 'Merhaba!'})
        self.assertEqual(self.model.generate.call_args.args[0], prompt_for('merhaba'))

    def test_unknown_does_not_generate_gibberish(self):
        result = respond(self.model, self.info, 'benim için kod yaz')
        self.assertEqual(result['source'], 'application')
        self.model.generate.assert_not_called()

    def test_broken_output_is_not_replaced_by_expected_answer(self):
        self.model.generate.return_value = 'pmera de nedir mum'
        result = respond(self.model, self.info, 'merhaba')
        self.assertEqual(result['source'], 'application')
        self.assertNotIn('Merhaba!', result['text'])

    def test_untrained_checkpoint_never_claims_it_can_chat(self):
        self.assertEqual(respond(self.model, {}, 'hello')['source'], 'application')
        self.model.generate.assert_not_called()


if __name__ == '__main__':
    unittest.main()
