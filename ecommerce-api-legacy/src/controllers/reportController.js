const ReportService = require('../services/ReportService');

const reportController = {
    async getFinancialReport(req, res, next) {
        try {
            const report = await ReportService.getFinancialReport();
            res.status(200).json(report);
        } catch (err) {
            next(err);
        }
    },
};

module.exports = reportController;
