# -*- coding: UTF-8 -*- 
import jieba
import sys
import json
import glob
import os
import re
import jieba.analyse
from nltk.tag import StanfordPOSTagger

def parseDateType(indir,datetype='all'):
	if datetype == 'all':
		print 'select all'
		fileList = glob.glob(indir + '/*_2015-*')
	elif datetype.isdigit():
		print 'select month'
		fileList = glob.glob(indir + '/*_2015-' + datetype + '-*')
	else:
		print 'select date'
		fileList = glob.glob(indir + '/*_' + datetype + '*')
	return fileList

"""
	use 'Jieba(結巴)' to segment sentences, and stanford tagger to tagging terms
	https://github.com/fxsjy/jieba
	http://nlp.stanford.edu/software/tagger.shtml

	@dir: `rawdata` directory
	@month: specify month
"""
def segment_pos(dir='rawdata', datetype='all', outdir='nohref_seg'):
	jieba.set_dictionary('dict/dict.txt.big')
	for tag in loadTag():
		jieba.add_word(tag)
	
	chinese_postagger = StanfordPOSTagger('tagger/chinese-distsim.tagger', 'tagger/stanford-postagger.jar', encoding='utf-8')
	
	for file in parseDateType(dir,datetype):
		dirname, filename = os.path.split(file)
		head = filename.split('.')[0]
		outfile = outdir + '/' + head + '.txt'
		if os.path.isfile(outfile):
			print 'pass %s...' %head
			continue

		print 'segment %s ...' %head
		f = open(outfile, 'w')
		dataList = readJson(file)
		p = re.compile("http[s]?://.*\n")
		for data in dataList:
			content = data['content']
			content = re.sub(p, '', content)
			segList = jieba.cut(content)
			wordList, tagList = postagging(chinese_postagger, segList)
			for w, t in zip(wordList, tagList):
				f.write(w.encode('utf-8'))
				f.write(' ')
				f.write(t)
				f.write(' ')
			f.write('\n')
		f.close()

"""
	read a json file into dataList

	@file: a json file
"""
def readJson(file):
	dataList = []
	with open(file, 'r') as f:
		for line in f:
			dataList.append(json.loads(line))
	
	return dataList

def sortAllFile(jsonList, textList):
	def extract_time(json):
		try:
			return json[1]['datetime']
		except KeyError:
			return 0
	
	#ans = []
	#with open('result/2015-10-19_answer.txt', 'r') as f:
	#	for line in f:
	#		ans.append(int(line.strip()))
	
	sort_jsonList = sorted(enumerate(jsonList),key=extract_time)
	newTextList = []
	newJsonList = []
	newans = []
	for index, json in sort_jsonList:
		newTextList.append(textList[index])
		newJsonList.append(json)
		newans.append(ans[index])
	#with open('result/2015-10-19_answer_sort.txt', 'w') as f:
	#	for a in newans:
	#		f.write('%d\n' %a)
	return newJsonList, newTextList

"""
	load tags from news websites
	
"""
#TODO: cut the threshold
def loadTag():
	from collections import Counter
	for file in glob.glob('news_corpus/*.txt'):
		tagList = []
		with open(file, 'r') as f:
			for line in f:
				tagList.append(line.strip().split()[1])
	return tagList

"""
	tagging
	@chinese_postagger: model
	@segList: a list of terms segmented from a news article

"""
def postagging(chinese_postagger, segList):
	posList = chinese_postagger.tag(segList)
	wordList = []
	tagList = []
	for _, tp in posList:
		tp = tp.split('#')
		word = tp[0]
		tag = tp[1]
		wordList.append(word)
		tagList.append(tag)
	return wordList, tagList

