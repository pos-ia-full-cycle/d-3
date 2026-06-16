const { Router } = require('express');
const userController = require('../controllers/userController');
const requireAdminAuth = require('../middlewares/auth');

const router = Router();

router.delete('/users/:id', requireAdminAuth, userController.deleteUser);

module.exports = router;
