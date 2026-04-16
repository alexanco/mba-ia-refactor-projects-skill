const express = require('express');
const router = express.Router();
const ReportController = require('../controllers/reportController');

router.get('/financial-report', ReportController.getFinancialReport);

module.exports = router;
