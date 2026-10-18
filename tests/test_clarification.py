import unittest
from unittest.mock import Mock
from scratch.dialogue import Dialogue

PAIRS=[{'question':'python nedir','answer':'Python bir dildir.'},
       {'question':'python listesi nedir','answer':'Liste değerleri tutar.'}]


class ClarificationTests(unittest.TestCase):
    def setUp(self):
        self.model=Mock()
        self.dialogue=Dialogue(self.model,{'conversation_pairs':PAIRS})
        # Ambiguity is deliberate: test the selection protocol independently
        # from lexical ranking, which is audited with real corpus/weights.
        self.dialogue.index.match=Mock(return_value=None)
        self.dialogue.index.suggest=Mock(return_value=PAIRS)

    def test_does_not_generate_until_user_selects(self):
        result=self.dialogue.reply('python listelerini anlat')
        self.assertEqual(result['source'],'application')
        self.assertEqual(len(result['suggestions']),2)
        self.model.generate.assert_not_called()
        self.model.generate.return_value=PAIRS[1]['answer']
        chosen=self.dialogue.reply('2')
        self.assertEqual(chosen['text'],PAIRS[1]['answer'])
        self.assertEqual(self.dialogue.last_question,PAIRS[1]['question'])
        self.assertIn(PAIRS[1]['question'],self.model.generate.call_args.args[0])
        self.assertFalse(self.dialogue.pending)

    def test_yes_with_multiple_choices_never_guesses(self):
        self.dialogue.reply('anlat bakalım')
        self.assertEqual(self.dialogue.reply('evet')['source'],'application')
        self.assertEqual(self.dialogue.reply('3')['source'],'application')
        self.assertEqual(self.dialogue.reply('9')['source'],'application')
        self.model.generate.assert_not_called()
        self.assertEqual(len(self.dialogue.pending),2)

    def test_cancel_clear_and_new_question_remove_stale_choices(self):
        self.dialogue.reply('anlat bakalım')
        self.dialogue.reply('hiçbiri')
        self.assertFalse(self.dialogue.pending)
        self.dialogue.reply('anlat bakalım')
        self.dialogue.clear()
        self.assertFalse(self.dialogue.pending)
        self.dialogue.reply('anlat bakalım')
        self.model.generate.return_value=PAIRS[0]['answer']
        self.dialogue.reply('python nedir')
        self.assertFalse(self.dialogue.pending)

    def test_broken_output_or_short_budget_does_not_become_clarification(self):
        self.model.generate.return_value='bozuk'
        self.assertNotIn('suggestions',self.dialogue.reply('python nedir'))
        self.assertNotIn('suggestions',self.dialogue.reply('python nedir',budget=1))
        self.dialogue.index.suggest.assert_not_called()

    def test_single_option_accepts_explicit_yes(self):
        self.dialogue.index.suggest.return_value=PAIRS[:1]
        self.dialogue.reply('hangi python')
        self.model.generate.return_value=PAIRS[0]['answer']
        self.assertEqual(self.dialogue.reply('evet')['source'],'model')

    def test_taught_alias_uses_existing_alternative_with_new_followup_wording(self):
        base={'question':'liste nedir','answer':'Liste sıralı değerleri tutar.'}
        alias={'question':'bana listeden bahset','answer':base['answer']}
        alternative={'question':'liste için örnek','answer':'renkler = ["mavi", "yeşil"]'}
        session=Dialogue(self.model,{'conversation_pairs':[base,alias,alternative],
            'followup_links':{'liste nedir':alternative['question']}})
        self.model.generate.return_value=alias['answer']
        session.reply(alias['question'])
        self.model.generate.return_value=alternative['answer']
        self.assertEqual(session.reply('peki bunun örneği var mı')['text'],alternative['answer'])
