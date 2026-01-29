Page({
  data: {
    password: '',
    showError: false,
    loginLoading: false,
    inputFocus: true
  },

  onLoad: function() {
    console.log('🔐 登录页面加载开始')
    
    // 检查是否已经登录
    var isLoggedIn = wx.getStorageSync('isLoggedIn')
    var token = wx.getStorageSync('token')
    
    console.log('🔍 检查登录状态:', {
      isLoggedIn: isLoggedIn,
      hasToken: !!token
    })
    
    if (isLoggedIn && token) {
      // 已登录，直接跳转到首页
      console.log('✅ 用户已登录，跳转到首页')
      wx.reLaunch({
        url: '/pages/home/home',
        success: function() {
          console.log('✅ 成功跳转到首页')
        },
        fail: function(error) {
          console.error('❌ 跳转失败:', error)
    }
      })
      return
    }
    
    console.log('📝 用户未登录，显示登录页面')
  },

  onShow: function() {
    // 页面显示时自动聚焦
    this.setData({ inputFocus: true })
  },

  focusInput: function() {
    var self = this
    // 点击密码点区域时重新聚焦输入框
    this.setData({ 
      inputFocus: false,
      showError: false 
    }, function() {
      // 重新设置焦点
      setTimeout(function() {
        self.setData({ inputFocus: true })
      }, 100)
    })
  },

  onPasswordInput: function(e) {
    var self = this
    var value = e.detail.value
    
    // 限制只能输入数字，最多4位
    if (!/^\d*$/.test(value) || value.length > 4) {
      return
    }
    
    this.setData({
      password: value,
      showError: false
    })
    
    // 当输入4位密码时自动验证
    if (value.length === 4) {
      // 失去焦点，避免键盘干扰验证界面
      this.setData({ inputFocus: false })
      
      setTimeout(function() {
        self.autoLogin()
      }, 300) // 延迟300ms，让用户看到第4个点的填充动画
    }
  },

  autoLogin: function() {
    var self = this
    var password = this.data.password
    
    if (password.length !== 4) {
      return
    }

    if (this.data.loginLoading) {
      return // 防止重复提交
    }

    this.setData({ loginLoading: true })

    // 调用后端API验证密码
    var app = getApp()
    app.request({
      url: '/auth/login',
      method: 'POST',
      data: {
        password: password
      }
    }).then(function(response) {
      if (response.access_token) {
        // 密码正确，保存登录状态和token
        wx.setStorageSync('isLoggedIn', true)
        wx.setStorageSync('loginTime', Date.now())
        wx.setStorageSync('token', response.access_token)
        
        console.log('✅ 登录成功，即将跳转到首页')
      
        // 确保存储同步完成后再跳转
        setTimeout(function() {
          wx.reLaunch({
        url: '/pages/home/home',
            success: function() {
              console.log('✅ 跳转到首页成功')
          wx.showToast({
                title: '登录成功 ✨',
                icon: 'none',
                duration: 1500
          })
            },
            fail: function(error) {
              console.error('❌ 跳转到首页失败:', error)
        }
      })
        }, 100)
      }
    }).catch(function(error) {
      console.error('登录失败:', error)
      // 密码错误或网络错误
      self.handleLoginError(error)
    }).finally(function() {
      self.setData({ loginLoading: false })
    })
  },

  handleLoginError: function(error) {
    var self = this
      this.setData({
        showError: true,
        password: ''
      })
      
    var errorMsg = '登录失败，请重试'
    if (error.message && error.message.includes('401')) {
      errorMsg = '密码错误'
    } else if (error.message && error.message.includes('network')) {
      errorMsg = '网络连接失败'
    }
    
    wx.showToast({
      title: JSON.stringify(error),
      icon: 'none',
      duration: 20000
    })
    
    // 震动反馈
    wx.vibrateShort()
    
    // 3秒后隐藏错误提示，并重新聚焦
    setTimeout(function() {
      self.setData({ 
        showError: false,
        inputFocus: true 
      })
    }, 3000)
  }
}) 