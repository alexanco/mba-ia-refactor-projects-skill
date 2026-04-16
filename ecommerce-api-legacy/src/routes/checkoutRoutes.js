const express = require('express');
const router = express.Router();
const CheckoutController = require('../controllers/checkoutController');

router.post('/checkout', CheckoutController.checkout);

module.exports = router;
