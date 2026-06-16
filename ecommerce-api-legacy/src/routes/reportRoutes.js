const { Router } = require('express');
const reportController = require('../controllers/reportController');
const requireAdminAuth = require('../middlewares/auth');

const router = Router();

router.get('/admin/financial-report', requireAdminAuth, reportController.getFinancialReport);

module.exports = router;
