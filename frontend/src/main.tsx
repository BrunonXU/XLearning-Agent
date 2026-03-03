import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './index.css'

// 页面（懒加载）
const HomePage = React.lazy(() => import('./pages/HomePage'))
const WorkspacePage = React.lazy(() => import('./pages/WorkspacePage'))

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <React.Suspense fallback={<div className="flex h-screen items-center justify-center"><div className="animate-spin h-8 w-8 border-2 border-primary border-t-transparent rounded-full" /></div>}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/workspace/:planId" element={<WorkspacePage />} />
        </Routes>
      </React.Suspense>
    </BrowserRouter>
  </React.StrictMode>
)
