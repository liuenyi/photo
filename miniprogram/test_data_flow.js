// 测试数据流
console.log('🧪 ===== 开始测试数据流 =====')

// 1. 测试API响应
var app = getApp()
app.request({
  url: '/albums/',
  method: 'GET',
  data: {
    page: 1,
    size: 10,
    sort_by: 'default'
  }
}).then(function(response) {
  console.log('✅ API测试成功')
  console.log('📦 响应数据:', response)
  
  // 2. 测试数据处理
  if (response && response.items) {
    var albums = response.items
    console.log('📊 相册数量:', albums.length)
    
    if (albums.length > 0) {
      var firstAlbum = albums[0]
      console.log('📝 第一个相册:', firstAlbum)
      
      // 3. 测试图片URL处理
      var baseUrl = app.globalData.imageBaseUrl
      var coverUrl = firstAlbum.cover_image
      if (coverUrl && !coverUrl.startsWith('http')) {
        coverUrl = baseUrl + '/' + coverUrl
      }
      console.log('🖼️ 处理后的封面URL:', coverUrl)
    }
  }
}).catch(function(error) {
  console.error('❌ API测试失败:', error)
}) 