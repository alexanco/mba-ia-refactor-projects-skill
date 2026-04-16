const UserModel = require('../models/userModel');

class UserController {
    static deleteUser(req, res, next) {
        const parsedId = Number(req.params.id);

        if (!Number.isInteger(parsedId) || parsedId <= 0) {
            return res.status(400).json({ error: 'Bad Request: id must be a positive integer' });
        }

        try {
            UserModel.deleteById(parsedId);
            return res.json({ msg: 'Usuário deletado com sucesso' });
        } catch (err) {
            next(err);
        }
    }
}

module.exports = UserController;
