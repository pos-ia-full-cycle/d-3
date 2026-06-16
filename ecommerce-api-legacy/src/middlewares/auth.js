const config = require('../config');

function requireAdminAuth(req, res, next) {
    const authHeader = req.headers.authorization;
    if (!authHeader || authHeader !== `Bearer ${config.adminToken}`) {
        return res.status(401).json({ error: 'Unauthorized' });
    }
    next();
}

module.exports = requireAdminAuth;
