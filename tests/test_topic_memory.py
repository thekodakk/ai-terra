import unittest
from unittest.mock import Mock
from scratch.dialogue import Dialogue
from scratch.routing import QuestionIndex


class TopicMemoryTests(unittest.TestCase):
    def setUp(self):
        self.pairs = [
            {'question':'liste nedir','answer':'Liste değerleri tutar.'},
            {'question':'döngü nedir','answer':'Döngü işlemi tekrarlar.'},
            {'question':'teşekkürler','answer':'Rica ederim.'},
            {'question':'çok sağ ol','answer':'Rica ederim.'},
            {'question':'tamam','answer':'Tamam.'},
            {'question':'başka konuya geçelim','answer':'Yeni konuyu yaz.'},
            {'question':'yanlış anladın','answer':'Yeniden açıklar mısın?'},
        ]
        self.model = Mock()
        self.session = Dialogue(self.model, {'conversation_pairs':self.pairs})

    def say(self, index):
        self.model.generate.return_value = self.pairs[index]['answer']
        return self.session.reply(self.pairs[index]['question'])

    def test_acknowledgements_and_aliases_preserve_topic(self):
        self.say(0)
        for index in (2,3,4):
            self.say(index)
            self.assertEqual(self.session.last_question, 'liste nedir')
        self.model.generate.return_value = self.pairs[0]['answer']
        self.assertEqual(self.session.reply('tekrar anlat')['text'], self.pairs[0]['answer'])
        self.assertIn('liste nedir', self.model.generate.call_args.args[0])

    def test_back_restores_previous_topic_using_model(self):
        self.say(0)
        self.say(1)
        self.say(4)
        self.model.generate.return_value = self.pairs[0]['answer']
        result = self.session.reply('önceki konuya dön')
        self.assertEqual(result['source'], 'model')
        self.assertEqual(self.session.last_question, 'liste nedir')
        self.assertFalse(self.session.topic_history)
        self.assertEqual(self.session.reply('önceki konuya dön')['source'], 'application')

    def test_failed_back_does_not_consume_history(self):
        self.say(0)
        self.say(1)
        self.model.generate.return_value = 'bozuk çıktı'
        self.assertEqual(self.session.reply('önceki konuya dön')['source'], 'application')
        self.assertEqual(self.session.topic_history, ['liste nedir'])
        self.assertEqual(self.session.last_question, 'döngü nedir')

    def test_reset_and_correction_remove_stale_topics(self):
        for index in (5,6):
            self.say(0)
            self.say(1)
            self.say(index)
            self.assertIsNone(self.session.last_question)
            self.assertFalse(self.session.topic_history)
            self.assertEqual(self.session.reply('tekrar anlat')['source'], 'application')

    def test_unknown_request_and_clear_remove_history(self):
        self.say(0)
        self.say(1)
        self.session.reply('uzaylıların adresi')
        self.assertFalse(self.session.topic_history)
        self.say(0)
        self.say(1)
        self.session.clear()
        self.assertFalse(self.session.topic_history)

    def test_generator_index_keeps_questions_and_vectors_aligned(self):
        index = QuestionIndex(iter(self.pairs))
        self.assertEqual(len(index.vectors), len(self.pairs))
        self.assertEqual(index.ranked('liste nedir')[0][1]['question'], 'liste nedir')

