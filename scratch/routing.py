"""Local lexical matching, separate from the neural model's capabilities."""
from collections import Counter
import math
import re
import unicodedata


def fold(text):
    text = text.lower().replace('ı', 'i')
    return ''.join(c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c))


def features(text):
    words = re.findall(r'[a-z]+', fold(text))
    counts = Counter()
    for word in words:
        counts['word:' + word] += 2
        bounded = '^' + word + '$'
        for n in (3, 4):
            counts.update(bounded[i:i+n] for i in range(len(bounded)-n+1))
    return counts


def content_words(text):
    stops = {'bir', 'bana', 'beni', 'bu', 'su', 'o', 've', 'ile', 'icin', 'ne', 'nedir', 'demek',
             'hakkinda', 'konusunu', 'konusunda', 'bilgi', 'lutfen', 'kisa', 'misin', 'mi', 'midir',
             'olarak', 'veriyi', 'tutmak', 'icinde', 'ise', 'nasil', 'yapar', 'yapilabilir', 'anlama', 'gelir'}
    return [word for word in re.findall('[a-z]+', fold(text))
            if word not in stops and not word.startswith(('acikla', 'anlat'))]


class QuestionIndex:
    def __init__(self, pairs):
        self.pairs = list(pairs)
        raw = [features(p['question']) for p in self.pairs]
        df = Counter(token for row in raw for token in row)
        self.idf = {token: math.log((len(raw)+1)/(count+1))+1 for token,count in df.items()}
        self.vectors = [self.vector(row) for row in raw]

    def vector(self, counts):
        vector = {key: (1+math.log(count))*self.idf[key] for key,count in counts.items() if key in self.idf}
        norm = math.sqrt(sum(value*value for value in vector.values())) or 1
        return {key:value/norm for key,value in vector.items()}

    def match(self, text, threshold=.54, margin=.10):
        # Approximate matching must never change numbers/operators or match a
        # compound/negated request to a simple definition.
        folded = fold(text)
        if re.search(r'[0-9+*/=<>]', folded) or re.search(r'\b(ve|ama|degil|istemiyorum|farki|arasindaki)\b', folded):
            return None
        best = self.ranked(text)
        if not best:
            return None
        score, pair = best[0]
        gap = score - (best[1][0] if len(best)>1 else 0)
        if score < threshold or gap < margin:
            return None
        query_words, target_words = content_words(text), content_words(pair['question'])
        if not query_words or any(not any(q == t or (min(len(q),len(t)) >= 4 and (q.startswith(t) or t.startswith(q)))
                                             for t in target_words) for q in query_words):
            return None
        # A high lexical score alone cannot tell "write Python" from "what is
        # Python". Restrict approximate routes to explanation questions.
        cues = ('nedir', 'ne demek', 'ne anlama', 'anlat', 'acikla', 'bilgi', 'ne ise', 'ne yapar', 'ne yapil')
        if not any(cue in folded for cue in cues):
            return None
        return {'pair': pair, 'score': round(score, 3)}

    def ranked(self, text):
        vector = self.vector(features(text))
        groups = {}
        for pair, candidate in zip(self.pairs, self.vectors):
            score = sum(value*candidate.get(key, 0) for key,value in vector.items())
            key = pair['answer'].strip()
            if score > groups.get(key, (0, None))[0]:
                groups[key] = (score, pair)
        return sorted(groups.values(), key=lambda item:item[0], reverse=True)

    def suggest(self, text, limit=3):
        """Suggestions require user selection; they are never automatic answers."""
        folded = fold(text)
        if re.search(r'[0-9+*/=<>]', folded) or re.search(r'\b(ve|ama|degil|istemiyorum|farki|arasindaki)\b', folded):
            return []
        words = content_words(text)
        if not words:
            return []
        results = []
        for score, pair in self.ranked(text):
            if score < .55:
                break
            target = content_words(pair['question'])
            overlaps = sum(any(q==t or (min(len(q),len(t))>=4 and (q.startswith(t) or t.startswith(q))) for t in target) for q in words)
            if overlaps / len(words) >= .5:
                results.append(pair)
            if len(results) == limit:
                break
        return results
