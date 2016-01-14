import sys
import json
from main import readJson

def readCluster(file):
	with open(file, 'r') as f:
		result = f.read()
		result = result.strip().split('\n')
	labelList = [int(x) for x in result]
	return labelList

def readText(file):
	result = []
	with open(file, 'r') as f:
		for line in f:
			result.append(line)
	return result

def showCluster(jsonList, labelList):
	cluster_dict = {}
	for l in set(labelList):
		cluster_dict[l] = []

	index = 0
	for data, label in zip(jsonList, labelList):
		cluster_dict[label].append((data['title'],index))
		index += 1
	return cluster_dict

def outputCluster(textList, jsonList, labelList, outfile):
	cluster_dict = showCluster(jsonList, labelList)
	with open(outfile, 'w') as f:
		for label, titleList in cluster_dict.iteritems():
			f.write('Cluster %d:\n' %label)
			for (title,idx) in titleList:
				print title, idx
				f.write('%d ' %idx)
				f.write(title.encode('utf-8'))
				f.write('\n')
			f.write('\n')
	return cluster_dict

def extractCluster(textList, jsonList, labelList, outtextfile, outjsonfile):
	
	cluster_dict = showCluster(jsonList, labelList)
	max_label = -1
	max_length = -1
	for label, titleList in cluster_dict.iteritems():
		if len(titleList) > max_length:
			max_label = label
			max_length = len(titleList)
	outtext = open(outtextfile, 'w')
	outjson = open(outjsonfile, 'w')
	for (title,idx) in cluster_dict[max_label]:
		outtext.write('%s' %(textList[idx]))
		outjson.write(json.dumps(jsonList[idx], ensure_ascii=False).encode('utf8') + "\n")
	outtext.close()
	outjson.close()

if __name__ == '__main__':
	if len(sys.argv) != 4:
		print 'usage: python cluster_analysis.py textfile jsonfile outfile'
		print '(e.g.) python cluster_analysis.py vectordata/total_10.txt vectordata/total_10.json cluster_title_10.txt'
		exit()

	clusterfile = 'cluster_label.txt'
	textfile = sys.argv[1]
	jsonfile = sys.argv[2]
	outfile = sys.argv[3]

	labelList = readCluster(clusterfile)
	textList = readText(textfile)
	jsonList = readJson(jsonfile)
	outputCluster(textList, jsonList, labelList, outfile)
	#extractCluster(textList, jsonList, labelList, 'vectordata/new.txt', 'vectordata/new.json')
