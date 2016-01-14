import math
import sys

def readLabel(file):
	ansList = []
	with open(file, 'r') as f:
		for line in f:
			ansList.append(int(line.strip()))
	return ansList

def costructDict(ansList, predList):
	ansDict = {}
	predDict = {}
	news_idx = 0
	for ans,pred in zip(ansList, predList):
		if ans in ansDict:
			ansDict[ans].add(news_idx)
		else:
			ansDict[ans] = {news_idx}

		if pred in predDict:
			predDict[pred].add(news_idx)
		else:
			predDict[pred] = {news_idx}

		news_idx += 1
	return ansDict, predDict, news_idx

def calEntropy(ansDict, predDict, num_doc):
	cluster_entropy = {}
	for class_i, class_set in ansDict.iteritems():
		for cluster_j, cluster_set in predDict.iteritems():
			prob_ij = len(class_set & cluster_set) / float(len(class_set))
			if prob_ij == 0.0:
				continue
			if cluster_j in cluster_entropy:
				cluster_entropy[cluster_j] += -(prob_ij * math.log(prob_ij))
			else:
				cluster_entropy[cluster_j] = -(prob_ij * math.log(prob_ij))
	entropy_all = 0.0
	for cluster_j, cluster_set in predDict.iteritems():
		entropy_all += cluster_entropy[cluster_j] * len(cluster_set) / float(num_doc)
	return entropy_all

def calR_P_F1(ansDict, predDict, num_doc):
	recall = {}
	precision = {}
	for class_i, class_set in ansDict.iteritems():
		recall[class_i] = {}
		precision[class_i] = {}
		for cluster_j, cluster_set in predDict.iteritems():
			recall[class_i][cluster_j] = len(class_set & cluster_set) / float(len(cluster_set))
			precision[class_i][cluster_j] = len(class_set & cluster_set) / float(len(class_set))
	
	f1 = {}
	for class_i, cluster_dict in recall.iteritems():
		f1[class_i] = {}
		for cluster_j, r in cluster_dict.iteritems():
			p = precision[class_i][cluster_j]
			if r == 0.0 or p == 0.0:
				f1[class_i][cluster_j] = 0.0
			else:
				f1[class_i][cluster_j] = (2*r*p)/float(r+p)

	final_r = 0.0
	final_p = 0.0
	final_f1 = 0.0
	for class_i, cluster_dict in recall.iteritems():
		recall_i = max(cluster_dict.values())
		precision_i = max(precision[class_i].values())
		f1_i = max(f1[class_i].values())
		final_r += recall_i * len(ansDict[class_i]) / float(num_doc)
		final_p += precision_i * len(ansDict[class_i]) / float(num_doc)
		final_f1 += f1_i * len(ansDict[class_i]) / float(num_doc)

	return final_r, final_p, final_f1

if __name__ == '__main__':
	ansList = readLabel('result/2015-10-19_answer_sort.txt')
	predList = readLabel(sys.argv[1])
	ansDict, predDict, num_doc = costructDict(ansList, predList)
	entropy = calEntropy(ansDict, predDict, num_doc)
	r, p, f1 = calR_P_F1(ansDict, predDict, num_doc)

	print 'entropy: %.4f' %entropy
	print 'recall: %.4f, precision: %.4f, f-measure: %.4f' %(r,p,f1)

