var app = getApp()

Page({
  data: {
    albums: [],
    currentPage: 1,
    hasMore: true,
    loading: false,
    refreshing: false,
    loadingTriggered: false,
    error: false
  },

  onLoad: function() {
    console.log('🏠 ===== Home页面onLoad开始 =====')
    this.checkLoginAndLoad()
  },

  onShow: function() {
    console.log('👁️ Home页面onShow')
    
    // 每次显示时都检查登录状态
    this.checkLoginAndLoad()
  },

  onPullDownRefresh: function() {
    this.refreshData()
  },

  onReachBottom: function() {
    this.loadMoreAlbums()
  },

  refreshData: function() {
    var self = this
    console.log('🔄 下拉刷新开始')
    wx.showNavigationBarLoading()
    this.setData({ refreshing: true })
    
    // 清除缓存并重新加载
    this.setData({ 
      currentPage: 1, 
      hasMore: true 
    })
    
    this.loadAlbumsFromAPI(true, 'refresh').then(function() {
      self.setData({ refreshing: false })
      wx.hideNavigationBarLoading()
      wx.stopPullDownRefresh()
      console.log('✅ 下拉刷新完成')
    }).catch(function(error) {
      self.setData({ refreshing: false })
      wx.hideNavigationBarLoading()
      wx.stopPullDownRefresh()
      console.error('❌ 下拉刷新失败:', error)
    })
  },

  loadAlbums: function(isRefresh, source) {
    var self = this
    isRefresh = isRefresh || false
    source = source || 'unknown'
    
    console.log('🔄 加载相册 - 来源: ' + source + ', 刷新: ' + isRefresh)
    
    // 直接从API加载数据
    console.log('🌐 开始从API加载数据')
    return this.loadAlbumsFromAPI(isRefresh, source)
  },

  loadAlbumsFromAPI: function(isRefresh, source) {
    var self = this
    isRefresh = isRefresh || false
    source = source || 'unknown'
    
    if (this.data.loading) return Promise.resolve()
    
    this.setData({ loading: true })
    
    return app.request({
      url: '/albums/',
      method: 'GET',
      data: {
        page: this.data.currentPage,
        size: 10,
        sort_by: 'default'
      }
    }).then(function(response) {
      console.log('✅ API响应:', response)
      
      var albumsData = []
      if (response && response.items && Array.isArray(response.items)) {
        albumsData = response.items
      } else if (response && response.data && Array.isArray(response.data)) {
        albumsData = response.data
      } else if (response && Array.isArray(response)) {
        albumsData = response
      }
      
      var albums = self.processAlbumsData(albumsData)
      var newAlbums = isRefresh ? albums : self.data.albums.concat(albums)
      
      self.setData({ 
        albums: newAlbums,
        loading: false,
        hasMore: albumsData.length === 10,
        currentPage: self.data.currentPage + (albumsData.length > 0 ? 1 : 0),
        error: false
      })
      
      console.log('✅ 相册数据处理完成，共 ' + newAlbums.length + ' 个相册')
    }).catch(function(error) {
      self.setData({ loading: false })
      console.error('❌ 加载相册失败:', error)
      
      // 检查是否为认证错误，如果是则重新检查登录状态
      if (error.message && error.message.includes('认证失效')) {
        console.log('🔄 检测到认证失效，重新检查登录状态')
        // 延迟一下再检查，让app.js的clearLoginState先执行
        setTimeout(function() {
          self.checkLoginAndLoad()
        }, 200)
        return
      }
      
      wx.showToast({
        title: '加载失败，请重试',
        icon: 'none'
      })
      throw error
    })
  },

  loadMoreAlbums: function() {
    if (!this.data.hasMore || this.data.loading) {
      return
    }
    
    console.log('📄 加载更多相册...')
    this.loadAlbumsFromAPI(false, 'loadMore')
  },

  processAlbumsData: function(albums) {
    var self = this
    var baseUrl = app.globalData.imageBaseUrl || 'https://photo.liuenyi.com'
    
    console.log('🎨 ===== 处理相册数据 =====')
    console.log('📦 原始相册数据:', albums)
    console.log('🌐 图片基础URL:', baseUrl)
    
    var processedAlbums = albums.map(function(album) {
      var coverUrl = album.cover_image || self.getDefaultCover()
      if (coverUrl && !coverUrl.startsWith('http')) {
        coverUrl = baseUrl + '/' + coverUrl
      }
      
      var processedAlbum = Object.assign({}, album, {
        // 确保模板需要的字段都存在
        coverUrl: coverUrl,  // 模板中使用的字段
        cover_image: coverUrl, // 保持原字段
        displayName: album.name || '未命名相册',
        photoCountText: (album.photo_count || 0) + '张照片',
        timeAgo: self.formatTimeAgo(album.updated_at),
        name: album.name || '未命名相册',
        description: album.description || ''
      })
      
      console.log('✨ 处理相册:', {
        id: album.id,
        name: album.name,
        coverUrl: coverUrl,
        photoCount: album.photo_count
      })
      
      return processedAlbum
    })
    
    console.log('✅ 相册数据处理完成，共', processedAlbums.length, '个相册')
    return processedAlbums
  },

  getDefaultCover: function() {
    return 'https://via.placeholder.com/300x200/f0f0f0/999999?text=相册封面'
  },

  formatTimeAgo: function(dateString) {
    if (!dateString) return '未知时间'
    
    var date = new Date(dateString)
    var now = new Date()
    var diffTime = now - date
    var diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))
    
    if (diffDays === 0) return '今天'
    if (diffDays === 1) return '昨天'
    if (diffDays < 7) return diffDays + '天前'
    if (diffDays < 30) return Math.floor(diffDays / 7) + '周前'
    return Math.floor(diffDays / 30) + '个月前'
  },

  onAlbumTap: function(e) {
    var album = e.currentTarget.dataset.album
    wx.navigateTo({
      url: '/pages/album/album?albumId=' + album.id + '&albumName=' + encodeURIComponent(album.name)
    })
  },

  // 分享功能
  onShareAppMessage: function() {
    return {
      title: '🎈 咱家的记忆 - 珍藏美好回忆',
      desc: '一个精美的私人相册小程序，记录生活中的美好瞬间',
      path: '/pages/home/home',
      imageUrl: '', // 可以设置分享图片
      success: function() {
        console.log('✅ 分享成功')
      },
      fail: function() {
        console.log('❌ 分享失败')
      }
    }
  },

  // 分享到朋友圈功能  
  onShareTimeline: function() {
    return {
      title: '🎈 咱家的记忆 - 珍藏美好回忆',
      query: '',
      imageUrl: '', // 可以设置分享图片
      success: function() {
        console.log('✅ 分享到朋友圈成功')
      },
      fail: function() {
        console.log('❌ 分享到朋友圈失败')
      }
    }
  },

  // 检查登录状态并加载数据
  checkLoginAndLoad: function() {
    var isLoggedIn = wx.getStorageSync('isLoggedIn')
    
    console.log('🔍 ===== 登录状态检查 =====')
    console.log('📊 isLoggedIn:', isLoggedIn)
    
    if (isLoggedIn !== true) {
      // 未登录，跳转到登录页面
      console.log('❌ ===== 未登录，跳转到登录页 =====')
      
      wx.reLaunch({
        url: '/pages/login/login',
        success: function() {
          console.log('✅ 成功跳转到登录页')
        },
        fail: function(error) {
          console.error('❌ 跳转到登录页失败:', error)
        }
      })
      return
    }

    console.log('✅ ===== 登录检查通过，开始加载首页数据 =====')
    
    // 检查是否已经有数据，避免重复加载
    if (this.data.albums.length === 0) {
      console.log('📦 无数据，开始加载')
      this.loadAlbums(false, 'checkLoginAndLoad')
    } else {
      console.log('💾 使用已有数据，无需重新加载，当前相册数量:', this.data.albums.length)
    }
  }
})
