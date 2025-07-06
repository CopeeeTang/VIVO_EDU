// 历史报告页面功能模块
class HistoryManager {
    constructor() {
        this.currentFilter = 'all';
        this.currentSort = 'date';
        this.selectedReportId = null;
        this.reports = [];
        this.init();
    }

    init() {
        this.loadReports();
        this.bindEvents();
        this.updateTime();
        this.updateStats();
        
        // 每秒更新时间
        setInterval(() => this.updateTime(), 1000);
    }

    bindEvents() {
        // 返回按钮
        this.bindBackButton();
        
        // 筛选标签
        this.bindFilterTabs();
        
        // 排序下拉菜单
        this.bindSortDropdown();
        
        // 报告卡片
        this.bindReportCards();
        
        // 菜单弹窗
        this.bindMenuModal();
        
        // 确认弹窗
        this.bindConfirmModal();
        
        // 点击外部关闭弹窗
        this.bindOutsideClick();
    }

    bindBackButton() {
        const backBtn = document.getElementById('backBtn');
        if (backBtn) {
            backBtn.addEventListener('click', () => {
                this.navigateBack();
            });
        }
    }

    bindFilterTabs() {
        const filterTabs = document.querySelectorAll('.filter-tab');
        filterTabs.forEach(tab => {
            tab.addEventListener('click', () => {
                this.handleFilterChange(tab.dataset.filter);
            });
        });
    }

