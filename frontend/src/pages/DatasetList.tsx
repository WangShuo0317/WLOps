import { useEffect, useState } from 'react'
import { 
  Button, 
  Table, 
  Space, 
  Modal, 
  Upload, 
  Form, 
  Input, 
  Select, 
  message,
  Tag,
  Popconfirm,
} from 'antd'
import { UploadOutlined, DeleteOutlined, DownloadOutlined } from '@ant-design/icons'
import { datasetApi } from '@/services/api'
import { authStorage } from '@/services/auth'
import { formatFileSize } from '@/utils/helpers'
import type { Dataset } from '@/types'
import type { UploadFile } from 'antd'
import dayjs from 'dayjs'

const DatasetList = () => {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [loading, setLoading] = useState(false)
  const [uploadModalVisible, setUploadModalVisible] = useState(false)
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [form] = Form.useForm()

  const userInfo = authStorage.getUser()
  const userId = userInfo?.userId || 1

  useEffect(() => {
    loadDatasets()
  }, [])

  const loadDatasets = async () => {
    setLoading(true)
    try {
      const res = await datasetApi.getUserDatasets(userId)
      setDatasets(res.data)
    } catch (error) {
      message.error('加载数据集失败')
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async (values: any) => {
    if (fileList.length === 0) {
      message.error('请选择文件')
      return
    }

    const formData = new FormData()
    // 修复：直接使用 file 对象，因为 beforeUpload 返回 false 时，file 就是原始 File 对象
    const file = fileList[0].originFileObj || fileList[0]
    formData.append('file', file as File)
    formData.append('name', values.name)
    formData.append('description', values.description || '')
    formData.append('datasetType', values.datasetType)
    formData.append('domain', values.domain)
    formData.append('userId', userId.toString())

    try {
      await datasetApi.upload(formData)
      message.success('上传成功')
      setUploadModalVisible(false)
      form.resetFields()
      setFileList([])
      loadDatasets()
    } catch (error: any) {
      console.error('上传失败:', error)
      message.error(error.response?.data?.message || '上传失败')
    }
  }

  const handleDelete = async (datasetId: string) => {
    try {
      await datasetApi.delete(datasetId, userId)
      message.success('删除成功')
      loadDatasets()
    } catch (error: any) {
      console.error('删除失败:', error)
      message.error(error.response?.data?.error || '删除失败')
    }
  }

  const handleDownload = async (datasetId: string) => {
    try {
      const res = await datasetApi.getDownloadUrl(datasetId)
      window.open(res.data.downloadUrl, '_blank')
    } catch (error) {
      message.error('获取下载链接失败')
    }
  }

  const columns = [
    {
      title: '数据集名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '领域',
      dataIndex: 'domain',
      key: 'domain',
      render: (domain: string) => <Tag color="blue">{domain}</Tag>,
    },
    {
      title: '类型',
      dataIndex: 'datasetType',
      key: 'datasetType',
    },
    {
      title: '文件大小',
      dataIndex: 'fileSize',
      key: 'fileSize',
      render: (size: number) => formatFileSize(size),
    },
    {
      title: '样本数',
      dataIndex: 'sampleCount',
      key: 'sampleCount',
      render: (count?: number) => count || '-',
    },
    {
      title: '是否优化',
      dataIndex: 'isOptimized',
      key: 'isOptimized',
      render: (isOptimized: boolean) => (
        <Tag color={isOptimized ? 'green' : 'default'}>
          {isOptimized ? '是' : '否'}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Dataset) => (
        <Space>
          <Button
            type="link"
            icon={<DownloadOutlined />}
            onClick={() => handleDownload(record.datasetId)}
          >
            下载
          </Button>
          <Popconfirm
            title="确定删除此数据集？"
            onConfirm={() => handleDelete(record.datasetId)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h1>数据集管理</h1>
        <Button
          type="primary"
          icon={<UploadOutlined />}
          onClick={() => setUploadModalVisible(true)}
        >
          上传数据集
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={datasets}
        rowKey="datasetId"
        loading={loading}
      />

      <Modal
        title="上传数据集"
        open={uploadModalVisible}
        onCancel={() => {
          setUploadModalVisible(false)
          form.resetFields()
          setFileList([])
        }}
        onOk={() => form.submit()}
        okText="上传"
        cancelText="取消"
      >
        <Form form={form} layout="vertical" onFinish={handleUpload}>
          <Form.Item
            name="name"
            label="数据集名称"
            rules={[{ required: true, message: '请输入数据集名称' }]}
          >
            <Input placeholder="请输入数据集名称" />
          </Form.Item>

          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} placeholder="请输入描述（可选）" />
          </Form.Item>

          <Form.Item
            name="datasetType"
            label="数据集类型"
            rules={[{ required: true, message: '请选择数据集类型' }]}
          >
            <Select placeholder="请选择数据集类型">
              <Select.Option value="training">训练集</Select.Option>
              <Select.Option value="validation">验证集</Select.Option>
              <Select.Option value="test">测试集</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="domain"
            label="领域"
            rules={[{ required: true, message: '请选择领域' }]}
          >
            <Select placeholder="请选择领域">
              <Select.Option value="math">数学</Select.Option>
              <Select.Option value="nlp">自然语言处理</Select.Option>
              <Select.Option value="cv">计算机视觉</Select.Option>
              <Select.Option value="other">其他</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item label="文件">
            <Upload
              fileList={fileList}
              beforeUpload={(file) => {
                setFileList([file])
                return false
              }}
              onRemove={() => setFileList([])}
              maxCount={1}
            >
              <Button icon={<UploadOutlined />}>选择文件</Button>
            </Upload>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default DatasetList
