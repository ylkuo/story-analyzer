# -*- coding: utf-8 -*

import pickle
import simplejson
from collections import defaultdict
from story_analyzer.context import Context

sensitive_pickle_file = 'data/privacy/sensitive_context.pickle'
profile_pickle_file = 'data/privacy/profile_danny.pickle'
sensitive_word_file = 'data/privacy/sensitive_words.txt'
profile_data_file = 'data/privacy/Danny_json_out'

context = Context()

# build representation for sensitive concepts
try:
	pkl_file = open(sensitive_pickle_file, 'rb')
	sensitive_context = pickle.load(pkl_file)
	pkl_file.close()
except:
	fp = open(sensitive_word_file, 'r')
	sensitive_context = {}
	for line in fp:
		line = line.strip()
		sensitive_set = set()
		non_sensitive_set = set()
		if line != '':
			sensitive_seeds, non_sensitive_seeds = line.split('|')
			for concept in sensitive_seeds.split(','):
				if concept == '':
					continue
				new_context = context.build_context(concept)[concept]
				sensitive_context[concept] = new_context
				for category in sensitive_context[concept].keys():
					for matched_concept in sensitive_context[concept][category].keys():
						sensitive_set.add(matched_concept)
			for concept in non_sensitive_seeds.split(','):
				if concept == '':
					continue
				new_context = context.build_context(concept)[concept]
				for category in new_context.keys():
					for matched_concept in new_context[category].keys():
						non_sensitive_set.add(matched_concept)
	# remove concepts in context of nonsensitive concept
	for concept in sensitive_context.keys():
		for category in sensitive_context[concept].keys():
			for matched_concept in sensitive_context[concept][category].keys():
				if (matched_concept in sensitive_set) and (matched_concept in non_sensitive_set):
					del sensitive_context[concept][category][matched_concept]
	fp.close()
	output = open(sensitive_pickle_file, 'wb')
	pickle.dump(sensitive_context, output)
	output.close()

# read updates and track profile to give explanation
try:
	pkl_file = open(profile_pickle_file, 'rb')
	profile = pickle.load(pkl_file)
	pkl_file.close()
except:
	fp = open(profile_data_file, 'r')
	result = simplejson.load(fp)
	profile = defaultdict(dict)
	for post in result['results']['bindings']:
		post_context = context.build_context(post['message']['value'])
		for concept in post_context.keys():
			for sensitive_concept in sensitive_context.keys():
				for category in post_context[concept].keys():
					category_context1 = post_context[concept][category].keys()
					category_context2 = \
						sensitive_context[sensitive_concept][category].keys()
					for token in category_context1:
						if token in category_context2:
							if token not in profile[concept].keys():
								profile[concept][token] = []
							profile[concept][token].extend(\
								post_context[concept][category][token])
	fp.close()
	output = open(profile_pickle_file, 'wb')
	pickle.dump(profile, output)
	output.close()

# print reason
category_count = defaultdict(int)
for extracted_concept in profile.keys():
	for matched_concept in set(profile[extracted_concept].keys()):
		for sensitive_concept in sensitive_context.keys():
			for category in sensitive_context[sensitive_concept]:
				if matched_concept in \
					sensitive_context[sensitive_concept][category].keys() \
					and len(profile[extracted_concept][matched_concept]) > 1:
					output_profile_reason = []
					output_matched_reason = []
					print '"%s" is related to "%s" because of "%s"' % \
							(extracted_concept, sensitive_concept, matched_concept)
					for reason in profile[extracted_concept][matched_concept]:
						if reason not in output_profile_reason:
							print reason
							output_profile_reason.append(reason)
					print 'and'
					for reason in sensitive_context[sensitive_concept][category][matched_concept]:
						if reason not in output_matched_reason:
							print reason
					print '-------------------------------------'
					category_count[sensitive_concept] += 1
print category_count
