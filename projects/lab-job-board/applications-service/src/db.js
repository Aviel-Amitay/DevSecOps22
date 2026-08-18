'use strict';

const { Pool } = require('pg');
const fs = require('fs');

function databaseUrl() {
  if (process.env.DATABASE_URL) return process.env.DATABASE_URL;

  const passwordFile = process.env.POSTGRES_PASSWORD_FILE || '/run/secrets/db_password';
  const password = fs.existsSync(passwordFile)
    ? fs.readFileSync(passwordFile, 'utf8').trim()
    : process.env.POSTGRES_PASSWORD;
  if (!password) {
    throw new Error('Set DATABASE_URL or provide POSTGRES_PASSWORD_FILE');
  }
  const user = encodeURIComponent(process.env.POSTGRES_USER || 'postgres');
  const encodedPassword = encodeURIComponent(password);
  const host = process.env.POSTGRES_HOST || 'localhost';
  const port = process.env.POSTGRES_PORT || '5432';
  const database = process.env.POSTGRES_DB || 'jobboard';

  return `postgresql://${user}:${encodedPassword}@${host}:${port}/${database}`;
}

const pool = new Pool({
  connectionString: databaseUrl(),
  max: 10,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
});

pool.on('error', (err) => {
  console.error('Unexpected database pool error:', err.message);
});

async function initDB() {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS applications (
      id              UUID         PRIMARY KEY,
      job_id          VARCHAR(255) NOT NULL,
      applicant_name  VARCHAR(200) NOT NULL,
      applicant_email VARCHAR(200) NOT NULL,
      cover_letter    TEXT,
      status          VARCHAR(50)  DEFAULT 'pending'
                      CHECK (status IN ('pending', 'reviewed', 'accepted', 'rejected')),
      created_at      TIMESTAMP    DEFAULT NOW()
    )
  `);

  await pool.query(`
    CREATE INDEX IF NOT EXISTS idx_applications_job_id ON applications(job_id)
  `);

  console.log('[db] Applications table ready');
}

module.exports = { pool, initDB };
