#encoding=UTF-8
import json
import sys
import re
import math
import os
import itertools
from main import readJson
from cluster_analysis import readText, readCluster, outputCluster
from gensim import corpora, similarities
from subprocess import call
from datetime import datetime, timedelta

sourceList = {	'蘋果': 'apple', 
				'自由': 'ltn',
				'東森':'ettoday',
				'中央社':'cna',
				'風傳媒':'storm',
				'大紀元':'epochtimes',
				'IThome':'IThome',
				'聯合':'udn',
				'中時':'chinatimes'
			}

def getSource(data):
	content = data['content']
	urls = re.findall("http[s]?://.*\n",content)
	print urls
	index1 = content.find("1.媒體來源:".decode('utf-8'))
	index2 = content.find("2.完整新聞標題".decode('utf-8'))
	print re.sub('\n','',content[index1:index2])

class TopicDetection():
	def __init__(self):
		self.dictionary = None
		self.topic = dict()
		self.corpus = []
		self.corpusvector = []
		self.doc_denom = []
		self.tc = {}
		self.nutrition = {}
		self.newcoming_topic = {}
		self.meanCluster = {}
	
	def constructTermCount(self,update=False,newDocList=None):
		if update:
			tmpcorpus = newDocList
		else:
			tmpcorpus = self.corpus
		for doc in tmpcorpus:
			for (term,count) in doc:
				if term in self.tc:
					self.tc[term] += count
				else:
					self.tc[term] = count
		return
	
	def getDictId2Token(self):
		id2token = {}
		for (token,id) in self.dictionary.token2id.iteritems():
			id2token[id] = token
		return id2token

	def getDocCount(self,tokenid):
		return self.dictionary.dfs[tokenid]
	
	def getTermCount(self,tokenid):
		return self.tc[tokenid]

	def getTotalCount(self):
		return sum(self.tc.values())

	def getDocLength(self, docid):
		doclength = 0
		for _, count in self.corpus[docid]:
			doclength += count
		return doclength

	def splitDoc(self,textList):
		newList = []
		for text in textList:
			new = text.strip().split(' ')
			newList.append(new)
		return newList

	def term_idf(self,update=False,newDocList=None):
		totaldoc = len(self.corpus)
		if update:
			tmpcorpus = newDocList
		else:
			tmpcorpus = self.corpus

		for docid, doc in enumerate(tmpcorpus):
			if update:
				docid += totaldoc - len(tmpcorpus)
			doclength = float(self.getDocLength(docid))
			docvector = {}
			denom = 0.0
			for (termid, count) in doc:
				weight = (count / doclength)  * math.log((totaldoc+1)/float(self.getDocCount(termid)))
				docvector[termid] = weight
				denom += weight * weight
			self.doc_denom.append(math.sqrt(denom))
			self.corpusvector.append(docvector)
		return
	
	def termweight(self,update=False,newDocList=None):
		totalc = self.getTotalCount()
		if update:
			tmpcorpus = newDocList
		else:
			tmpcorpus = self.corpus

		for doc in tmpcorpus:
			docvector = {}
			denom = 0.0
			for (termid, count) in doc:
				weight = count * math.log((totalc+1)/float(self.getTermCount(termid) + 0.5))
				docvector[termid] = weight
				denom += weight * weight
			self.doc_denom.append(math.sqrt(denom))
			self.corpusvector.append(docvector)
		return

	def writeDictionary(self,filename):
		if self.dictionary is None:
			return
		sorted_dict = sorted(self.dictionary.token2id.items(), key=lambda x:x[1])
		with open(filename, 'w') as f:
			with open(filename,'w') as f:
				for (term,id) in sorted_dict:
					f.write(term.encode('utf-8'))
					f.write(' %d' %id)
					f.write('\n')
		return

	def writeCorpus(self, filename, corpus):
		with open(filename,'w') as f:
			for doc in corpus:
				for (term,count) in doc:
					f.write('%d %d ' %(term,count))
				f.write('\n')
		return	

	def writeTermWeight(self, filename):
		num_doc = 0
		num_term = len(self.dictionary.values())
		num_nonzero = 0
		for doc in self.corpusvector:
			num_doc += 1
			num_nonzero += len(doc)
		
		with open(filename, 'w') as f:
			f.write('%d %d %d\n' %(num_doc,num_term,num_nonzero))
			for docvector in self.corpusvector:
				for termid, weight in docvector.iteritems():
					f.write('%d %.4f ' %((termid+1), weight))
				f.write('\n')
		return

	def constructTermVector(self, textList, dictfile, outfile=None, update=False):
		newList = self.splitDoc(textList)
		if self.dictionary is None:
			self.dictionary = corpora.Dictionary(newList)
			self.dictionary.save(dictfile)
			tokenidfile = dictfile.split('.')[0] + '.clabel'
			self.writeDictionary(tokenidfile)

		else:
			#self.dictionary = corpora.Dictionary.load(dictfile)
			self.dictionary.add_documents(newList)
			
		#id2token = self.getDictId2Token(self.dictionary)
		#get term vectors of newList
		for text in newList:
			self.corpus.append(self.dictionary.doc2bow(text))
		#update term count
		self.constructTermCount(update=update,newDocList=[self.corpus[-1]])
		#calculate term weight
		self.termweight(update=update,newDocList=[self.corpus[-1]])
		#self.term_idf(update=update,newDocList=[self.corpus[-1]])
		#output
		if outfile is not None:
			self.writeTermWeight(outfile)
	
	def cosine_similarity(self, doc1, doc2, doc1_norm, doc2_norm):
		sim = 0.0
		for (termid, weight) in doc1.iteritems():
			if termid in doc2:
				sim += weight * doc2[termid]
		sim /= (doc1_norm * doc2_norm)
		return sim

	def calMeanCluster(self, topicid):
		for idx2 in docIndexList:
			doc2_vector = self.corpusvector[idx2]
			doc2_norm = self.doc_denom[idx2]
			for (term, weight) in doc2_vector.iteritems():
				if term in mean_cluster:
					mean_cluster[term] += weight/float(doc2_norm)
				else:
					mean_cluster[term] = weight/float(doc2_norm)
		return mean_cluster

	def updateMeanCluster(self, topicid, newDocIndex):
		doc1_vector = self.corpusvector[newDocIndex]
		doc1_norm = self.doc_denom[newDocIndex]

		#update cluster's mean
		if topicid in self.meanCluster:
			num_doc = len(self.topic[topicid])
			for (term, weight) in doc1_vector.iteritems():
				if term in self.meanCluster[topicid]:
					self.meanCluster[topicid][term] += (weight / float(doc1_norm))
				else:
					self.meanCluster[topicid][term] = (weight / float(doc1_norm))
		#add first term weight into cluster (normalized)
		else:
			self.meanCluster[topicid] = {}
			for (term, weight) in doc1_vector.iteritems():
				self.meanCluster[topicid][term] = (weight / float(doc1_norm))
		return

	def track_meancluster(self, topicid, newDocIndex, newDocTitle, sim_threshold=0.225):
		#calculate cluster's mean

		sim = 0.0
		doc1_vector = self.corpusvector[newDocIndex]
		doc1_norm = self.doc_denom[newDocIndex]

		cluster_vector = self.meanCluster[topicid]
		cluster_num = len(self.topic[topicid])

		for (term, weight) in doc1_vector.iteritems():
			if term in cluster_vector:
				sim += (cluster_vector[term]/float(cluster_num)) * (weight/float(doc1_norm))
		
		if sim > sim_threshold:
			return (True, sim)
		else:
			return (False, sim)

	def calNutrition(self):
		for topicidx in self.newcoming_topic:
			#num_new = self.newcoming_topic[topicidx]
			#if topicidx in self.topic:
			#	num_old = len(self.topic[topicidx])
			#else:
			#	self.nutrition[topicidx] = num_new
			#	continue
			if topicidx in self.nutrition:
				#self.nutrition[topicidx] += (num_new + num_old)/float(num_old)
				#self.nutrition[topicidx] += math.log(self.newcoming_topic[topicidx])
				self.nutrition[topicidx] = self.newcoming_topic[topicidx]
			else:
				#self.nutrition[topicidx] = (num_new + num_old)/float(num_old)
				#self.nutrition[topicidx] = math.log(self.newcoming_topic[topicidx])
				self.nutrition[topicidx] = self.newcoming_topic[topicidx]
		return

	def cleanCluster(self, numtopic=100):
		print 'current document count: %d' %(len(self.corpus))
		print 'current topic count: %d' %(len(self.topic))
		self.calNutrition()
		sorted_nutrition = sorted(self.nutrition.items(), key=lambda x:x[1])

		if len(self.topic) < numtopic:
			num_remove = 0
		
		else:
			num_remove = len(self.topic) - numtopic
			print '%d to remove\n' %num_remove
			for tmp, (topicidx, nutr) in enumerate(sorted_nutrition):
				if tmp >= num_remove:
					break
				self.nutrition.pop(topicidx, None)
				self.topic.pop(topicidx, None)
				self.meanCluster.pop(topicidx, None)
				if topicidx not in self.topic:
					print '%d removed.' %topicidx
				else:
					print '%d error.' %topicidx
		# clear dictionary new coming topic
		self.newcoming_topic = {}
		
		self.showTopics()
		return
	
	def increNewComing(self, tid):
		if tid in self.newcoming_topic:
			self.newcoming_topic[tid] += 1
		else:
			self.newcoming_topic[tid] = 1
		return

	def assignCluster(self, title, threshold):
		if len(self.topic) == 0:
			self.topic[0] = [(title, 0)]
			self.newcoming_topic[0] = 1
			self.updateMeanCluster(0, 0)
			return
		max_topic_id = max(self.topic.keys())
		mapid = -1
		oldDocIndexList = []
		oldDocTitleList = []
		newDocIndex = len(self.corpus) - 1
		select_topic_sim = 0.0
		
		for topicid in self.topic:
			isOldTopic, sim = self.track_meancluster(topicid, newDocIndex, title, sim_threshold=threshold)

			if isOldTopic and sim > select_topic_sim:
				mapid = topicid
				select_topic_sim = sim	

		if mapid == -1:
			mapid = max_topic_id + 1
			self.updateMeanCluster(mapid, newDocIndex)
			self.topic[mapid] = [(title, newDocIndex)]
			self.increNewComing(mapid)
			#print 'new topic %d' %mapid
			#print 'new title:', title
			#print 'sim: %.4f' %sim
			return False
		else:
			#print 'assign to old topic %d' %topicidx
			#print 'new title:', title
			#print 'sim: %.4f' %sim
			self.updateMeanCluster(mapid, newDocIndex)
			self.topic[mapid].append((title,newDocIndex))
			self.increNewComing(mapid)
			return True

		#self.showTopics()
	
	def showTopics(self,outfile='tmptopic.txt'):
		print 'current topic num: %d\n' %len(self.topic)
		with open(outfile, 'w') as f:
			for topicidx in self.topic:
				line = 'Cluster %d:\n' %topicidx
				f.write(line)
				for title, docidx in self.topic[topicidx]:
					f.write(title.encode('utf-8'))
					f.write('\n')
		return

	def writeTopicIndex(self,outfile):
		ansDict = {}
		for tid in self.topic:
			for title, docidx in self.topic[tid]:
				ansDict[docidx] = tid
		sorted_ans = sorted(ansDict.items(), key=lambda x:x[0])
		with open(outfile, 'w') as f:
			for docidx, topicid in sorted_ans:
				print '%d, topic %d' %(docidx, topicid)
				f.write('%d\n' %topicid)
		return

	def extractHotTerm(self, outfile):
		id2token = self.getDictId2Token()
		self.hotterm = {}
		sorted_topicRank = sorted(self.nutrition.items(), key=lambda x:x[1], reverse=True)
		out = open(outfile, 'w')
		for tid, _ in sorted_topicRank:
			score_vector = {}
			out.write('Cluster %d: ' %tid)
			for title, docidx in self.topic[tid]:
				for termid, weight in self.corpusvector[docidx].iteritems():
					if termid in score_vector:
						score_vector[termid] += weight/float(self.doc_denom[docidx])
					else:
						score_vector[termid] = weight/float(self.doc_denom[docidx])
			sorted_score = sorted(score_vector.items(), key=lambda x:x[1], reverse=True)
			for termid, score in sorted_score[:10]:
				out.write(id2token[termid].encode('utf-8'))
				out.write(' ')
			out.write('\n')
			for title, _ in self.topic[tid]:
				out.write(title.encode('utf-8'))
				out.write('\n')
			out.write('\n')
		out.close()
		return

