/**
 * 家庭教育全景页面JavaScript
 * 处理数据加载、页面交互、动画效果和操作功能
 */

// 家庭教育全景管理对象
const EducationOverview = {
    // 当前报告数据
    currentData: null,
    
    // 页面元素
    elements: {
        attitudeContent: null,
        behaviorContent: null,
        childContent: null,
        summaryText: null,
        educationCards: null,
        detailSections: null
    },

    // 初始化
    init() {
        console.log('初始化家庭教育全景页面...');
        this.bindElements();
        this.loadEducationData();
        this.bindEvents();
        this.initAnimations();
    },

    // 绑定页面元素
    bindElements() {
        this.elements.attitudeContent = document.getElementById('attitudeContent');
        this.elements.behaviorContent = document.getElementById('behaviorContent');
        this.elements.childContent = document.getElementById('childContent');
        this.elements.summaryText = document.getElementById('summaryText');
        this.elements.educationCards = document.querySelectorAll('.education-card');
        this.elements.detailSections = document.querySelectorAll('.card-details');
    },

    // 加载教育数据
    async loadEducationData() {
        try {
            // 从localStorage获取报告上下文
            const reportContext = localStorage.getItem('reportContext');
            const cardType = localStorage.getItem('educationCardType');
            
            if (reportContext) {
                this.currentData = JSON.parse(reportContext);
            } else {
                // 从API获取数据或使用默认数据
                this.currentData = await this.fetchEducationData();
            }
            
            // 渲染页面数据
            this.renderEducationData();
            
            // 如果有特定的卡片类型，高亮显示
            if (cardType) {
                this.highlightCard(cardType);
            }
            
        } catch (error) {
            console.error('加载教育数据失败:', error);
            this.currentData = this.getDefaultEducationData();
            this.renderEducationData();
        }
    },

    // 从API获取教育数据
    async fetchEducationData() {
        try {
            const reportId = localStorage.getItem('currentReportId');
            if (reportId) {
                const response = await fetch(`/api/reports/${reportId}/education-overview`);
                if (response.ok) {
                    return await response.json();
                }
            }
        } catch (error) {
            console.error('API获取数据失败:', error);
        }
        
        return this.getDefaultEducationData();
    },

    // 获取默认教育数据
    getDefaultEducationData() {
        return {
            childName: '胡图图',
            recordingDate: '2025-05-06',
            attitude: {
                title: '教育态度和理念',
                summary: '家长展现出积极的教育态度，注重孩子的全面发展，尊重孩子的个性差异，强调品格教育的重要性。在教育理念上，倾向于民主式的教育方式，鼓励孩子独立思考和自主选择。',
                details: {
                    coreValues: '以孩子为中心，尊重个体差异，注重全面发展。',
                    educationPhilosophy: '培养孩子的自主性、创造性和责任感，建立正确的价值观念。',
                    expectations: '希望孩子能够健康快乐地成长，具备良好的品格和学习能力。'
                },
                insights: [
                    '教育态度积极正面，注重孩子的心理健康',
                    '重视品格教育，强调价值观的培养',
                    '期望与孩子能力匹配，目标设定合理'
                ]
            },
            behavior: {
                title: '教育行为与方法',
                summary: '在日常教育实践中，家长采用多元化的教育方法，注重实践与理论相结合。沟通方式以平等对话为主，管教策略相对温和，但在一致性方面还有改进空间。',
                details: {
                    communication: '采用平等对话，倾听孩子的想法，给予适当的引导和建议。',
                    discipline: '结合正面激励和规则约束，帮助孩子建立良好的行为习惯。',
                    guidance: '提供适合的学习环境，培养孩子的学习兴趣和学习方法。'
                },
                insights: [
                    '沟通方式民主平等，有利于亲子关系',
                    '管教策略相对温和，但需加强一致性',
                    '学习指导方法多样，注重兴趣培养'
                ]
            },
            child: {
                title: '孩子表现与状态',
                summary: '孩子在学习和生活中表现积极，具有较强的好奇心和学习热情。但在自控能力、专注力和情绪管理方面还需要进一步提升。社交能力良好，但处理冲突的技巧有待加强。',
                details: {
                    emotional: '孩子情绪波动较大，需要更多的情感支持和引导。',
                    academic: '学习态度积极，但专注力有待提高，需要更多的学习策略。',
                    social: '与同龄人相处良好，但在处理冲突时需要更多指导。'
                },
                insights: [
                    '学习态度积极，但专注力需要提升',
                    '情绪表达直接，需要情绪管理技巧',
                    '社交能力良好，冲突处理待改善'
                ]
            },
            summary: {
                overview: '综合分析显示，家庭教育环境整体积极健康，家长具备良好的教育理念和态度。在教育实践中表现出较强的包容性和引导性，但在规则一致性和情绪管理指导方面还有提升空间。孩子表现出良好的学习潜力和社交能力，需要在自控力和专注力方面进一步培养。',
                keyInsights: '家庭教育的核心在于建立良好的亲子关系，通过有效的沟通和引导，帮助孩子健康成长。',
                recommendations: '建议在教育过程中保持耐心和一致性，注重情感交流，给予孩子更多的理解和支持。'
            }
        };
    },

    // 渲染教育数据
    renderEducationData() {
        if (!this.currentData) return;

        const data = this.currentData;
        
        // 更新教育态度和理念内容
        if (this.elements.attitudeContent && data.attitude) {
            this.elements.attitudeContent.textContent = data.attitude.summary;
            this.updateDetailSection('attitudeDetails', data.attitude.details);
        }
        
        // 更新教育行为与方法内容
        if (this.elements.behaviorContent && data.behavior) {
            this.elements.behaviorContent.textContent = data.behavior.summary;
            this.updateDetailSection('behaviorDetails', data.behavior.details);
        }
        
        // 更新孩子表现与状态内容
        if (this.elements.childContent && data.child) {
            this.elements.childContent.textContent = data.child.summary;
            this.updateDetailSection('childDetails', data.child.details);
        }
        
        // 更新总结内容
        if (this.elements.summaryText && data.summary) {
            this.elements.summaryText.textContent = data.summary.overview;
            this.updateInsightsSection(data.summary);
        }
    },

    // 更新详情区域
    updateDetailSection(detailId, details) {
        const detailSection = document.getElementById(detailId);
        if (!detailSection || !details) return;

        const detailItems = detailSection.querySelectorAll('.detail-item');
        const detailKeys = Object.keys(details);
        
        detailItems.forEach((item, index) => {
            if (detailKeys[index]) {
                const textElement = item.querySelector('.detail-text');
                if (textElement) {
                    textElement.textContent = details[detailKeys[index]];
                }
            }
        });
    },

    // 更新洞察区域
    updateInsightsSection(summary) {
        const insightItems = document.querySelectorAll('.insight-item');
        
        if (insightItems.length >= 2) {
            const keyInsightText = insightItems[0].querySelector('.insight-text');
            const recommendationText = insightItems[1].querySelector('.insight-text');
            
            if (keyInsightText && summary.keyInsights) {
                keyInsightText.textContent = summary.keyInsights;
            }
            
            if (recommendationText && summary.recommendations) {
                recommendationText.textContent = summary.recommendations;
            }
        }
    },

    // 高亮显示特定卡片
    highlightCard(cardType) {
        const targetCard = document.querySelector(`[data-type="${cardType}"]`);
        if (targetCard) {
            targetCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
            targetCard.style.boxShadow = '0 0 20px rgba(157, 188, 152, 0.5)';
            
            setTimeout(() => {
                targetCard.style.boxShadow = '';
            }, 3000);
        }
    },

    // 绑定事件
    bindEvents() {
        // 卡片点击展开/收起详情
        this.elements.educationCards.forEach(card => {
            const cardTitle = card.querySelector('.card-title');
            if (cardTitle) {
                cardTitle.addEventListener('click', () => {
                    this.toggleCardDetails(card);
                });
                
                // 添加点击样式
                cardTitle.style.cursor = 'pointer';
                cardTitle.addEventListener('mouseenter', () => {
                    cardTitle.style.color = 'var(--primary-color)';
                });
                cardTitle.addEventListener('mouseleave', () => {
                    cardTitle.style.color = 'var(--black)';
                });
            }
        });

        // 监听页面可见性变化
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.refreshData();
            }
        });

        // 监听返回按钮
        const backButton = document.querySelector('.back-button');
        if (backButton) {
            backButton.addEventListener('click', () => {
                // 清除localStorage中的临时数据
                localStorage.removeItem('educationCardType');
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
        
        // 初始化音频播放器状态
        this.initAudioPlayer();
    },
    
    // 初始化音频播放器
    initAudioPlayer() {
        const totalTimeEl = document.getElementById('totalTime');
        const currentTimeEl = document.getElementById('currentTime');
        
        if (totalTimeEl) {
            totalTimeEl.textContent = this.formatTime(this.audioState.duration);
        }
        
        if (currentTimeEl) {
            currentTimeEl.textContent = this.formatTime(this.audioState.currentTime);
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

    // 切换卡片详情显示
    toggleCardDetails(card) {
        const cardDetails = card.querySelector('.card-details');
        if (cardDetails) {
            cardDetails.classList.toggle('collapsed');
            
            // 更新卡片状态
            const isCollapsed = cardDetails.classList.contains('collapsed');
            card.setAttribute('data-expanded', !isCollapsed);
        }
    },

    // 初始化动画
    initAnimations() {
        // 为卡片添加进入动画
        this.elements.educationCards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(30px)';
            
            setTimeout(() => {
                card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 200);
        });

        // 为总结区域添加动画
        const summarySection = document.querySelector('.summary-section');
        if (summarySection) {
            summarySection.style.opacity = '0';
            summarySection.style.transform = 'translateY(30px)';
            
            setTimeout(() => {
                summarySection.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                summarySection.style.opacity = '1';
                summarySection.style.transform = 'translateY(0)';
            }, this.elements.educationCards.length * 200);
        }

        // 添加加载动画
        this.showLoadingAnimation();
    },

    // 显示加载动画
    showLoadingAnimation() {
        this.elements.educationCards.forEach(card => {
            card.classList.add('card-loading');
            
            setTimeout(() => {
                card.classList.remove('card-loading');
            }, 1500);
        });
    },

    // 刷新数据
    async refreshData() {
        console.log('刷新教育全景数据...');
        await this.loadEducationData();
    },

    // 导出数据
    exportData() {
        if (!this.currentData) {
            alert('没有可导出的数据');
            return;
        }
        
        const exportData = {
            ...this.currentData,
            exportTime: new Date().toISOString(),
            pageType: 'education-overview',
            version: '1.0'
        };
        
        const blob = new Blob([JSON.stringify(exportData, null, 2)], {
            type: 'application/json'
        });
        
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `家庭教育全景_${this.currentData.childName}_${this.currentData.recordingDate}.json`;
        link.click();
        
        URL.revokeObjectURL(url);
        
        // 显示成功提示
        this.showNotification('数据导出成功！', 'success');
    },

    // 分享见解
    shareInsights() {
        if (!this.currentData || !this.currentData.summary) {
            alert('没有可分享的见解');
            return;
        }
        
        const shareText = `${this.currentData.childName}的家庭教育全景分析\n\n关键洞察：${this.currentData.summary.keyInsights}\n\n改进建议：${this.currentData.summary.recommendations}`;
        
        if (navigator.share) {
            navigator.share({
                title: '家庭教育全景分析',
                text: shareText,
                url: window.location.href
            });
        } else {
            // 复制到剪贴板
            navigator.clipboard.writeText(shareText).then(() => {
                this.showNotification('见解已复制到剪贴板！', 'success');
            }).catch(() => {
                // 降级方案
                const textArea = document.createElement('textarea');
                textArea.value = shareText;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                this.showNotification('见解已复制到剪贴板！', 'success');
            });
        }
    },

    // 显示通知
    showNotification(message, type = 'info') {
        // 创建通知元素
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? 'var(--primary-color)' : '#f44336'};
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            z-index: 9999;
            opacity: 0;
            transform: translateY(-20px);
            transition: opacity 0.3s ease, transform 0.3s ease;
        `;
        
        document.body.appendChild(notification);
        
        // 显示动画
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateY(0)';
        }, 100);
        
        // 自动隐藏
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateY(-20px)';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    EducationOverview.init();
});

// 导出为全局对象
window.EducationOverview = EducationOverview; 