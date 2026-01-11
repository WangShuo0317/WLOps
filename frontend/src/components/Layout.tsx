import { useState } from 'react'
import { Layout as AntLayout, Menu, theme, Dropdown, Avatar } from 'antd'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  DashboardOutlined,
  DatabaseOutlined,
  RocketOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  UserOutlined,
  LogoutOutlined,
} from '@ant-design/icons'
import { authStorage } from '@/services/auth'
import type { MenuProps } from 'antd'

const { Header, Sider, Content } = AntLayout

interface LayoutProps {
  children: React.ReactNode
}

const Layout = ({ children }: LayoutProps) => {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken()

  const userInfo = authStorage.getUser()

  const handleLogout = () => {
    authStorage.clear()
    navigate('/login')
  }

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: userInfo?.realName || userInfo?.username || '用户',
      disabled: true,
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ]

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表盘',
    },
    {
      key: '/datasets',
      icon: <DatabaseOutlined />,
      label: '数据集管理',
    },
    {
      key: '/tasks',
      icon: <RocketOutlined />,
      label: '任务管理',
    },
  ]

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Sider trigger={null} collapsible collapsed={collapsed}>
        <div style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          fontSize: collapsed ? 16 : 20,
          fontWeight: 'bold',
        }}>
          {collapsed ? 'WL' : 'WLOps'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <AntLayout>
        <Header style={{ 
          padding: '0 24px', 
          background: colorBgContainer,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            {collapsed ? (
              <MenuUnfoldOutlined
                style={{ fontSize: 18, cursor: 'pointer' }}
                onClick={() => setCollapsed(false)}
              />
            ) : (
              <MenuFoldOutlined
                style={{ fontSize: 18, cursor: 'pointer' }}
                onClick={() => setCollapsed(true)}
              />
            )}
            <div style={{ marginLeft: 24, fontSize: 18, fontWeight: 500 }}>
              模型训练与持续演进平台
            </div>
          </div>
          
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <div style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8 }}>
              <Avatar icon={<UserOutlined />} />
              <span>{userInfo?.username}</span>
            </div>
          </Dropdown>
        </Header>
        <Content
          style={{
            margin: '24px 16px',
            padding: 24,
            minHeight: 280,
            background: colorBgContainer,
            borderRadius: borderRadiusLG,
          }}
        >
          {children}
        </Content>
      </AntLayout>
    </AntLayout>
  )
}

export default Layout
