const UserModel = require('../models/UserModel');

const userController = {
    async deleteUser(req, res, next) {
        const userId = parseInt(req.params.id);
        if (!Number.isInteger(userId) || userId <= 0) {
            return res.status(400).json({ error: 'ID de usuário inválido' });
        }

        try {
            const user = await UserModel.findById(userId);
            if (!user) return res.status(404).json({ error: 'Usuário não encontrado' });

            await UserModel.deleteById(userId);
            res.status(200).json({ msg: 'Usuário e registros relacionados removidos com sucesso' });
        } catch (err) {
            next(err);
        }
    },
};

module.exports = userController;
