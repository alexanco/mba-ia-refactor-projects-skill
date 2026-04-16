const bcrypt = require('bcryptjs');
const UserModel = require('../models/userModel');
const CourseModel = require('../models/courseModel');
const EnrollmentModel = require('../models/enrollmentModel');
const PaymentModel = require('../models/paymentModel');
const AuditLogModel = require('../models/auditLogModel');
const { PaymentService, PAYMENT_STATUS } = require('./paymentService');

class EnrollmentService {
    static async checkout({ name, email, password, courseId, cardNumber }) {
        const course = CourseModel.findActiveById(courseId);
        if (!course) {
            const error = new Error('Curso não encontrado');
            error.status = 404;
            throw error;
        }

        let user = UserModel.findByEmail(email);
        if (!user) {
            const passwordHash = await bcrypt.hash(password || '123456', 12);
            const userId = UserModel.create({ name, email, passwordHash });
            user = { id: userId };
        }

        const paymentStatus = PaymentService.processCard(cardNumber);
        if (paymentStatus === PAYMENT_STATUS.DENIED) {
            const error = new Error('Pagamento recusado');
            error.status = 400;
            throw error;
        }

        const enrollmentId = EnrollmentModel.create({ userId: user.id, courseId });
        PaymentModel.create({ enrollmentId, amount: course.price, status: paymentStatus });
        AuditLogModel.create(`Checkout curso ${courseId} por ${user.id}`);

        return { enrollmentId };
    }
}

module.exports = EnrollmentService;
