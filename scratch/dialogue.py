"""Explicit session memory and follow-up resolution in application code."""
from .conversation import normalize, respond
from .routing import fold, QuestionIndex
from .arithmetic import calculate


class Dialogue:
    def __init__(self, model, info):
        self.model, self.info = model, info
        self.index = QuestionIndex(info.get('conversation_pairs', []))
        # An alias taught the same answer can use that answer's existing
        # alternative explanation. This is application bookkeeping, not memory
        # learned by the network. Conflicting alternatives are not inferred.
        known={normalize(p['question']):p for p in info.get('conversation_pairs',[])}
        self.followup_links=dict(info.get('followup_links',{}))
        alternatives={}
        for key,target in self.followup_links.items():
            if normalize(key) in known and normalize(target) in known:
                answer=known[normalize(key)]['answer']
                alternatives.setdefault(answer,set()).add(target)
        for key,pair in known.items():
            options=alternatives.get(pair['answer'],set())
            if len(options)==1:
                self.followup_links.setdefault(key,next(iter(options)))
        self.last_question = None
        self.pending = []
        self.topic_history = []
        self.known = known
        # Only aliases already taught the same answer inherit these roles.
        self.ack_answers = {known[normalize(q)]['answer'] for q in
                            ('teşekkürler', 'sağ ol', 'tamam', 'anladım', 'merhaba') if normalize(q) in known}
        self.reset_answers = {known[normalize(q)]['answer'] for q in
                              ('başka konuya geçelim', 'yanlış anladın', 'cevabın yanlış', 'yarın devam edelim')
                              if normalize(q) in known}

    def clear(self):
        self.last_question = None
        self.pending = []
        self.topic_history = []

    def remember_topic(self, question):
        answer = self.known.get(normalize(question), {}).get('answer')
        if answer in self.reset_answers:
            self.clear()
            return
        if answer in self.ack_answers:
            return
        previous_answer = self.known.get(normalize(self.last_question or ''), {}).get('answer')
        if self.last_question and answer != previous_answer:
            self.topic_history.append(self.last_question)
            self.topic_history = self.topic_history[-8:]
        self.last_question = question

    def reply(self, text, budget=1536, stop=None, emit=None):
        query = normalize(text)
        folded = fold(query)
        if self.pending:
            if folded in {'hayir','hicbiri','iptal','vazgectim'}:
                self.clear()
                return {'source':'application','text':'Seçenekleri bıraktım. Sorunu başka bir cümleyle yazabilirsin.'}
            selection = {'1':0,'birinci':0,'birincisi':0,'ilk secenek':0,'ilkini':0,
                         '2':1,'ikinci':1,'ikincisi':1,'ikinci secenek':1,
                         '3':2,'ucuncu':2,'ucuncusu':2}.get(folded)
            if folded.isdecimal() and selection is None:
                return {'source':'application','text':'Gösterilen seçeneklerden birinin numarasını yazabilirsin.'}
            if folded == 'evet':
                if len(self.pending)==1:
                    selection=0
                else:
                    return {'source':'application','text':'Hangi seçeneği kastettin? Numarasını yazabilirsin.'}
            if selection is not None:
                if selection>=len(self.pending):
                    return {'source':'application','text':'Gösterilen seçeneklerden birinin numarasını yazabilirsin.'}
                chosen=self.pending[selection]
                self.pending=[]
                result=respond(self.model,self.info,chosen,budget,stop,emit)
                if result['source']=='model':
                    self.remember_topic(chosen)
                    result['context_note']='Uygulama, seçtiğin öğretilmiş soruyu modele iletti: '+chosen
                return result
            # A fresh question replaces, rather than accidentally confirming,
            # choices from an earlier message.
            self.pending=[]
        if query not in self.known:
            calculation = calculate(text)
            if calculation is not None:
                self.clear()
                return calculation
        if folded in {'onceki konuya don', 'bir onceki konuya don', 'onceki konuyu tekrar anlat'}:
            if not self.topic_history:
                return {'source':'application','text':'Bu sohbette dönülebilecek önceki bir konu yok.'}
            target = self.topic_history[-1]
            result = respond(self.model, self.info, target, budget, stop, emit)
            if result['source'] == 'model':
                self.topic_history.pop()
                self.last_question = target
                result['context_note'] = 'Uygulama bu oturumdaki önceki konuyu seçti: ' + target
            return result
        example = folded in {'ornek ver', 'bir ornek ver', 'ornekle anlat', 'daha basit anlat', 'daha sade anlat',
                             'bunun ornegini ver', 'buna ornek ver', 'bir ornek gosterebilir misin', 'bunu ornekle anlat',
                             'peki bunun ornegi var mi', 'daha basit aciklar misin'}
        followup = example or fold(query) in {'tekrar anlat', 'bir daha anlat', 'tekrar acikla', 'bir daha acikla', 'anlamadim', 'bunu tekrar acikla'}
        if followup:
            if not self.last_question:
                return {'source':'application', 'text':'Hangi konuyu tekrar açıklamamı istersin? Henüz bu sohbette yanıtlanmış bir konu yok.'}
            target = self.followup_links.get(normalize(self.last_question))
            if example and not target:
                return {'source':'application', 'text':'Bu konu için henüz ayrı bir örnekli açıklama öğretilmedi. Başka bir konu seçebilir veya önceki yanıtı tekrar isteyebilirsin.'}
            result = respond(self.model, self.info, target or self.last_question, budget, stop, emit)
            if result['source'] == 'model':
                result['context_note'] = ('Uygulama son konu için öğretilmiş daha sade açıklamayı seçti.' if target else
                    'Uygulama son yanıtlanan konuyu hatırladı. Bu konu için başka açıklama öğretilmedi; önceki yanıt yeniden üretiliyor.')
            return result
        if self.last_question and fold(query).startswith(('peki ', 'ya ')):
            subject = query.split(' ', 1)[1].strip()
            # A bounded conversational ellipsis: "what about functions?" after
            # an explanation becomes "what are functions?" in application code.
            if subject and len(subject.split()) <= 3:
                result = respond(self.model, self.info, subject + ' nedir', budget, stop, emit, index=self.index)
                if result['source'] == 'model':
                    self.remember_topic(result.get('matched_question', subject + ' nedir'))
                    result['context_note'] = 'Uygulama takip sorusunu şöyle tamamladı: ' + subject + ' nedir?'
                    return result
        result = respond(self.model, self.info, text, budget, stop, emit, index=self.index)
        if result['source'] == 'model':
            self.remember_topic(result.get('matched_question', text))
        else:
            # Do not resolve a follow-up to a stale topic after an unrelated request.
            self.last_question = None
            self.topic_history = []
            suggestions=self.index.suggest(text) if result.get('reason')=='unknown_question' else []
            if suggestions and not (stop is not None and stop.is_set()):
                self.pending=[p['question'] for p in suggestions]
                result={'source':'application', 'suggestions':list(self.pending),
                        'text':'Sorunu kesin eşleştiremedim. Şunlardan birini mi kastettin?\n'+
                        '\n'.join(f'{i+1}) {q}' for i,q in enumerate(self.pending))+
                        '\nNumarasını yazabilir, “hiçbiri” diyebilir veya sorunu yeniden yazabilirsin. Bunlar uygulamanın önerileri.'}
        return result
