var express = require('express');
var router = express.Router();

function topic(req, res) {
	var modelCluster = require('../models/Cluster');

	modelCluster
	.getCluster({
		date: '2015-10-19',
		filename: '/home/fishwish/work/web/sample/ptt_news_2015-10-19_each.hotterm'
	})
	.then(function(result) {
		res.render('index', {
			ctrl_date:  '2015-10-19',
			ctrl_topics: result
		});
	})
	.done();
};
/* GET home page. */
router.get('/', topic);
module.exports = router;