"""
	split origin data into 'News' and 'Reply_News'
"""
def splitData(jsondir='rawdata', txtdir='nohref_seg', datetype='all'):
	for tmp in ['onlynews_pos', 'replynews_pos/', 'onlynews', 'replynews']:
		if not os.path.exists(tmp):
			os.makedirs(tmp)

	for jsonfile in parseDateType(jsondir,datetype):
		dirname, filename = os.path.split(jsonfile)
		head = filename.split('.')[0]
		newsposf = open('onlynews_pos/' + head + '.txt', 'w')
		replyposf = open('replynews_pos/' + head + '.txt', 'w')
			
		newsjsonf = open('onlynews/' + head + '.json', 'w')
		replyjsonf = open('replynews/' + head + '.json', 'w')

		dataList = readJson(jsonfile)
		linenum = 0
		with open(txtdir + '/' + head + '.txt', 'r') as f:
			for line in f:
				if line.strip() == '':
					continue
				if dataList[linenum]['title'].startswith("Re:"):
					replyposf.write(line)
					replyjsonf.write(json.dumps(dataList[linenum], ensure_ascii=False).encode('utf8') + "\n")
				else:
					newsposf.write(line)
					newsjsonf.write(json.dumps(dataList[linenum], ensure_ascii=False).encode('utf8') + "\n")
				linenum += 1
		newsposf.close()
		replyposf.close()
		newsjsonf.close()
		replyjsonf.close()

"""
	@dir: part-of-speech tagging directory (e.g. onlynews_pos)
	@month: month (e.g. 11)

"""
def filterData(indir='onlynews_pos', outdir='onlynews_select', datetype='all'):
	filteredTokens = ['媒體', '來源', '完整', '新聞標題', '報導', '記者', '連結', '網址', '新聞', '影音', '備註','自由','蘋果','ettoday','udn','tvbs','時報','日報','中央社','內文','QQ']

	if not os.path.exists(outdir):
		os.makedirs(outdir)
	def readStopWords(stopfile='stopwords.txt'):
		stopList = []
		with open(stopfile, 'r') as f:
			for line in f:
				stopList.append(line.strip())
		return stopList

	# filter one-length characters (exclude digits, english words)
	def filterOneLength(token):
		# calculate length of chinese
		utf8_length = len(entry)
		length = len(entry.decode('utf-8'))
		if length == 1 and utf8_length == 3:
			return True
		else:
			return False

	def filterStopWords(token):
		for stop in stopList:
			if token.find(stop) != -1:
				return True
	
		return False

	def filterUnImportantTokens(token):
		for ft in filteredTokens:
			if token.find(ft) != -1:
				return True
		
		return False


	stopList = readStopWords()
	for file in parseDateType(indir,datetype):
		dirname, filename = os.path.split(file)
		head = filename.split('.')[0]
		outfile = outdir + '/' + head + '.txt'
		selected = open(outfile, 'w')
		print 'process %s...' %file
		print 'store new documents in %s...' %outfile
		with open(file, 'r') as f:
			for line in f:
				wordtag = line.strip().split(' ')
				for idx,entry in enumerate(wordtag):
					entry = entry.lower()
					# word
					if idx % 2 == 0:
						if filterOneLength(entry):
							continue
						if filterStopWords(entry):
							continue
						if filterUnImportantTokens(entry):
							continue
						tag = wordtag[idx + 1]
						#if tag.startswith("N") or tag == "JJ" or tag.startswith("V"):		
						if tag == "NR" or tag == "NN":
							selected.write(entry)
							selected.write(' ')
				selected.write('\n')
	
def mergeData(indir='onlynews_select', outdir='vectordata', datetype='all'):

	if not os.path.exists(outdir):
		os.makedirs(outdir)

	def specifyOutFile(file, name):
		if file.split('.')[1] == 'txt':
			outfile = 'total_%s.txt' %name
		else:
			outfile = 'total_%s.json' %name
		return outfile

	fileList = parseDateType(indir,datetype)
	outfile = specifyOutFile(fileList[0], datetype)

	fileList.sort()
	total = open(outdir + '/' + outfile, 'w')
	for file in fileList:
		print 'merge %s ...' %file
		with open(file, 'r') as f:
			total.write(f.read())
	total.close()
	print 'files merge into %s/%s ...Done' %(outdir,outfile)
	

if __name__ == '__main__':
	if len(sys.argv) != 2:
		print 'usage: python main.py datetype' 
		print '(e.g. python main.py 10)'
		print 'note: process: segment_pos > splitData > filterData > mergeData'
		exit()
	
	datetype = sys.argv[1]

	""" This is for document segmentation and pos tagging """
	""" data is provided in directory 'nohref_seg' """	
	#segment_pos('rawdata', datetype=datetype)
	
	#splitData(datetype='all')
	filterData(indir='onlynews_pos', datetype='all')
	#merge final txt files into one single txt file
	mergeData(indir='onlynews_select', datetype=datetype)
	#merge corresponding json files into one single json file
	mergeData(indir='onlynews', datetype=datetype)
