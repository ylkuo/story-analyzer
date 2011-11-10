# -*- coding: utf-8 -*

import pickle
import simplenlp
from conceptnet_api import get_assertions
from collections import defaultdict
from nltk.corpus import stopwords

concept_stopwords = \
	['lots', 'much', 'many', 'too', 'someone', 'something', 'noun', \
	 'person', 'people', 'i', 'man']

class Context():
	def __init__(self, lang='en'):
		try:
			assertion_pickle = open('data/concept_assertion.pickle', 'rb')
			self.concept_assertions = pickle.load(assertion_pickle)
			assertion_pickle.close()
		except:
			self.concept_assertions = {}
		self.nlp = simplenlp.get(lang)
		self.stopwords = stopwords.words('english')
		self.stopwords.extend(concept_stopwords)

	def store_assertions(self):
		assertion_pickle = open('data/concept_assertion.pickle', 'wb')
		pickle.dump(self.concept_assertions, assertion_pickle)
		assertion_pickle.close()

	def update_assertion(self, concept, num_assertions=30):
		if concept not in self.concept_assertions.keys():
			assertions = get_assertions(concept, num_assertions=num_assertions)
			self.concept_assertions[concept] = assertions
			self.store_assertions()
			return assertions
		else:
			return self.concept_assertions[concept]

	def chaining(self, concept, final_arg1=[], final_arg2=[], \
			inter_arg1=[], inter_arg2=[], depth=0, chain=[]):
		assertions = self.update_assertion(concept)
		output = defaultdict(list)
		if depth == 2 or concept in concept_stopwords:
			return output
		for assertion in assertions:
			relation, arg1, arg2 = assertion
			if chain == []:
				output_chain = [assertion]
			else:
				output_chain = map(lambda x: x, chain)
				output_chain.append(assertion)
			if relation in final_arg1:
				if arg1 == concept and arg2 not in self.stopwords:
					output[arg2].append(output_chain)
			elif relation in final_arg2:
				if arg2 == concept and arg1 not in self.stopwords:
					output[arg1].append(output_chain)
			if relation in inter_arg1:
				if arg1 == concept and arg2 not in self.stopwords:
					for item in self.chaining(concept=arg2, depth=depth+1, \
							final_arg1=final_arg1, final_arg2=final_arg2, \
							inter_arg1=inter_arg1, inter_arg2=inter_arg2, \
							chain=output_chain).items():
						arg2, new_assertions = item
						for new in new_assertions:
							output[arg2].append(new)
			if relation in inter_arg2:
				if arg2 == concept and arg1 not in self.stopwords:
					for item in self.chaining(concept=arg1, depth=depth+1, \
							final_arg1=final_arg1, final_arg2=final_arg2, \
							inter_arg1=inter_arg1, inter_arg2=inter_arg2, \
							chain=output_chain).items():
						arg1, new_assertions = item
						for new in new_assertions:
							output[arg1].append(new)
		return output
		
	def get_location(self, concept):
		return self.chaining(concept, \
				final_arg1=['AtLocation', 'LocatedNear'], \
				inter_arg1=['IsA', 'UsedFor', 'CapableOf', 'ReceivesAction', \
							'DefinedAs'], \
				inter_arg2=['HasProperty'])

	def get_action(self, concept):
		return self.chaining(concept, \
				final_arg1=['UsedFor', 'CapableOf', 'HasSubevent', \
							'HasFirstSubevent', 'HasLastSubevent', \
							'HasPrerequisite', 'Causes', \
							'CausesDesire', 'ReceivesAction'], \
				inter_arg1=['IsA', 'AtLocation', 'CapableOf', 'DefinedAs'], \
				inter_arg2=['HasProperty'])

	def get_property(self, concept):
		return self.chaining(concept, \
				final_arg1=['HasProperty'], \
				inter_arg1=['IsA', 'UsedFor', 'CapableOf' \
							'ReceivesAction', 'DefinedAs'])

	def get_object(self, concept):
		return self.chaining(concept, \
				final_arg1=['IsA', 'HasA', 'MadeOf', 'SymbolOf'], \
				final_arg2=['PartOf', 'UsedFor', 'AtLocation', \
							'CreatedBy', 'ReceivesAction', \
							'HasProperty', 'LocatedNear'], \
				inter_arg1=['CapableOf', 'MotivatedByGoal', \
							'CauseDesire', 'DefinedAs'])

	def get_actor(self, concept):
		return self.chaining(concept, \
				final_arg2=['CapableOf', 'Desires'], \
				inter_arg1=['IsA', 'HasA', 'UsedFor', 'CreatedBy', \
							'MotivatedByGoal', 'Causes', \
							'CauseDesire', 'DefinedAs', \
							'ReceivesAction'], \
				inter_arg2=['PartOf', 'AtLocation', 'HasProperty', \
							'SymbolOf', 'LocatedNear'])

	def build_context(self, sentence):
		context = defaultdict(dict)
		concepts = self.nlp.extract_concepts(
            sentence, max_words=2, check_conceptnet=True)
		for token in concepts:
			token = self.nlp.normalize(token).strip(',!~').strip()
			if token in self.stopwords or token in context.keys():
				continue
			context[token]['location'] = self.get_location(token)
			context[token]['action'] = self.get_action(token)
			context[token]['property'] = self.get_property(token)
			context[token]['object'] = self.get_object(token)
			context[token]['actor'] = self.get_actor(token)
		return context


if __name__ == '__main__':
	context = Context()
	concept = 'unhealthy'
	print context.get_location(concept)
	print context.get_action(concept)
	print context.get_property(concept)
	print context.get_object(concept)
	print context.get_actor(concept)
	print context.build_context('A hotdog anywhere is a hit')
