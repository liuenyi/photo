App({
  globalData: {
    // apiBaseUrl: 'http://192.168.3.94:8000/api',
    // imageBaseUrl: 'http://192.168.3.94:8000',
    apiBaseUrl: 'https://photo.liuenyi.com/api',
    imageBaseUrl: 'https://photo.liuenyi.com',
    isLoggedIn: false
  },

  onLaunch: function() {
    console.log('[启动] 咱家的记忆应用启动')
    
    // 检查网络状态
    wx.getNetworkType({
      success: function(res) {
        console.log('[网络] 网络类型:', res.networkType)
        if (res.networkType === 'none') {
          wx.showToast({
            title: '网络连接失败',
            icon: 'none'
          })
        }
      }
    })
    
    // 检查更新
    if (wx.getUpdateManager) {
      var updateManager = wx.getUpdateManager()
      if (updateManager.onCheckForUpdate) {
        updateManager.onCheckForUpdate(function(res) {
          if (res.hasUpdate) {
            console.log('[更新] 发现新版本')
          }
        })
      }
    }
    
    // 监听网络状态变化
    wx.onNetworkStatusChange(function(res) {
      console.log('[网络] 网络状态变化:', res.isConnected, res.networkType)
    })
  },

  onShow: function() {
    console.log('[显示] 应用进入前台')
  },

  onHide: function() {
    console.log('[隐藏] 应用进入后台')
  },

  request: function(options) {
    var self = this
    var token = wx.getStorageSync('token')
    
    return new Promise(function(resolve, reject) {
      var requestData = {
        url: self.globalData.apiBaseUrl + options.url,
        method: options.method || 'GET',
        data: options.data || {},
        header: {
          'Content-Type': 'application/json'
        },
        success: function(res) {
          console.log('[请求] 响应状态:', res.statusCode, '数据:', res.data)
          
          if (res.statusCode === 200) {
            // 检查响应内容是否包含认证错误信息
            if (res.data && typeof res.data === 'object') {
              var responseStr = JSON.stringify(res.data).toLowerCase()
              console.log('[认证] 检查响应内容:', responseStr)
              
              if (responseStr.includes('not authenticated') || 
                  responseStr.includes('无效的认证') || 
                  responseStr.includes('authentication') ||
                  res.data.detail === 'Not authenticated') {
                console.log('[认证] 🚨 检测到认证错误响应，清除登录状态')
                self.clearLoginState()
                reject(new Error('认证失效'))
                return
              }
            }
            resolve(res.data)
          } else if (res.statusCode === 401 || res.statusCode === 403) {
            // HTTP 401/403 认证失效
            console.log('[认证] 🚨 HTTP认证失效 ' + res.statusCode + '，清除登录状态')
            self.clearLoginState()
            reject(new Error('认证失效'))
          } else {
            console.error('[请求] 请求失败:', res)
            reject(new Error('请求失败: ' + res.statusCode))
          }
        },
        fail: function(error) {
          console.error('[请求] 网络错误:', error)
          reject(error)
        }
      }
      
      // 添加认证token
      if (token) {
        requestData.header['Authorization'] = 'Bearer ' + token
      }
      
      wx.request(requestData)
    })
  },

  // 清除登录状态的统一方法
  clearLoginState: function() {
    console.log('[认证] 🧹 清除登录状态')
    
    // 检查当前状态
    var currentLoggedIn = wx.getStorageSync('isLoggedIn')
    var currentToken = wx.getStorageSync('token')
    console.log('[认证] 清除前状态:', { isLoggedIn: currentLoggedIn, hasToken: !!currentToken })
    
    wx.removeStorageSync('token')
    wx.removeStorageSync('isLoggedIn')
    wx.removeStorageSync('loginTime')
    this.globalData.isLoggedIn = false
    
    console.log('[认证] ✅ 登录状态已清除，页面将自动检测并跳转')
    
    // 不在这里跳转，让页面自己检测状态变化来跳转
    // 触发一个自定义事件，通知页面状态已清除
    if (typeof this.onLoginStateCleared === 'function') {
      this.onLoginStateCleared()
    }
  },

  // 全局分享配置
  onShareAppMessage: function() {
    return {
      title: '🎈 咱家的记忆 - 珍藏美好回忆',
      desc: '一个精美的私人相册小程序，记录生活中的美好瞬间',
      path: '/pages/home/home',
      imageUrl: ''
    }
  },

  onShareTimeline: function() {
    return {
      title: '🎈 咱家的记忆 - 珍藏美好回忆',
      query: '',
      imageUrl: ''
    }
  }
}) 