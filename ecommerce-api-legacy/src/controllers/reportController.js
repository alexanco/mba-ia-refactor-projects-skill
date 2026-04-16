const ReportService = require('../services/reportService');

class ReportController {
    static getFinancialReport(req, res, next) {
        try {
            const report = ReportService.getFinancialReport();
            return res.json(report);
        } catch (err) {
            next(err);
        }
    }
}

module.exports = ReportController;
