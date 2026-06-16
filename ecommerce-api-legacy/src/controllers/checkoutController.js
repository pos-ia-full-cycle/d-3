const CheckoutService = require('../services/CheckoutService');

function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function isValidCardNumber(card) {
    return /^\d{13,19}$/.test(card);
}

const checkoutController = {
    async checkout(req, res, next) {
        const { usr: userName, eml: email, pwd: password, c_id: courseId, card: cardNumber } = req.body;

        if (!userName || !email || !courseId || !cardNumber) {
            return res.status(400).json({ error: 'Campos obrigatórios: usr, eml, c_id, card' });
        }
        if (!isValidEmail(email)) {
            return res.status(400).json({ error: 'Email inválido' });
        }
        if (!Number.isInteger(Number(courseId)) || Number(courseId) <= 0) {
            return res.status(400).json({ error: 'c_id deve ser um inteiro positivo' });
        }
        if (!isValidCardNumber(String(cardNumber))) {
            return res.status(400).json({ error: 'Número de cartão inválido' });
        }

        try {
            const result = await CheckoutService.processCheckout({
                userName,
                email,
                password,
                courseId: Number(courseId),
                cardNumber: String(cardNumber),
            });
            res.status(200).json({ msg: 'Sucesso', enrollment_id: result.enrollmentId });
        } catch (err) {
            next(err);
        }
    },
};

module.exports = checkoutController;
