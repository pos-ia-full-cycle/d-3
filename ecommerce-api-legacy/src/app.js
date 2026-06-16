const express = require('express');
const config = require('./config');
const { initDb } = require('./db');
const logger = require('./utils/logger');

const checkoutRoutes = require('./routes/checkoutRoutes');
const reportRoutes = require('./routes/reportRoutes');
const userRoutes = require('./routes/userRoutes');
const errorHandler = require('./middlewares/errorHandler');

const app = express();
app.use(express.json());

app.use('/api', checkoutRoutes);
app.use('/api', reportRoutes);
app.use('/api', userRoutes);

app.use(errorHandler);

initDb()
    .then(() => {
        app.listen(config.port, () => {
            logger.info(`LMS API running on port ${config.port}`);
        });
    })
    .catch((err) => {
        logger.error(`Failed to initialize database: ${err.message}`);
        process.exit(1);
    });

module.exports = app;
