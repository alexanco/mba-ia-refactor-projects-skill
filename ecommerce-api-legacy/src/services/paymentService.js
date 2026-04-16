const PAYMENT_STATUS = {
    PAID: 'PAID',
    DENIED: 'DENIED',
};

class PaymentService {
    // TODO: Replace with real payment gateway integration using config.paymentGatewayKey
    static processCard(cardNumber) {
        if (cardNumber.startsWith('4')) {
            return PAYMENT_STATUS.PAID;
        }
        return PAYMENT_STATUS.DENIED;
    }
}

module.exports = { PaymentService, PAYMENT_STATUS };
