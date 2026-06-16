const logger = require('../utils/logger');

function errorHandler(err, req, res, next) {
    const statusCode = err.statusCode || 500;

    if (statusCode >= 500) {
        logger.error(`Unhandled error: ${err.message}\n${err.stack}`);
        return res.status(500).json({ error: 'Erro interno do servidor' });
    }

    res.status(statusCode).json({ error: err.message });
}

module.exports = errorHandler;