    bindSortDropdown() {
        const sortBtn = document.getElementById('sortBtn');
        const sortMenu = document.getElementById('sortMenu');
        const sortOptions = document.querySelectorAll('.sort-option');
        
        if (sortBtn && sortMenu) {
            sortBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleSortMenu();
            });
        }
        
        sortOptions.forEach(option => {
            option.addEventListener('click', () => {
                this.handleSortChange(option.dataset.sort);
            });
        });
    }

    bindReportCards() {
        // 监听按钮点击
        document.addEventListener('click', (e) => {
            if (e.target.closest('.menu-btn')) {
                const reportId = e.target.closest('.menu-btn').dataset.reportId;
                this.showMenuModal(reportId);
            } else if (e.target.closest('.listen-btn')) {
                const reportId = e.target.closest('.listen-btn').dataset.reportId;
                this.handleListenReport(reportId);
            } else if (e.target.closest('.view-btn')) {
                const reportId = e.target.closest('.view-btn').dataset.reportId;
                this.handleViewReport(reportId);
            }
        });
    }

    bindMenuModal() {
        const menuModal = document.getElementById('menuModal');
        const menuClose = document.getElementById('menuClose');
        const menuOptions = document.querySelectorAll('.menu-option');
        
        if (menuClose) {
            menuClose.addEventListener('click', () => {
                this.hideMenuModal();
            });
        }
        
        menuOptions.forEach(option => {
            option.addEventListener('click', () => {
                const action = option.dataset.action;
                this.handleMenuAction(action);
            });
        });
    }

    bindConfirmModal() {
        const confirmCancel = document.getElementById('confirmCancel');
        const confirmDelete = document.getElementById('confirmDelete');
        
        if (confirmCancel) {
            confirmCancel.addEventListener('click', () => {
                this.hideConfirmModal();
            });
        }
        
        if (confirmDelete) {
            confirmDelete.addEventListener('click', () => {
                this.confirmDeleteReport();
            });
        }
    }

    bindOutsideClick() {
        document.addEventListener('click', (e) => {
            // 关闭排序菜单
            if (!e.target.closest('.sort-dropdown')) {
                this.hideSortMenu();
            }
        });
        
        // 点击弹窗背景关闭
        const menuOverlay = document.querySelector('.menu-overlay');
        const confirmOverlay = document.querySelector('.confirm-overlay');
        
        if (menuOverlay) {
            menuOverlay.addEventListener('click', () => {
                this.hideMenuModal();
            });
        }
        
        if (confirmOverlay) {
            confirmOverlay.addEventListener('click', () => {
                this.hideConfirmModal();
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

    loadReports() {
        // 从localStorage获取报告数据，或使用模拟数据
        const savedReports = localStorage.getItem('historyReports');
        if (savedReports) {
            this.reports = JSON.parse(savedReports);
        } else {
            this.reports = this.getMockReports();
        }
        
        this.renderReports();
    }

    getMockReports() {
        return [
            {
                id: '001',
                title: '胡图图_2025-07-04',
                status: 'analyzing',
                uploadTime: '刚刚上传',
                progress: 65,
                duration: '0:00',
                conflicts: 0,
                score: 0,
                summary: '正在分析中...',
                date: new Date('2025-07-04T15:30:00')
            },
            {
                id: '002',
                title: '胡图图_2025-07-03',
                status: 'completed',
                uploadTime: '昨天 15:30',
                duration: '37分33秒',
                conflicts: 3,
                score: 4.2,
                summary: '整体表现良好，在倾听和耐心方面表现出色',
                date: new Date('2025-07-03T15:30:00')
            },
            {
                id: '003',
                title: '胡图图_2025-07-02',
                status: 'completed',
                uploadTime: '3天前 20:45',
                duration: '42分15秒',
                conflicts: 2,
                score: 4.5,
                summary: '沟通技巧有所提升，建议继续保持积极的引导方式',
                date: new Date('2025-07-02T20:45:00')
            },
            {
                id: '004',
                title: '胡图图_2025-07-01',
                status: 'completed',
                uploadTime: '4天前 16:20',
                duration: '35分48秒',
                conflicts: 4,
                score: 3.8,
                summary: '在情绪管理方面需要加强，建议学习更多耐心沟通技巧',
                date: new Date('2025-07-01T16:20:00')
            },
            {
                id: '005',
                title: '胡图图_2025-06-30',
                status: 'completed',
                uploadTime: '5天前 14:15',
                duration: '28分22秒',
                conflicts: 1,
                score: 4.7,
                summary: '表现优秀，与孩子的互动非常和谐，值得继续保持',
                date: new Date('2025-06-30T14:15:00')
            }
        ];
    }

    updateStats() {
        const totalReports = this.reports.length;
        const completedReports = this.reports.filter(r => r.status === 'completed');
        
        // 计算总时长（小时）
        let totalMinutes = 0;
        completedReports.forEach(report => {
            const duration = report.duration;
            if (duration && duration !== '0:00') {
                const matches = duration.match(/(\d+)分(\d+)秒/);
                if (matches) {
                    totalMinutes += parseInt(matches[1]);
                }
            }
        });
        const totalHours = (totalMinutes / 60).toFixed(1);
        
        // 计算平均评分
        const scores = completedReports.filter(r => r.score > 0).map(r => r.score);
        const averageScore = scores.length > 0 ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1) : '0.0';
        
        // 更新显示
        const totalReportsEl = document.getElementById('totalReports');
        const totalDurationEl = document.getElementById('totalDuration');
        const averageScoreEl = document.getElementById('averageScore');
        
        if (totalReportsEl) totalReportsEl.textContent = totalReports;
        if (totalDurationEl) totalDurationEl.textContent = totalHours;
        if (averageScoreEl) averageScoreEl.textContent = averageScore;
    }

    renderReports() {
        const reportsList = document.getElementById('reportsList');
        const emptyState = document.getElementById('emptyState');
        
        if (!reportsList) return;
        
        // 过滤和排序报告
        let filteredReports = this.filterReports();
        filteredReports = this.sortReports(filteredReports);
        
        if (filteredReports.length === 0) {
            reportsList.style.display = 'none';
            if (emptyState) emptyState.style.display = 'block';
            return;
        }
        
        reportsList.style.display = 'flex';
        if (emptyState) emptyState.style.display = 'none';
        
        // 渲染报告卡片
        reportsList.innerHTML = filteredReports.map(report => this.createReportCard(report)).join('');
    }

    filterReports() {
        if (this.currentFilter === 'all') {
            return this.reports;
        }
        return this.reports.filter(report => report.status === this.currentFilter);
    }

    sortReports(reports) {
        return reports.sort((a, b) => {
            switch (this.currentSort) {
                case 'date':
                    return new Date(b.date) - new Date(a.date);
                case 'name':
                    return a.title.localeCompare(b.title);
                case 'duration':
                    return this.parseDuration(b.duration) - this.parseDuration(a.duration);
                default:
                    return 0;
            }
        });
    }

    parseDuration(duration) {
        if (!duration || duration === '0:00') return 0;
        const matches = duration.match(/(\d+)分(\d+)秒/);
        if (matches) {
            return parseInt(matches[1]) * 60 + parseInt(matches[2]);
        }
        return 0;
    }

    createReportCard(report) {
        if (report.status === 'analyzing') {
            return this.createAnalyzingCard(report);
        } else {
            return this.createCompletedCard(report);
        }
    }

    createAnalyzingCard(report) {
        return `
            <div class="report-card analyzing" data-report-id="${report.id}" data-status="analyzing">
                <div class="card-header">
                    <div class="report-icon analyzing-icon">
                        <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
                            <path d="M16 8V24M8 16H24" stroke="#FFA726" stroke-width="3" stroke-linecap="round"/>
                            <circle cx="16" cy="16" r="12" stroke="#FFA726" stroke-width="2" stroke-dasharray="4 4"/>
                        </svg>
                    </div>
                    <div class="report-meta">
                        <h3 class="report-title">${report.title}</h3>
                        <div class="report-subtitle">
                            <span class="status-badge analyzing">分析中</span>
                            <span class="upload-time">${report.uploadTime}</span>
                        </div>
                    </div>
                    <div class="card-menu">
                        <button class="menu-btn" data-report-id="${report.id}">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                                <circle cx="12" cy="12" r="1" fill="#738088"/>
                                <circle cx="12" cy="5" r="1" fill="#738088"/>
                                <circle cx="12" cy="19" r="1" fill="#738088"/>
                            </svg>
                        </button>
                    </div>
                </div>
                <div class="card-content">
                    <div class="progress-section">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${report.progress}%"></div>
                        </div>
                        <span class="progress-text">正在分析音频内容... ${report.progress}%</span>
                    </div>
                    <div class="action-section">
                        <button class="action-btn secondary" disabled>
                            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                                <path d="M9 1.5V16.5M1.5 9H16.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                            </svg>
                            等待分析完成
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    createCompletedCard(report) {
        return `
            <div class="report-card completed" data-report-id="${report.id}" data-status="completed">
                <div class="card-header">
                    <div class="report-icon completed-icon">
                        <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
                            <path d="M26.667 8L12 22.667L5.333 16" stroke="#4CAF50" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
                            <circle cx="16" cy="16" r="12" stroke="#4CAF50" stroke-width="2"/>
                        </svg>
                    </div>
                    <div class="report-meta">
                        <h3 class="report-title">${report.title}</h3>
                        <div class="report-subtitle">
                            <span class="status-badge completed">已完成</span>
                            <span class="upload-time">${report.uploadTime}</span>
                        </div>
                    </div>
                    <div class="card-menu">
                        <button class="menu-btn" data-report-id="${report.id}">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                                <circle cx="12" cy="12" r="1" fill="#738088"/>
                                <circle cx="12" cy="5" r="1" fill="#738088"/>
                                <circle cx="12" cy="19" r="1" fill="#738088"/>
                            </svg>
                        </button>
                    </div>
                </div>
                <div class="card-content">
                    <div class="report-summary">
                        <div class="summary-stats">
                            <div class="stat-box">
                                <div class="stat-icon duration">
                                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                                        <circle cx="8" cy="8" r="6" stroke="#9DBC98" stroke-width="1.5"/>
                                        <path d="M8 4V8L11 11" stroke="#9DBC98" stroke-width="1.5" stroke-linecap="round"/>
                                    </svg>
                                </div>
                                <span class="stat-value">${report.duration}</span>
                            </div>
                            <div class="stat-box">
                                <div class="stat-icon conflicts">
                                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                                        <path d="M8 1.5L2.5 13.5H13.5L8 1.5Z" stroke="#F87171" stroke-width="1.5" stroke-linejoin="round"/>
                                        <path d="M8 6V9" stroke="#F87171" stroke-width="1.5" stroke-linecap="round"/>
                                        <circle cx="8" cy="11.5" r="0.5" fill="#F87171"/>
                                    </svg>
                                </div>
                                <span class="stat-value">${report.conflicts}个冲突</span>
                            </div>
                            <div class="stat-box">
                                <div class="stat-icon score">
                                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                                        <path d="M8 1L10.09 5.26L15 6.11L11.5 9.59L12.18 14.5L8 12.27L3.82 14.5L4.5 9.59L1 6.11L5.91 5.26L8 1Z" fill="#FACC15"/>
                                    </svg>
                                </div>
                                <span class="stat-value">${report.score}分</span>
                            </div>
                        </div>
                        <div class="summary-text">
                            <p class="summary-highlight">${report.summary}</p>
                        </div>
                    </div>
                    <div class="action-section">
                        <button class="action-btn secondary listen-btn" data-report-id="${report.id}">
                            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                                <path d="M6.75 4.5L12.75 9L6.75 13.5V4.5Z" fill="currentColor"/>
                            </svg>
                            听录音
                        </button>
                        <button class="action-btn primary view-btn" data-report-id="${report.id}">
                            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                                <path d="M2.25 4.5H15.75V13.5H2.25V4.5Z" stroke="currentColor" stroke-width="1.5"/>
                                <path d="M6 7.5H12M6 10.5H10.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                            </svg>
                            查看报告
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    handleFilterChange(filter) {
        this.currentFilter = filter;
        
        // 更新标签状态
        document.querySelectorAll('.filter-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.filter === filter);
        });
        
        // 重新渲染报告
        this.renderReports();
    }

    toggleSortMenu() {
        const sortMenu = document.getElementById('sortMenu');
        if (sortMenu) {
            sortMenu.classList.toggle('active');
        }
    }

    hideSortMenu() {
        const sortMenu = document.getElementById('sortMenu');
        if (sortMenu) {
            sortMenu.classList.remove('active');
        }
    }

    handleSortChange(sort) {
        this.currentSort = sort;
        
        // 更新排序按钮文本
        const sortText = document.querySelector('.sort-text');
        if (sortText) {
            const sortNames = {
                'date': '按时间排序',
                'name': '按名称排序',
                'duration': '按时长排序'
            };
            sortText.textContent = sortNames[sort] || '按时间排序';
        }
        
        // 隐藏菜单
        this.hideSortMenu();
        
        // 重新渲染报告
        this.renderReports();
    }

    showMenuModal(reportId) {
        this.selectedReportId = reportId;
        const menuModal = document.getElementById('menuModal');
        if (menuModal) {
            menuModal.classList.add('active');
        }
    }

    hideMenuModal() {
        const menuModal = document.getElementById('menuModal');
        if (menuModal) {
            menuModal.classList.remove('active');
        }
        this.selectedReportId = null;
    }

    handleMenuAction(action) {
        const report = this.reports.find(r => r.id === this.selectedReportId);
        if (!report) return;
        
        switch (action) {
            case 'rename':
                this.handleRenameReport(report);
                break;
            case 'export':
                this.handleExportReport(report);
                break;
            case 'share':
                this.handleShareReport(report);
                break;
            case 'delete':
                this.showConfirmModal();
                return; // 不隐藏菜单，等待确认
        }
        
        this.hideMenuModal();
    }

    handleRenameReport(report) {
        const newName = prompt('请输入新的报告名称:', report.title);
        if (newName && newName.trim() && newName !== report.title) {
            report.title = newName.trim();
            this.saveReports();
            this.renderReports();
            this.showToast('报告重命名成功');
        }
    }

    handleExportReport(report) {
        // 模拟导出功能
        this.showToast('正在导出报告...');
        setTimeout(() => {
            this.showToast('报告导出成功');
        }, 2000);
    }

    handleShareReport(report) {
        // 模拟分享功能
        if (navigator.share) {
            navigator.share({
                title: report.title,
                text: `家庭教育报告：${report.summary}`,
                url: window.location.href
            }).catch(err => {
                console.log('分享失败:', err);
                this.showToast('分享功能暂不可用');
            });
        } else {
            // 复制链接到剪贴板
            navigator.clipboard.writeText(window.location.href).then(() => {
                this.showToast('链接已复制到剪贴板');
            }).catch(() => {
                this.showToast('分享功能暂不可用');
            });
        }
    }

    showConfirmModal() {
        const confirmModal = document.getElementById('confirmModal');
        if (confirmModal) {
            confirmModal.classList.add('active');
        }
    }

    hideConfirmModal() {
        const confirmModal = document.getElementById('confirmModal');
        if (confirmModal) {
            confirmModal.classList.remove('active');
        }
    }

    confirmDeleteReport() {
        const reportIndex = this.reports.findIndex(r => r.id === this.selectedReportId);
        if (reportIndex !== -1) {
            this.reports.splice(reportIndex, 1);
            this.saveReports();
            this.updateStats();
            this.renderReports();
            this.showToast('报告已删除');
        }
        
        this.hideConfirmModal();
        this.hideMenuModal();
    }

    handleListenReport(reportId) {
        // 模拟听录音功能
        this.showToast('正在加载录音文件...');
        setTimeout(() => {
            this.showToast('录音播放功能开发中...');
        }, 1000);
    }

    handleViewReport(reportId) {
        // 导航到报告详情页面
        window.location.href = `report.html?id=${reportId}`;
    }

    navigateBack() {
        // 返回主页
        window.location.href = 'home.html';
    }

    saveReports() {
        localStorage.setItem('historyReports', JSON.stringify(this.reports));
    }

    showToast(message) {
        // 创建提示消息
        const toast = document.createElement('div');
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 80px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--primary-color);
            color: white;
            padding: 12px 24px;
            border-radius: 25px;
            z-index: 4000;
            font-size: 14px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            animation: fadeInOut 3s ease-out;
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 3000);
    }

    // 模拟分析进度更新
    simulateAnalysisProgress() {
        const analyzingReports = this.reports.filter(r => r.status === 'analyzing');
        
        analyzingReports.forEach(report => {
            if (report.progress < 100) {
                report.progress = Math.min(100, report.progress + Math.random() * 5);
                
                if (report.progress >= 100) {
                    // 分析完成，转换为完成状态
                    report.status = 'completed';
                    report.duration = `${Math.floor(Math.random() * 50 + 20)}分${Math.floor(Math.random() * 60)}秒`;
                    report.conflicts = Math.floor(Math.random() * 5 + 1);
                    report.score = (Math.random() * 2 + 3).toFixed(1);
                    report.summary = '分析完成，报告已生成。建议查看详细分析结果。';
                    
                    this.showToast(`${report.title} 分析完成！`);
                }
            }
        });
        
        if (analyzingReports.length > 0) {
            this.saveReports();
            this.updateStats();
            this.renderReports();
        }
    }

    // 页面可见性变化处理
    handleVisibilityChange() {
        if (!document.hidden) {
            // 页面重新可见时更新时间和数据
            this.updateTime();
            this.loadReports();
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
class HistoryUtils {
    static formatTime(date) {
        const hours = date.getHours().toString().padStart(2, '0');
        const minutes = date.getMinutes().toString().padStart(2, '0');
        return `${hours}:${minutes}`;
    }

    static formatDate(date) {
        const now = new Date();
        const diffTime = now - date;
        const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays === 0) {
            return `今天 ${this.formatTime(date)}`;
        } else if (diffDays === 1) {
            return `昨天 ${this.formatTime(date)}`;
        } else if (diffDays < 7) {
            return `${diffDays}天前 ${this.formatTime(date)}`;
        } else {
            const year = date.getFullYear();
            const month = (date.getMonth() + 1).toString().padStart(2, '0');
            const day = date.getDate().toString().padStart(2, '0');
            return `${year}-${month}-${day}`;
        }
    }

    static debounce(func, delay) {
        let timeoutId;
        return function (...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    const historyManager = new HistoryManager();
    
    // 监听页面可见性变化
    document.addEventListener('visibilitychange', () => {
        historyManager.handleVisibilityChange();
    });
    
    // 监听网络状态变化
    window.addEventListener('online', () => {
        historyManager.handleNetworkChange();
    });
    
    window.addEventListener('offline', () => {
        historyManager.handleNetworkChange();
    });
    
    // 模拟分析进度更新（每5秒检查一次）
    setInterval(() => {
        historyManager.simulateAnalysisProgress();
    }, 5000);
    
    // 全局错误处理
    window.addEventListener('error', (event) => {
        console.error('页面错误:', event.error);
        historyManager.showToast('页面出现错误，请刷新重试');
    });
    
    // 页面卸载前的清理
    window.addEventListener('beforeunload', () => {
        // 保存当前状态
        historyManager.saveReports();
    });
});

// 添加 CSS 动画
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeInOut {
        0% { opacity: 0; transform: translate(-50%, -20px); }
        15% { opacity: 1; transform: translate(-50%, 0); }
        85% { opacity: 1; transform: translate(-50%, 0); }
        100% { opacity: 0; transform: translate(-50%, -20px); }
    }
`;
document.head.appendChild(style); 