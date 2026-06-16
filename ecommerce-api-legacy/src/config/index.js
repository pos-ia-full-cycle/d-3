require('dotenv').config();

module.exports = {
    port: parseInt(process.env.PORT) || 3000,
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
    adminToken: process.env.ADMIN_TOKEN || 'change-me-in-production',
};
