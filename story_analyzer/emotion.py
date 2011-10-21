# -*- coding: utf-8 -*

import csv, os
from conceptnet.analogyspace import conceptnet_2d_from_db
from csc.divisi.blend import Blend
from csc.util.persist import get_picklecached_thing
from simplenlp import get_nl

wordnet_affect_category = [
	'positive-emotion', 'negative-emotion', \
	'ambiguous-emotion', 'neutral-emotion', \
	'emotion', 'affective-state', 'mental-state', \
	'general-dislike', 'positive-fear', 'negative-fear', \
	'ambiguous-fear', 'positive-concern', 'negative-concern', \
	'neutral-unconcern', 'negative-unconcern', \
	'positive-suspense', 'negative-suspense', \
	'positive-expectation', 'ambiguous-expectation', \
	'negative-agitation', 'ambiguous-agitation', \
	'positive-languor', 'neutral-languor', 'regret-sorrow', \
	'positive-hope', 'satisfaction-pride', 'joy-pride', \
	'fear-intimidation', 'general-gaiety']

path = os.path.abspath(__file__).replace(\
		os.path.basename(__file__), '').replace(\
		__file__.split('/')[-2]+'/', '')

class Emotion():
	def __init__(self, emoticon_file=path+'/data/emoticons.csv', \
			affect_wordnet_file=path+'/data/affectiveWNmatrix.pickle'):
		# Build emoticon dictionary
		self.emoticon = {}
		emoticon_reader = csv.reader(open(emoticon_file, 'r'))
		for emoticon, meaning in emoticon_reader:
			self.emoticon[emoticon.decode('utf-8')] = meaning
		self.emoticon_list = self.emoticon.keys()
		# Create blending of affect WordNet and ConceptNet
		cnet = conceptnet_2d_from_db('en')
		affectwn_raw = get_picklecached_thing(affect_wordnet_file)
		affectwn_normalized = affectwn_raw.normalized()
		theblend = Blend([affectwn_normalized, cnet])
		self.affectwn = theblend.svd()
		# Get natural language processing tool
		self.nl = get_nl('en')

	def eval_emotion_of_concept(self, concept):
		if concept in self.emoticon_list:
			concept = self.emoticon[concept]
		pos = self.affectwn.u['positive-emotion', :].hat()
		neg = self.affectwn.u['negative-emotion', :].hat()
		neu = self.affectwn.u['neutral-emotion', :].hat()
		amb = self.affectwn.u['ambiguous-emotion', :].hat()
		try:
			concept_vec = self.affectwn.u[concept, :].hat()
			return (concept_vec*pos, concept_vec*neg, \
					concept_vec*neu, concept_vec*amb)
		except KeyError:
			values = []
			for token in concept.split():
				try:
					concept_vec = self.affectwn.u[token, :].hat()
					values.append((concept_vec*pos, concept_vec*neg, \
							concept_vec*neu, concept_vec*amb))
				except KeyError:
					continue
			max_value = None
			max_sum = 0
			for value in values:
				if sum(value) > max_sum:
					max_value = value
					max_sum = sum(value)
			if max_value != None:
				return max_value
			return (0,0,0,0)

	def get_emoticon_from_sentence(self, sentence):
		found_emoticon = []
		for token in sentence.split():
			if token in self.emoticon_list:
				found_emoticon.append(token)
		return found_emoticon

	def get_emotion_of_sentence(self, sentence):
		found_emoticon = self.get_emoticon_from_sentence(sentence)
		for emoticon in found_emoticon:
			sentence = sentence.replace(emoticon, self.emoticon[emoticon])
		concepts = self.nl.extract_concepts(
			sentence, max_words=2, check_conceptnet=True)
		remove = []
		for concept in concepts:
			if len(concept.split()) == 2:
				remove.extend(concept.split())
		for concept in remove:
			if concept in concepts:
				concepts.remove(concept)
		emotion_eval = map(lambda x: self.eval_emotion_of_concept(x), concepts)
		return self.combine_emotion(emotion_eval)

	def combine_emotion(self, emotion_eval_tuples):
		final_value = []
		for pos, neg, neu, amb in emotion_eval_tuples:
			if pos > 0 and pos > neg and (pos > neu or pos > 0.4) and pos > amb:
				final_value.append(pos)
			elif neg > 0 and neg > pos and \
					(neg > neu or neg > 0.4) and neg > amb:
				final_value.append(neg*(-1))
			elif amb > 0 and amb > pos and amb > neg and amb > neu:
				pos_count = 0
				neg_count = 0
				for value in final_value:
					if value > 0: pos_count += 1
					elif value < 0: neg_count += 1
				if pos_count > neg_count:
					final_value.append(pos)
				elif neg_count > pos_count:
					final_value.append(neg*(-1))
				else:
					final_value.append(0)
			else:
				final_value.append(0)
		return sum(final_value)

	def get_emotion_of_paragraph(self, paragraph):
		found_emoticon = self.get_emoticon_from_sentence(paragraph)
		for emoticon in found_emoticon:
			paragraph = paragraph.replace(emoticon, self.emoticon[emoticon])
		emotion_sequence = []
		emotion_pattern = []
		token_count = 0
		for sentence in \
				paragraph.replace('/', ' ').replace(\
				'!', '.').replace('?', '.').split('.'):
			if sentence.strip() == '':
				continue
			emotion_token = u'x'
			emotion_sequence.append(self.get_emotion_of_sentence(sentence))
			if emotion_sequence[token_count] > 0.4:
				emotion_token = u'p'
			elif emotion_sequence[token_count] < -0.4:
				emotion_token = u'n'
			if token_count == 0:
				emotion_pattern.append(emotion_token)
			elif emotion_token != emotion_pattern[-1]:
				emotion_pattern.append(emotion_token)
			token_count += 1
		return (sum(emotion_sequence), emotion_sequence, emotion_pattern)

if __name__ == '__main__':
	emotion = Emotion()

	paragraph = u"I met a guy in a child pshyciatry unit this past week. We both struggle from depression but seem to make eachother really happy. He calls me multiple times everyday and says he loves me. I really like him but I'm afraid this may be moving too fast."
	print emotion.get_emotion_of_paragraph(paragraph)

	paragraph = u"I asked my gf 2 marry me by chanching my facebook status to engaged after we'd dinner. She accepted n was so excited. A weeks later i met another girl n a picture of us was pubished, so my gf delted me from her facebook list n neva seen her again. :("
	print emotion.get_emotion_of_paragraph(paragraph)
