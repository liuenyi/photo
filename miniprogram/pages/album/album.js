var app = getApp()

Page({
  data: {
    albumId: null,
    albumName: '',
    photos: [],
    page: 1,
    hasMore: true,
    loading: false,
    refreshing: false,
    error: false,
    albumInfo: {
      name: '',
      description: ''
    }
  },

  onLoad: function(options) {
    console.log('🖼️ 相册页面加载开始')
    
    var albumId = parseInt(options.albumId)
    var albumName = options.albumName ? decodeURIComponent(options.albumName) : '相册'
    
    this.setData({ 
      albumId: albumId,
      albumName: albumName,
      albumInfo: {
        name: albumName,
        description: ''
      }
    })
    
    // 设置页面标题
    wx.setNavigationBarTitle({
      title: albumName
    })
    
    // 直接加载数据
    this.loadPhotos(false)
  },

  onShow: function() {
    console.log('👁️ 相册页面显示')
    
    // 如果没有数据且不在加载中，重新加载
    if (this.data.photos.length === 0 && !this.data.loading && this.data.albumId) {
      console.log('🔄 检测到无数据，重新加载照片')
      this.loadPhotos(false)
    }
  },

  onPullDownRefresh: function() {
    this.refreshData()
  },

  onReachBottom: function() {
    this.loadMorePhotos()
  },

  onShareAppMessage: function() {
    return {
      title: '相册: ' + this.data.albumName,
      path: '/pages/album/album?albumId=' + this.data.albumId + '&albumName=' + encodeURIComponent(this.data.albumName),
      imageUrl: this.data.photos.length > 0 ? this.data.photos[0].fullUrl : ''
    }
  },

  refreshData: function() {
    var self = this
    console.log('🔄 下拉刷新开始')
    wx.showNavigationBarLoading()
    this.setData({ 
      refreshing: true,
      page: 1,
      hasMore: true 
    })
    
    this.loadPhotos(true).then(function() {
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

  loadPhotos: function(isRefresh) {
    var self = this
    isRefresh = isRefresh || false
    
    console.log('🌐 开始加载照片')
    
    if (this.data.loading && !isRefresh) {
      console.log('⚠️ 正在加载中，跳过重复请求')
      return Promise.resolve()
    }
    
    this.setData({ loading: true })
    
    return app.request({
      url: '/photos/',
      method: 'GET',
      data: {
        album_id: this.data.albumId,
        page: this.data.page,
        size: 1000
      }
    }).then(function(response) {
      console.log('✅ API响应:', response)
      
      var photosData = []
      if (response && response.items && Array.isArray(response.items)) {
        photosData = response.items
      } else if (response && response.data && Array.isArray(response.data)) {
        photosData = response.data
      } else if (response && Array.isArray(response)) {
        photosData = response
      }

      var photos = self.processPhotosData(photosData)
      var newPhotos = isRefresh ? photos : self.data.photos.concat(photos)
      var currentPage = isRefresh ? 1 : self.data.page
      var nextPage = currentPage + 1
      var hasMorePages = response.pages ? currentPage < response.pages : false
      
      self.setData({
        photos: newPhotos,
        loading: false,
        hasMore: hasMorePages || photosData.length === 1000,
        page: nextPage
      })
      
      console.log('✅ 照片加载完成，共 ' + newPhotos.length + ' 张照片')
    }).catch(function(error) {
      self.setData({ loading: false })
      console.error('❌ 加载照片失败:', error)
      
      wx.showToast({
        title: '加载失败，请重试',
        icon: 'none'
      })
      throw error
    })
  },

  loadMorePhotos: function() {
    if (!this.data.hasMore || this.data.loading) {
      return
    }
    
    console.log('📄 加载更多照片...')
    this.loadPhotos(false)
  },

  processPhotosData: function(photos) {
    var self = this
    console.log('🎨 处理照片数据，输入:', photos.length, '张照片')
    
    return photos.map(function(photo, index) {
      var baseUrl = getApp().globalData.imageBaseUrl || 'https://photo.liuenyi.com'
      var fullUrl = photo.url
      var thumbnailUrl = photo.thumbnail_url || photo.url
      
      if (fullUrl && !fullUrl.startsWith('http')) {
        fullUrl = baseUrl + '/' + fullUrl
      }
      if (thumbnailUrl && !thumbnailUrl.startsWith('http')) {
        thumbnailUrl = baseUrl + '/' + thumbnailUrl
      }
      
      return Object.assign({}, photo, {
        fullUrl: fullUrl,
        thumbnailUrl: thumbnailUrl,
        displayName: photo.original_filename || '照片',
        sizeText: self.formatFileSize(photo.file_size),
        timeAgo: self.formatTimeAgo(photo.created_at),
        hasDescription: !!(photo.description && photo.description.trim())
      })
    })
  },

  formatFileSize: function(bytes) {
    if (!bytes || bytes === 0) return '未知大小'
    
    var sizes = ['B', 'KB', 'MB', 'GB']
    var i = 0
    var size = bytes
    
    while (size >= 1024 && i < sizes.length - 1) {
      size /= 1024
      i++
    }
    
    return size.toFixed(i === 0 ? 0 : 1) + sizes[i]
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

  onPhotoTap: function(e) {
    var index = e.currentTarget.dataset.index
    var photo = e.currentTarget.dataset.photo
    
    var urls = this.data.photos.map(function(p) {
      return p.fullUrl
    })
    
    wx.previewImage({
      urls: urls,
      current: photo.fullUrl
    })
  },

  onRetry: function() {
    console.log('🔄 用户点击重试')
    this.setData({ 
      error: false,
      page: 1,
      hasMore: true
    })
    this.loadPhotos(true)
  },

  onLongPress: function(e) {
    var photo = e.currentTarget.dataset.photo
    
    wx.showActionSheet({
      itemList: ['保存到相册', '查看详情'],
      success: function(res) {
        if (res.tapIndex === 0) {
            this.savePhoto(photo)
        } else if (res.tapIndex === 1) {
            this.showPhotoDetail(photo)
        }
      }.bind(this)
    })
  },

  savePhoto: function(photo) {
    var self = this
    
    wx.getSetting({
      success: function(res) {
        if (res.authSetting['scope.writePhotosAlbum']) {
          self.downloadAndSavePhoto(photo)
        } else if (res.authSetting['scope.writePhotosAlbum'] === false) {
          wx.showModal({
            title: '需要相册权限',
            content: '需要您授权保存图片到相册的权限，请在设置中开启',
            confirmText: '去设置',
            cancelText: '取消',
            success: function(modalRes) {
              if (modalRes.confirm) {
                wx.openSetting({
                  success: function(settingRes) {
                    if (settingRes.authSetting['scope.writePhotosAlbum']) {
                      self.downloadAndSavePhoto(photo)
                    }
                  }
                })
              }
            }
          })
        } else {
          wx.authorize({
            scope: 'scope.writePhotosAlbum',
            success: function() {
              self.downloadAndSavePhoto(photo)
            },
            fail: function() {
              wx.showToast({
                title: '需要相册权限才能保存图片',
                icon: 'none',
                duration: 2000
              })
            }
          })
        }
      }
    })
  },

  downloadAndSavePhoto: function(photo) {
    wx.showLoading({ title: '保存中...' })
    
    wx.downloadFile({
      url: photo.fullUrl,
      success: function(res) {
        if (res.statusCode === 200) {
          wx.saveImageToPhotosAlbum({
            filePath: res.tempFilePath,
            success: function() {
              wx.hideLoading()
              wx.showToast({
                title: '保存成功',
                icon: 'success'
              })
            },
            fail: function(error) {
              wx.hideLoading()
              console.error('保存图片失败:', error)
              wx.showToast({
                title: '保存失败',
                icon: 'none'
              })
            }
          })
        } else {
          wx.hideLoading()
          wx.showToast({
            title: '图片下载失败',
            icon: 'none'
          })
        }
      },
      fail: function(error) {
        wx.hideLoading()
        console.error('下载图片失败:', error)
        wx.showToast({
          title: '下载失败',
          icon: 'none'
        })
      }
    })
  },

  showPhotoDetail: function(photo) {
    var detailInfo = [
      '文件名: ' + (photo.original_filename || '未知'),
      '尺寸: ' + (photo.width && photo.height ? (photo.width + '×' + photo.height) : '未知'),
      '大小: ' + this.formatFileSize(photo.file_size),
      '上传时间: ' + this.formatDate(photo.created_at)
    ]
    
    if (photo.description) {
      detailInfo.unshift('描述: ' + photo.description)
    }
    
    wx.showModal({
      title: '照片详情',
      content: detailInfo.join('\n'),
      showCancel: false,
      confirmText: '确定'
    })
  },

  formatDate: function(dateString) {
    if (!dateString) return '未知时间'
    var date = new Date(dateString)
    return date.toLocaleString('zh-CN')
  }
}) 