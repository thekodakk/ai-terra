import unittest
from unittest.mock import Mock
from scratch.dialogue import Dialogue
from scratch.routing import QuestionIndex

PAIRS = [
    {'question':'değişken nedir anlatır mısın', 'answer':'Değişken bir değerin ismidir.'},
    {'question':'fonksiyon nedir açıklar mısın', 'answer':'Fonksiyon tekrar çağrılabilen kod bölümüdür.'},
    {'question':'merhaba', 'answer':'Merhaba!'},
]


class DialogueTests(unittest.TestCase):
    def setUp(self):
        self.model = Mock()
        self.session = Dialogue(self.model, {'conversation_pairs':PAIRS})

    def test_followup_reuses_last_successful_topic(self):
        self.model.generate.return_value = PAIRS[0]['answer']
        self.session.reply(PAIRS[0]['question'])
        result = self.session.reply('tekrar anlat')
        self.assertEqual(result['source'], 'model')
        self.assertIn('context_note', result)
        self.assertIn(PAIRS[0]['question'], self.model.generate.call_args.args[0])

    def test_clear_and_unsupported_message_remove_stale_context(self):
        self.model.generate.return_value = 'Merhaba!'
        self.session.reply('merhaba')
        self.session.clear()
        self.assertEqual(self.session.reply('anlamadım')['source'], 'application')
        self.session.reply('merhaba')
        self.session.reply('uzaylılar ne zaman gelecek')
        self.assertIsNone(self.session.last_question)

    def test_followup_uses_trained_alternative_not_stored_answer(self):
        from scratch.conversation import normalize
        alternate = {'question':'değişken için daha sade açıklama', 'answer':'Bir değere isim takıyoruz.'}
        self.session = Dialogue(self.model, {'conversation_pairs':PAIRS+[alternate],
            'followup_links':{normalize(PAIRS[0]['question']):alternate['question']}})
        self.model.generate.return_value = PAIRS[0]['answer']
        self.session.reply(PAIRS[0]['question'])
        self.model.generate.return_value = alternate['answer']
        result = self.session.reply('anlamadım')
        self.assertEqual(result['text'], alternate['answer'])
        self.assertIn(alternate['question'], self.model.generate.call_args.args[0])
        self.assertIn('daha sade', result['context_note'])
        self.model.generate.return_value = 'bozuk çıktı'
        self.assertEqual(self.session.reply('anlamadım')['source'], 'application')

    def test_followup_can_switch_to_another_known_concept(self):
        self.model.generate.return_value = PAIRS[0]['answer']
        self.session.reply(PAIRS[0]['question'])
        self.model.generate.return_value = PAIRS[1]['answer']
        result = self.session.reply('peki fonksiyon?')
        self.assertEqual(result['source'], 'model')
        self.assertIn('context_note', result)
        self.assertIn('fonksiyon', self.session.last_question)

    def test_approximate_route_still_uses_neural_generation(self):
        self.model.generate.return_value = PAIRS[0]['answer']
        result = self.session.reply('bir değişkeni anlatır mısın')
        self.assertEqual(result['source'], 'model')
        self.assertEqual(result['matched_question'], PAIRS[0]['question'])
        self.model.generate.assert_called_once()

    def test_operator_and_compound_routes_abstain(self):
        index = QuestionIndex(PAIRS)
        for query in ['değişken ve fonksiyon nedir', 'değişken değil fonksiyon anlat', '2-3 kaç eder']:
            self.assertIsNone(index.match(query))

    def test_ambiguous_routes_abstain(self):
        index = QuestionIndex([{'question':'abc nedir', 'answer':'a'}, {'question':'abc nedir', 'answer':'b'}])
        self.assertIsNone(index.match('abc anlat'))
