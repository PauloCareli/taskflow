import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { App } from './app/App'
import { createAppRouter } from './app/router'
import './styles/index.css'

const container = document.getElementById('root')
if (!container) {
  throw new Error('Root element #root not found in index.html')
}

createRoot(container).render(
  <StrictMode>
    <App router={createAppRouter()} />
  </StrictMode>,
)
