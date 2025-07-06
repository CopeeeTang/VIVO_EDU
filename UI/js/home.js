/**
 * 主页面JavaScript功能
 * 处理主页面的各种交互功能和数据显示
 */

(function() {
    'use strict';
    
    // 主页面功能模块
    class HomeManager {
        constructor() {
            this.currentUser = null;
            this.init();
        }

        init() {
            this.loadUserInfo();
            this.bindEvents();
            this.updateTime();
            this.loadDailyQuote();
            
            // 每秒更新时间
            setInterval(() => this.updateTime(), 1000);
        }

        bindEvents() {
            // 功能卡片点击事件
            this.bindFunctionCards();
            
            // 专家卡片点击事件
            this.bindExpertCards();
            
            // 教育资源卡片点击事件
            this.bindResourceCards();
            
            // 查看全部链接点击事件
            this.bindViewAllLinks();
            
            // 历史报告预览点击事件
            this.bindHistoryPreview();
        }

        bindFunctionCards() {
            const recordingCard = document.querySelector('.recording-card');
            const uploadCard = document.querySelector('.upload-card');
            
            if (recordingCard) {
                recordingCard.addEventListener('click', () => {
                    this.handleFunctionClick('recording');
                });
            }
            
            if (uploadCard) {
                uploadCard.addEventListener('click', () => {
                    this.handleFunctionClick('upload');
                });
            }
        }

        bindExpertCards() {
            const expertCards = document.querySelectorAll('.expert-card');
            const expertActions = document.querySelectorAll('.expert-action');
            
            expertCards.forEach((card, index) => {
                card.addEventListener('click', (e) => {
                    // 如果点击的是操作按钮，则触发专家联系
                    if (e.target.closest('.expert-action')) {
                        this.handleExpertContact(index);
                    } else {
                        this.handleExpertView(index);
                    }
                });
            });
        }

        bindResourceCards() {
            const resourceCards = document.querySelectorAll('.resource-card');
            
            resourceCards.forEach((card, index) => {
                card.addEventListener('click', () => {
                    this.handleResourceView(index);
                });
            });
        }

        bindViewAllLinks() {
            const viewAllLinks = document.querySelectorAll('.view-all-link');
            
            viewAllLinks.forEach(link => {
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    const section = link.closest('.expert-section, .resource-section');
                    
                    if (section.classList.contains('expert-section')) {
                        this.handleViewAllExperts();
                    } else if (section.classList.contains('resource-section')) {
                        this.handleViewAllResources();
                    }
                });
            });
        }

        bindHistoryPreview() {
            const viewAll = document.querySelector('.view-all');
            const previewCard = document.querySelector('.preview-card');
            
            if (viewAll) {
                viewAll.addEventListener('click', () => {
                    this.handleViewAllReports();
                });
            }
            
            if (previewCard) {
                previewCard.addEventListener('click', () => {
                    this.handlePreviewReportClick();
                });
            }
        }

        updateTime() {
            const timeElement = document.querySelector('.time');
            if (timeElement) {
                const now = new Date();
                const hours = now.getHours().toString().padStart(2, '0');
                const minutes = now.getMinutes().toString().padStart(2, '0');
                timeElement.textContent = `${hours}:${minutes}`;
            }
        }

        loadUserInfo() {
            // 从localStorage获取用户信息
            const userInfo = localStorage.getItem('userInfo');
            if (userInfo) {
                this.currentUser = JSON.parse(userInfo);
                this.updateUserDisplay();
            }
            
            // 更新进阶天数
            this.updateProgressDays();
        }

        updateUserDisplay() {
            const greetingText = document.querySelector('.greeting-text');
            if (greetingText && this.currentUser) {
                const hour = new Date().getHours();
                let greeting = '您好';
                
                if (hour < 12) {
                    greeting = '早上好';
                } else if (hour < 18) {
                    greeting = '下午好';
                } else {
                    greeting = '晚上好';
                }
                
                greetingText.textContent = `${greeting}, ${this.currentUser.name || 'Martina'}`;
            }
        }

        updateProgressDays() {
            const progressDay = document.querySelector('.progress-day');
            if (progressDay) {
                // 计算用户注册天数（这里使用模拟数据）
                const registrationDate = new Date('2024-01-01');
                const currentDate = new Date();
                const daysDiff = Math.floor((currentDate - registrationDate) / (1000 * 60 * 60 * 24));
                
                progressDay.textContent = `今天是你向辅导专家进阶的第${daysDiff}天`;
            }
        }

        async loadDailyQuote() {
            const quoteContent = document.querySelector('.quote-content');
            if (quoteContent) {
                try {
                    // 这里可以调用API获取每日一句，目前使用本地数据
                    const quotes = [
                        '教育的本质意味着：一棵树摇动另一棵树，一朵云推动另一朵云，一个灵魂唤醒另一个灵魂。',
                        '家庭是孩子的第一所学校，父母是孩子的第一任老师。',
                        '每一个孩子都是独一无二的，需要用心去发现他们的特质和潜能。',
                        '倾听是最好的教育方式，理解是最深的关爱表达。',
                        '陪伴是最长情的告白，耐心是最好的教育态度。'
                    ];
                    
                    const randomQuote = quotes[Math.floor(Math.random() * quotes.length)];
                    quoteContent.textContent = randomQuote;
                } catch (error) {
                    console.error('加载每日一句失败:', error);
                }
            }
        }

        handleFunctionClick(type) {
            this.showLoadingState();
            
            switch (type) {
                case 'recording':
                    this.navigateToRecording();
                    break;
                case 'upload':
                    this.navigateToUpload();
                    break;
                default:
                    console.warn('未知功能类型:', type);
            }
        }

        navigateToRecording() {
            // 添加过渡动画
            const recordingCard = document.querySelector('.recording-card');
            if (recordingCard) {
                recordingCard.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    window.location.href = 'recording.html';
                }, 200);
            }
        }

        navigateToUpload() {
            // 添加过渡动画
            const uploadCard = document.querySelector('.upload-card');
            if (uploadCard) {
                uploadCard.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    window.location.href = 'upload.html';
                }, 200);
            }
        }

        handleExpertView(index) {
            console.log('查看专家详情:', index);
            // 这里可以导航到专家详情页面
            this.showToast('专家详情页面开发中...');
        }

        handleExpertContact(index) {
            console.log('联系专家:', index);
            // 这里可以打开联系专家的功能
            this.showToast('专家联系功能开发中...');
        }

        handleResourceView(index) {
            console.log('查看教育资源:', index);
            // 这里可以导航到资源详情页面
            this.showToast('教育资源详情页面开发中...');
        }

        handleViewAllExperts() {
            console.log('查看所有专家');
            // 这里可以导航到专家列表页面
            this.showToast('专家列表页面开发中...');
        }

        handleViewAllResources() {
            console.log('查看所有教育资源');
            // 这里可以导航到资源列表页面
            this.showToast('教育资源列表页面开发中...');
        }

        handleViewAllReports() {
            // 导航到历史报告页面
            window.location.href = 'history.html';
        }

        handlePreviewReportClick() {
            // 导航到具体报告页面
            window.location.href = 'report.html';
        }

        showLoadingState() {
            const body = document.body;
            body.classList.add('loading');
            
            setTimeout(() => {
                body.classList.remove('loading');
            }, 2000);
        }

        showToast(message) {
            // 创建提示消息
            const toast = document.createElement('div');
            toast.textContent = message;
            toast.style.cssText = `
                position: fixed;
                top: 20px;
                left: 50%;
                transform: translateX(-50%);
                background: var(--primary-color);
                color: white;
                padding: 12px 24px;
                border-radius: 25px;
                z-index: 3000;
                font-size: 14px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
                animation: fadeIn 0.3s ease-out;
            `;
            
            document.body.appendChild(toast);
            
            setTimeout(() => {
                toast.style.animation = 'fadeOut 0.3s ease-out';
                setTimeout(() => {
                    if (toast.parentNode) {
                        toast.remove();
                    }
                }, 300);
            }, 2000);
        }

        // 页面可见性变化时的处理
        handleVisibilityChange() {
            if (!document.hidden) {
                // 页面重新可见时更新时间和用户信息
                this.updateTime();
                this.updateUserDisplay();
            }
        }

        // 网络状态变化处理
        handleNetworkChange() {
            if (navigator.onLine) {
                this.showToast('网络连接已恢复');
            } else {
                this.showToast('网络连接已断开');
            }
        }
    }

    // 工具函数
    class HomeUtils {
        static formatTime(date) {
            const hours = date.getHours().toString().padStart(2, '0');
            const minutes = date.getMinutes().toString().padStart(2, '0');
            return `${hours}:${minutes}`;
        }

        static formatDate(date) {
            const year = date.getFullYear();
            const month = (date.getMonth() + 1).toString().padStart(2, '0');
            const day = date.getDate().toString().padStart(2, '0');
            return `${year}-${month}-${day}`;
        }

        static debounce(func, delay) {
            let timeoutId;
            return function (...args) {
                clearTimeout(timeoutId);
                timeoutId = setTimeout(() => func.apply(this, args), delay);
            };
        }

        static throttle(func, limit) {
            let inThrottle;
            return function (...args) {
                if (!inThrottle) {
                    func.apply(this, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            };
        }
    }

    // 页面加载完成后初始化
    document.addEventListener('DOMContentLoaded', () => {
        const homeManager = new HomeManager();
        
        // 监听页面可见性变化
        document.addEventListener('visibilitychange', () => {
            homeManager.handleVisibilityChange();
        });
        
        // 监听网络状态变化
        window.addEventListener('online', () => {
            homeManager.handleNetworkChange();
        });
        
        window.addEventListener('offline', () => {
            homeManager.handleNetworkChange();
        });
        
        // 监听页面尺寸变化
        window.addEventListener('resize', HomeUtils.debounce(() => {
            // 处理响应式布局调整
            homeManager.handleResize();
        }, 250));
        
        // 全局错误处理
        window.addEventListener('error', (event) => {
            console.error('页面错误:', event.error);
            homeManager.showToast('页面出现错误，请刷新重试');
        });
        
        // 页面卸载前的清理
        window.addEventListener('beforeunload', () => {
            // 清理定时器等资源
            console.log('页面即将卸载');
        });
    });

    // 添加 CSS 动画
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes fadeOut {
            from { opacity: 1; transform: translateY(0); }
            to { opacity: 0; transform: translateY(-10px); }
        }
        
        .loading {
            pointer-events: none;
            opacity: 0.7;
        }
        
        .loading * {
            cursor: wait !important;
        }
    `;
    document.head.appendChild(style);
})(); 