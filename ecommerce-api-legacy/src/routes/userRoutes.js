const express = require('express');
const router = express.Router();
const UserController = require('../controllers/userController');

router.delete('/:id', UserController.deleteUser);

module.exports = router;
