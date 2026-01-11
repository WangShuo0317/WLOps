import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom'
import { useEffect } from 'react'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import DatasetList from './pages/DatasetList'
import TaskList from './pages/TaskList'
import TaskDetail from './pages/TaskDetail'
import CreateTask from './pages/CreateTask'
import Login from './pages/Login'
import { authStorage } from './services/auth'

// 路由守卫组件
const PrivateRoute = ({ children }: { children: React.ReactNode }) => {
  const navigate = useNavigate()
  const location = useLocation()
  const isLoggedIn = authStorage.isLoggedIn()

  useEffect(() => {
    if (!isLoggedIn) {
      navigate('/login', { state: { from: location }, replace: true })
    }
  }, [isLoggedIn, navigate, location])

  return isLoggedIn ? <>{children}</> : null
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/*"
        element={
          <PrivateRoute>
            <Layout>
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/datasets" element={<DatasetList />} />
                <Route path="/tasks" element={<TaskList />} />
                <Route path="/tasks/create" element={<CreateTask />} />
                <Route path="/tasks/:taskId" element={<TaskDetail />} />
              </Routes>
            </Layout>
          </PrivateRoute>
        }
      />
    </Routes>
  )
}

export default App
