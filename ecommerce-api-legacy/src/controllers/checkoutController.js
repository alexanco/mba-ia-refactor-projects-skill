const EnrollmentService = require('../services/enrollmentService');

class CheckoutController {
    static async checkout(req, res, next) {
        const { usr: name, eml: email, pwd: password, c_id: courseId, card: cardNumber } = req.body;

        if (!name || !email || !courseId || !cardNumber) {
            return res.status(400).json({ error: 'Bad Request: name, email, c_id and card are required' });
        }

        const parsedCourseId = Number(courseId);
        if (!Number.isInteger(parsedCourseId) || parsedCourseId <= 0) {
            return res.status(400).json({ error: 'Bad Request: c_id must be a positive integer' });
        }

        try {
            const { enrollmentId } = await EnrollmentService.checkout({
                name,
                email,
                password,
                courseId: parsedCourseId,
                cardNumber,
            });
            return res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
        } catch (err) {
            next(err);
        }
    }
}

module.exports = CheckoutController;
