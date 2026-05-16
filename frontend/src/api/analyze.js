import axios from 'axios'

const http = axios.create({
  baseURL: '/api',
  timeout: 120000,
})

export function getHealth() {
  return http.get('/health')
}

export function getMode() {
  return http.get('/mode')
}

export function analyze(payload) {
  return http.post('/analyze', payload)
}
