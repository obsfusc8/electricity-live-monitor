import Fastify from 'fastify'
import cors from '@fastify/cors'
import { createClient } from '@clickhouse/client'

const fastify = Fastify({
  logger: true
})

fastify.register(cors, {
  origin: '*'
})

const client = createClient({
  url: process.env.CLICKHOUSE_URL || 'http://localhost:8123',
  username: process.env.CLICKHOUSE_USER || 'default',
  password: process.env.CLICKHOUSE_PASSWORD || '',
  database: process.env.CLICKHOUSE_DB || 'powergrid'
})

fastify.get('/api/generation', async (request, reply) => {
  try {
    const result = await client.query({
      query: 'SELECT * FROM pgcb_generation ORDER BY date DESC, time DESC LIMIT 24',
      format: 'JSONEachRow',
    })
    const data = await result.json()
    return data
  } catch (error) {
    fastify.log.error(error)
    reply.code(500).send({ error: 'Database error' })
  }
})

fastify.get('/api/daily-generation', async (request, reply) => {
  try {
    const result = await client.query({
      query: 'SELECT * FROM bpdb_generation ORDER BY installed_capacity DESC LIMIT 50',
      format: 'JSONEachRow',
    })
    const data = await result.json()
    return data
  } catch (error) {
    fastify.log.error(error)
    reply.code(500).send({ error: 'Database error' })
  }
})

fastify.listen({ port: 3000, host: '0.0.0.0' }, function (err, address) {
  if (err) {
    fastify.log.error(err)
    process.exit(1)
  }
  console.log(`Server is now listening on ${address}`)
})
