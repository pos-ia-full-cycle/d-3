const bcrypt = require('bcryptjs');
const { runInTransaction } = require('../db');
const CourseModel = require('../models/CourseModel');
const UserModel = require('../models/UserModel');
const EnrollmentModel = require('../models/EnrollmentModel');
const PaymentModel = require('../models/PaymentModel');
const AuditLogModel = require('../models/AuditLogModel');

const APPROVED_CARD_PREFIX = '4';

const CheckoutService = {
    async processCheckout({ userName, email, password, courseId, cardNumber }) {
        const course = await CourseModel.findActiveById(courseId);
        if (!course) throw Object.assign(new Error('Curso não encontrado'), { statusCode: 404 });

        const paymentStatus = cardNumber.startsWith(APPROVED_CARD_PREFIX) ? 'PAID' : 'DENIED';
        if (paymentStatus === 'DENIED') throw Object.assign(new Error('Pagamento recusado'), { statusCode: 400 });

        return runInTransaction(async () => {
            let existingUser = await UserModel.findByEmail(email);
            let userId;

            if (existingUser) {
                userId = existingUser.id;
            } else {
                const passwordHash = await bcrypt.hash(password || 'changeme', 12);
                userId = await UserModel.create(userName, email, passwordHash);
            }

            const enrollmentId = await EnrollmentModel.create(userId, courseId);
            await PaymentModel.create(enrollmentId, course.price, paymentStatus);
            await AuditLogModel.record(`Checkout course ${courseId} by user ${userId}`);

            return { enrollmentId };
        });
    },
};

module.exports = CheckoutService;
