/**
 * 报告主页面JavaScript
 * 处理数据获取、页面交互、图表渲染和导航功能
 */

// 报告页面管理对象
const ReportManager = {
    // 当前报告数据
    currentReport: null,
    
    // 页面元素
    elements: {
        recordingDuration: null,
        conflictCount: null,
        advantages: null,
        improvements: null,
        childName: null,
        educationCards: null,
        conflictChart: null,
        behaviorColumns: null,
        strategyCards: null,
        stepsSection: null
    },

    // 初始化
    init() {
        console.log('初始化报告页面...');
        this.bindElements();
        this.loadReportData();
        this.bindEvents();
        this.renderCharts();
    },

    // 绑定页面元素
    bindElements() {
        this.elements.recordingDuration = document.getElementById('recordingDuration');
        this.elements.conflictCount = document.getElementById('conflictCount');
        this.elements.advantages = document.getElementById('advantages');
        this.elements.improvements = document.getElementById('improvements');
        this.elements.childName = document.querySelector('.child-name');
        this.elements.educationCards = document.querySelectorAll('.education-card');
        this.elements.conflictChart = document.querySelector('.conflict-chart');
        this.elements.behaviorColumns = document.querySelectorAll('.behavior-column');
        this.elements.strategyCards = document.querySelectorAll('.strategy-card');
        this.elements.stepsSection = document.querySelector('.steps-section');
    },

    // 加载报告数据
    async loadReportData() {
        try {
            // 从localStorage获取报告ID或使用默认数据
            const reportId = localStorage.getItem('currentReportId');
            
            if (reportId) {
                // 从后端API获取报告数据
                const response = await fetch(`/api/reports/${reportId}`);
                if (response.ok) {
                    this.currentReport = await response.json();
                } else {
                    console.warn('无法获取报告数据，使用默认数据');
                    this.currentReport = this.getDefaultReportData();
                }
            } else {
                // 使用默认数据
                this.currentReport = this.getDefaultReportData();
            }
            
            this.renderReportData();
        } catch (error) {
            console.error('加载报告数据失败:', error);
            this.currentReport = this.getDefaultReportData();
            this.renderReportData();
        }
    },

    // 获取默认报告数据
    getDefaultReportData() {
        return {
            childName: '胡图图',
            recordingDate: '2025-05-06',
            recordingDuration: '37分60秒',
            conflictCount: 3,
            advantages: ['细心观察', '耐心引导', '积极鼓励', '情绪稳定', '善于沟通'],
            improvements: ['语言表达', '情绪控制', '规则意识', '专注力', '社交技能'],
            rating: {
                title: '细心的指挥大王',
                level: 'A',
                color: '#9DBC98'
            },
            educationOverview: {
                attitude: {
                    title: '教育态度和理念',
                    content: '家长展现出积极的教育态度，注重孩子的全面发展。'
                },
                behavior: {
                    title: '教育行为与方法',
                    content: '采用多元化的教育方法，注重实践与理论相结合。'
                },
                child: {
                    title: '孩子表现与状态',
                    content: '孩子在学习和生活中表现积极，但仍需加强自控能力。'
                }
            },
            conflicts: [
                {
                    id: 1,
                    time: '10:30',
                    emotion: -2,
                    description: '关于作业完成时间的争执'
                },
                {
                    id: 2,
                    time: '14:20',
                    emotion: -3,
                    description: '关于看电视时间的冲突'
                },
                {
                    id: 3,
                    time: '16:45',
                    emotion: -1,
                    description: '关于零食选择的分歧'
                }
            ],
            behaviors: {
                positive: ['主动给予表扬', '耐心解释原因', '提供选择机会', '及时响应需求'],
                negative: ['使用威胁言论', '强制性要求', '忽视情绪表达', '缺乏耐心']
            },
            strategies: {
                communication: [
                    '使用"我"语句表达感受',
                    '倾听孩子的想法和感受',
                    '避免使用负面标签',
                    '给予充分的表达时间',
                    '使用积极的语言引导'
                ],
                emotion: [
                    '保持冷静的语调',
                    '认识并接纳情绪',
                    '教授情绪管理技巧',
                    '提供情绪宣泄的方式',
                    '建立情绪调节的习惯'
                ]
            },
            steps: [
                {
                    number: 1,
                    content: '观察和记录孩子的行为模式，了解触发因素，建立行为观察日记，持续跟踪变化。'
                },
                {
                    number: 2,
                    content: '制定具体的行为改善计划，设定可达成的小目标，逐步引导孩子建立良好习惯。'
                },
                {
                    number: 3,
                    content: '定期评估进展情况，调整策略方法，保持耐心和一致性。'
                }
            ]
        };
    },

    // 渲染报告数据
    renderReportData() {
        if (!this.currentReport) return;

        const report = this.currentReport;
        
        // 更新基本信息
        if (this.elements.childName) {
            this.elements.childName.textContent = `${report.childName}_${report.recordingDate}`;
        }
        
        if (this.elements.recordingDuration) {
            this.elements.recordingDuration.textContent = report.recordingDuration;
        }
        
        if (this.elements.conflictCount) {
            this.elements.conflictCount.textContent = `${report.conflictCount}个`;
        }
        
        // 更新优势标签
        if (this.elements.advantages && report.advantages) {
            this.elements.advantages.innerHTML = report.advantages
                .map(advantage => `<span>${advantage}</span>`)
                .join('');
        }
        
        // 更新待提高标签
        if (this.elements.improvements && report.improvements) {
            this.elements.improvements.innerHTML = report.improvements
                .map(improvement => `<span>${improvement}</span>`)
                .join('');
        }
        
        // 更新评级
        const ratingTitle = document.querySelector('.rating-title');
        if (ratingTitle && report.rating) {
            ratingTitle.textContent = report.rating.title;
        }
        
        // 更新行为列表
        this.updateBehaviorLists(report.behaviors);
        
        // 更新策略列表
        this.updateStrategyLists(report.strategies);
        
        // 更新步骤列表
        this.updateStepsList(report.steps);
    },

    // 更新行为列表
    updateBehaviorLists(behaviors) {
        if (!behaviors) return;
        
        const positiveList = document.querySelector('.behavior-column.positive .behavior-list');
        const negativeList = document.querySelector('.behavior-column.negative .behavior-list');
        
        if (positiveList && behaviors.positive) {
            positiveList.innerHTML = behaviors.positive
                .map(behavior => `<div class="behavior-item">${behavior}</div>`)
                .join('');
        }
        
        if (negativeList && behaviors.negative) {
            negativeList.innerHTML = behaviors.negative
                .map(behavior => `<div class="behavior-item">${behavior}</div>`)
                .join('');
        }
    },

    // 更新策略列表
    updateStrategyLists(strategies) {
        if (!strategies) return;
        
        const communicationList = document.querySelector('.strategy-card:nth-child(1) .strategy-list');
        const emotionList = document.querySelector('.strategy-card:nth-child(2) .strategy-list');
        
        if (communicationList && strategies.communication) {
            communicationList.innerHTML = strategies.communication
                .map(strategy => `<li>${strategy}</li>`)
                .join('');
        }
        
        if (emotionList && strategies.emotion) {
            emotionList.innerHTML = strategies.emotion
                .map(strategy => `<li>${strategy}</li>`)
                .join('');
        }
    },

    // 更新步骤列表
    updateStepsList(steps) {
        if (!steps) return;
        
        const stepsList = document.querySelector('.steps-list');
        if (stepsList) {
            stepsList.innerHTML = steps
                .map(step => `
                    <div class="step-item">
                        <div class="step-number">${step.number}</div>
                        <div class="step-content">
                            <p>${step.content}</p>
                        </div>
                    </div>
                `)
                .join('');
        }
    },

    // 绑定事件
    bindEvents() {
        // 教育卡片点击事件
        this.elements.educationCards.forEach(card => {
            card.addEventListener('click', () => {
                const cardType = card.onclick.toString().match(/'([^']+)'/)[1];
                this.handleEducationCardClick(cardType);
            });
        });

        // 冲突标记点击事件
        const conflictMarkers = document.querySelectorAll('.conflict-marker');
        conflictMarkers.forEach(marker => {
            marker.addEventListener('click', () => {
                const conflictId = marker.dataset.conflictId || '1';
                this.handleConflictMarkerClick(conflictId);
            });
        });
        
        // 对话详情展开/收起
        const dialogueHeader = document.querySelector('.dialogue-header');
        if (dialogueHeader) {
            dialogueHeader.addEventListener('click', () => {
                this.toggleDialogueSection();
            });
        }
        
        // 音频播放器事件
        this.bindAudioEvents();
    },
    
    // 绑定音频播放器事件
    bindAudioEvents() {
        const playButton = document.getElementById('playButton');
        const progressBar = document.getElementById('progressBar');
        const speedButton = document.getElementById('speedButton');
        const volumeButton = document.getElementById('volumeButton');
        
        if (playButton) {
            playButton.addEventListener('click', () => {
                this.toggleAudio();
            });
        }
        
        if (progressBar) {
            progressBar.addEventListener('click', (e) => {
                const rect = progressBar.getBoundingClientRect();
                const percentage = (e.clientX - rect.left) / rect.width;
                this.seekAudio(percentage);
            });
        }
        
        if (speedButton) {
            speedButton.addEventListener('click', () => {
                this.toggleSpeed();
            });
        }
        
        if (volumeButton) {
            volumeButton.addEventListener('click', () => {
                this.toggleVolume();
            });
        }
    },
    
    // 切换对话详情展开/收起
    toggleDialogueSection() {
        const dialogueSection = document.querySelector('.dialogue-section');
        if (dialogueSection) {
            dialogueSection.classList.toggle('expanded');
            
            // 更新图标方向
            const icon = dialogueSection.querySelector('.section-icon');
            if (icon) {
                const isExpanded = dialogueSection.classList.contains('expanded');
                icon.style.transform = isExpanded ? 'rotate(0deg)' : 'rotate(-90deg)';
            }
        }
    },
    
    // 音频播放器状态
    audioState: {
        isPlaying: false,
        currentTime: 0,
        duration: 59, // 秒
        playbackRate: 1.0,
        volume: 1.0,
        progressInterval: null
    },
    
    // 切换音频播放/暂停
    toggleAudio() {
        const playButton = document.getElementById('playButton');
        const playIcon = playButton.querySelector('svg path');
        
        if (this.audioState.isPlaying) {
            this.pauseAudio();
            // 更新为播放图标
            playIcon.setAttribute('d', 'M4.5 2.25L13.5 9L4.5 15.75V2.25Z');
        } else {
            this.playAudio();
            // 更新为暂停图标
            playIcon.setAttribute('d', 'M6 4h2v10H6V4zm6 0h2v10h-2V4z');
        }
    },
    
    // 播放音频
    playAudio() {
        this.audioState.isPlaying = true;
        this.startProgressUpdate();
        console.log('开始播放音频');
    },
    
    // 暂停音频
    pauseAudio() {
        this.audioState.isPlaying = false;
        this.stopProgressUpdate();
        console.log('暂停音频');
    },
    
    // 跳转到指定位置
    seekAudio(percentage) {
        const newTime = this.audioState.duration * percentage;
        this.audioState.currentTime = newTime;
        this.updateProgress();
        console.log(`跳转到: ${newTime}秒`);
    },
    
    // 切换播放速度
    toggleSpeed() {
        const speedButton = document.getElementById('speedButton');
        const speedText = speedButton.querySelector('.speed-text');
        
        const speeds = [0.5, 1.0, 1.25, 1.5, 2.0];
        const currentIndex = speeds.indexOf(this.audioState.playbackRate);
        const nextIndex = (currentIndex + 1) % speeds.length;
        
        this.audioState.playbackRate = speeds[nextIndex];
        speedText.textContent = `${this.audioState.playbackRate}x`;
        
        console.log(`播放速度设置为: ${this.audioState.playbackRate}x`);
    },
    
    // 切换音量
    toggleVolume() {
        const volumeButton = document.getElementById('volumeButton');
        const volumeIcon = volumeButton.querySelector('svg');
        
        if (this.audioState.volume > 0) {
            this.audioState.volume = 0;
            // 静音图标
            volumeIcon.innerHTML = `
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5L6 9H2v6h4l5 4V5z"/>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M23 9l-6 6m0-6l6 6"/>
            `;
        } else {
            this.audioState.volume = 1.0;
            // 有音量图标
            volumeIcon.innerHTML = `
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5L6 9H2v6h4l5 4V5z"/>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.07 4.93a10 10 0 010 14.14M15.54 8.46a5 5 0 010 7.08"/>
            `;
        }
        
        console.log(`音量设置为: ${this.audioState.volume}`);
    },
    
    // 开始更新进度
    startProgressUpdate() {
        this.audioState.progressInterval = setInterval(() => {
            if (this.audioState.isPlaying) {
                this.audioState.currentTime += 0.1;
                if (this.audioState.currentTime >= this.audioState.duration) {
                    this.audioState.currentTime = this.audioState.duration;
                    this.pauseAudio();
                    const playButton = document.getElementById('playButton');
                    const playIcon = playButton.querySelector('svg path');
                    playIcon.setAttribute('d', 'M4.5 2.25L13.5 9L4.5 15.75V2.25Z');
                }
                this.updateProgress();
            }
        }, 100);
    },
    
    // 停止更新进度
    stopProgressUpdate() {
        if (this.audioState.progressInterval) {
            clearInterval(this.audioState.progressInterval);
            this.audioState.progressInterval = null;
        }
    },
    
    // 更新进度显示
    updateProgress() {
        const progressFill = document.getElementById('progressFill');
        const progressHandle = document.getElementById('progressHandle');
        const currentTimeEl = document.getElementById('currentTime');
        
        const percentage = (this.audioState.currentTime / this.audioState.duration) * 100;
        
        if (progressFill) {
            progressFill.style.width = `${percentage}%`;
        }
        
        if (progressHandle) {
            progressHandle.style.left = `${percentage}%`;
        }
        
        if (currentTimeEl) {
            currentTimeEl.textContent = this.formatTime(this.audioState.currentTime);
        }
    },
    
    // 格式化时间显示
    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    },

    // 处理教育卡片点击
    handleEducationCardClick(cardType) {
        console.log(`点击教育卡片: ${cardType}`);
        
        // 保存当前上下文
        localStorage.setItem('educationCardType', cardType);
        localStorage.setItem('reportContext', JSON.stringify(this.currentReport));
        
        // 跳转到教育全景详情页
        if (typeof App !== 'undefined' && App.navigateToEducationOverview) {
            App.navigateToEducationOverview(cardType);
        } else {
            window.location.href = 'education-overview.html';
        }
    },

    // 处理冲突标记点击
    handleConflictMarkerClick(conflictId) {
        console.log(`点击冲突标记: ${conflictId}`);
        
        // 保存当前上下文
        localStorage.setItem('conflictId', conflictId);
        localStorage.setItem('reportContext', JSON.stringify(this.currentReport));
        
        // 跳转到冲突分析详情页
        if (typeof App !== 'undefined' && App.navigateToConflictAnalysis) {
            App.navigateToConflictAnalysis(conflictId);
        } else {
            window.location.href = 'conflict-analysis.html';
        }
    },

    // 渲染图表
    renderCharts() {
        this.renderConflictChart();
        this.animateElements();
    },

    // 渲染冲突曲线图
    renderConflictChart() {
        if (!this.currentReport || !this.currentReport.conflicts) return;
        
        const chartCurve = document.querySelector('.chart-curve path');
        if (chartCurve) {
            // 根据冲突数据生成曲线路径
            const conflicts = this.currentReport.conflicts;
            const pathData = this.generateConflictPath(conflicts);
            chartCurve.setAttribute('d', pathData);
            
            // 添加动画效果
            const pathLength = chartCurve.getTotalLength();
            chartCurve.style.strokeDasharray = pathLength;
            chartCurve.style.strokeDashoffset = pathLength;
            
            // 触发动画
            setTimeout(() => {
                chartCurve.style.transition = 'stroke-dashoffset 2s ease-in-out';
                chartCurve.style.strokeDashoffset = '0';
            }, 500);
        }
    },

    // 生成冲突路径数据
    generateConflictPath(conflicts) {
        if (!conflicts || conflicts.length === 0) return '';
        
        const width = 269;
        const height = 179;
        const points = [];
        
        conflicts.forEach((conflict, index) => {
            const x = (index / (conflicts.length - 1)) * (width - 20) + 10;
            const y = height - ((conflict.emotion + 5) / 10) * (height - 20) - 10;
            points.push({ x, y });
        });
        
        if (points.length < 2) return '';
        
        let pathData = `M ${points[0].x} ${points[0].y}`;
        
        for (let i = 1; i < points.length; i++) {
            if (i === 1) {
                pathData += ` Q ${points[i].x} ${points[i].y}`;
            } else {
                pathData += ` Q ${points[i-1].x + (points[i].x - points[i-1].x) / 2} ${points[i-1].y} ${points[i].x} ${points[i].y}`;
            }
        }
        
        return pathData;
    },

    // 动画效果
    animateElements() {
        // 为卡片添加淡入动画
        const cards = document.querySelectorAll('.education-card, .strategy-card, .steps-card');
        cards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 100);
        });
        
        // 为评级徽章添加缩放动画
        const ratingBadge = document.querySelector('.rating-badge');
        if (ratingBadge) {
            ratingBadge.style.transform = 'scale(0)';
            setTimeout(() => {
                ratingBadge.style.transition = 'transform 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55)';
                ratingBadge.style.transform = 'scale(1)';
            }, 800);
        }
    },

    // 刷新数据
    async refreshData() {
        console.log('刷新报告数据...');
        await this.loadReportData();
        this.renderCharts();
    },

    // 导出报告
    exportReport() {
        if (!this.currentReport) {
            alert('没有可导出的报告数据');
            return;
        }
        
        const reportData = {
            ...this.currentReport,
            exportTime: new Date().toISOString(),
            version: '1.0'
        };
        
        const blob = new Blob([JSON.stringify(reportData, null, 2)], {
            type: 'application/json'
        });
        
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${this.currentReport.childName}_报告_${this.currentReport.recordingDate}.json`;
        link.click();
        
        URL.revokeObjectURL(url);
    },

    // 分享报告
    shareReport() {
        if (!this.currentReport) {
            alert('没有可分享的报告');
            return;
        }
        
        const shareData = {
            title: `${this.currentReport.childName}的家庭教育报告`,
            text: `查看${this.currentReport.childName}在${this.currentReport.recordingDate}的教育报告`,
            url: window.location.href
        };
        
        if (navigator.share) {
            navigator.share(shareData);
        } else {
            // 复制链接到剪贴板
            navigator.clipboard.writeText(window.location.href).then(() => {
                alert('报告链接已复制到剪贴板');
            });
        }
    }
};

// 扩展App对象的导航方法
if (typeof App !== 'undefined') {
    // 跳转到教育全景页面
    App.navigateToEducationOverview = function(cardType) {
        console.log(`导航到教育全景页面: ${cardType}`);
        this.navigateTo('education-overview');
    };
    
    // 跳转到冲突分析页面
    App.navigateToConflictAnalysis = function(conflictId) {
        console.log(`导航到冲突分析页面: ${conflictId}`);
        this.navigateTo('conflict-analysis');
    };
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    ReportManager.init();
});

// 导出为全局对象
window.ReportManager = ReportManager; 