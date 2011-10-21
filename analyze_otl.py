# -*- coding: utf-8 -*

import csv
from story_analyzer.emotion import Emotion

emotion_tool = Emotion()

otl_reader = csv.reader(open('data/otl_stories.csv', 'r'))
otl_writer = csv.writer(open('data/otl_output.csv', 'w'), \
						quoting=csv.QUOTE_MINIMAL)
for story_id, story, over, on, under in otl_reader:
	valence_value, emotion_sequence, emotion_pattern = \
		emotion_tool.get_emotion_of_paragraph(story)
	otl_writer.writerow([str(valence_value), \
		u"".join(emotion_pattern), story, over, on, under])
