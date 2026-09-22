import './app.css'
import App from './App.svelte'
import { inject } from '@vercel/analytics'

// Initialize Vercel Web Analytics
inject({ 
  mode: import.meta.env.MODE === 'production' ? 'production' : 'development',
  debug: import.meta.env.MODE !== 'production'
})

const app = new App({
  target: document.getElementById('app'),
})

export default app
