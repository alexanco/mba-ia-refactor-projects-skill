const express = require('express');
const config = require('./config');
const { initDb } = require('./config/database');
const checkoutRoutes = require('./routes/checkoutRoutes');
const reportRoutes = require('./routes/reportRoutes');
const userRoutes = require('./routes/userRoutes');
const errorHandler = require('./middlewares/errorHandler');

const app = express();
app.use(express.json());

initDb();

app.use('/api', checkoutRoutes);
app.use('/api/admin', reportRoutes);
app.use('/api/users', userRoutes);

app.use(errorHandler);

app.listen(config.port, () => {
    console.log(`LMS API running on port ${config.port}`);
});