if __name__ == '__main__':
	#from main import parseDateType
	#jsonfileList = parseDateType('onlynews_sort',datetype='10')
	#jsonfileList.extend(parseDateType('onlynews_sort',datetype='11'))
	#jsonfileList.sort()
	#textfileList = parseDateType('onlynews_select_sort',datetype='10')
	#textfileList.extend(parseDateType('onlynews_select_sort',datetype='11'))
	#textfileList.sort()
	jsonfileList = ['onlynews_sort/ptt_news_2015-10-19.json']
	textfileList = ['onlynews_select_sort/ptt_news_2015-10-19.txt']
	idx = 0
	td_first = TopicDetection()
	first_corpus = True
	last_datetime = ''
	for jsonfile, textfile in zip(jsonfileList, textfileList):
		dataList = readJson(jsonfile)
		textList = readText(textfile)
		print textfile
		head, tail = os.path.split(textfile)
		tail = tail.split('.')[0]
		matfile = "result/" + tail + ".mat"
		labelfile = "result/" + tail + "_label.txt"
		gendictfile = "gensim_tmp/" + tail + ".dict"
		#on-the-fly
		finalpredfile = "result/" + tail + "_mean.pred"
		finaltopicfile = "result/" + tail + "_mean.topic"
		for idx in range(len(textList)):
			newtext = [textList[idx]]
			if first_corpus and idx == 0:
				td_first.constructTermVector(newtext, gendictfile, outfile=matfile, update=False)
				last_datetime = datetime.strptime(dataList[idx]['datetime'], '%Y-%m-%d %H:%M:%S')
			else:
				td_first.constructTermVector(newtext, gendictfile, update=True)

			title = dataList[idx]['title']
			cur_datetime = datetime.strptime(dataList[idx]['datetime'], '%Y-%m-%d %H:%M:%S')
			
			isold = td_first.assignCluster(title, float(sys.argv[1]))
			print title, '-', cur_datetime, '/', last_datetime
			if last_datetime + timedelta(hours=12) < cur_datetime:
				last_datetime = last_datetime + timedelta(hours=12)
				td_first.cleanCluster()
			
		td_first.showTopics(outfile=finaltopicfile)
		td_first.writeTopicIndex(finalpredfile)
		if first_corpus:
			first_corpus = False
		idx += 1
	td_first.extractHotTerm('result/' + tail + '_mean.hotterm')
