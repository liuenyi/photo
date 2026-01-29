// 测试完整的登录和数据获取流程
const apiBase = 'https://photo.liuenyi.com/api'

// 1. 测试登录
console.log('🔐 测试登录...')
fetch(`${apiBase}/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ password: '0525' })
})
.then(response => response.json())
.then(loginData => {
  console.log('✅ 登录成功:', loginData)
  
  if (loginData.access_token) {
    // 2. 测试获取相册
    console.log('📁 测试获取相册...')
    return fetch(`${apiBase}/albums/`, {
      headers: { 'Authorization': `Bearer ${loginData.access_token}` }
    })
  } else {
    throw new Error('未获得访问令牌')
  }
})
.then(response => response.json())
.then(albumsData => {
  console.log('✅ 相册数据:', albumsData)
  
  if (albumsData.items && albumsData.items.length > 0) {
    const albumId = albumsData.items[0].id
    console.log(`📸 测试获取相册 ${albumId} 的照片...`)
    
    // 重新获取token进行照片请求
    return fetch(`${apiBase}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: '0525' })
    })
    .then(response => response.json())
    .then(loginData => {
      return fetch(`${apiBase}/photos/?album_id=${albumId}&page=1&size=10`, {
        headers: { 'Authorization': `Bearer ${loginData.access_token}` }
      })
    })
  } else {
    console.log('⚠️ 没有找到相册')
    return Promise.resolve({ json: () => ({ items: [] }) })
  }
})
.then(response => response.json())
.then(photosData => {
  console.log('✅ 照片数据:', photosData)
  console.log('🎉 所有API测试完成!')
})
.catch(error => {
  console.error('❌ 测试失败:', error)
}) 