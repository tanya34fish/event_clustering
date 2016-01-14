var Q = require('q')
  , fs = require('fs')
  ;

exports.getCluster = function(options) {
	var deferred = Q.defer();
	var filename = options['filename'];
	var date = options['date'];
	var num = options['num'] || 100;
	fs.readFile(filename, function(err, file) {
		if (err) {
			return deferred.reject(err);
		}

		var result = [];
		var clusterlines = file.toString().split('\n\n');
		for (var i=0; i<clusterlines.length; i++) {
			var lines = clusterlines[i].toString().split('\n');
			var hotterm = lines[0]
			var titles = []
			for (var j=1; j<lines.length; j++) {
				titles.push(lines[j]);
			}
			result.push({
				cluster_hotterm: hotterm,
				cluster_doc: titles
			});
		}

		deferred.resolve(result);
	})
	return deferred.promise;

};

