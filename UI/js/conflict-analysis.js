/**
 * 冲突场景剖析页面JavaScript
 * 处理数据加载、冲突切换、对话详情、情绪评估、分析功能和操作处理
 */

// 冲突场景剖析管理对象
const ConflictAnalysis = {
    // 当前数据
    currentData: null,
    currentConflictId: 1,
    
    // 页面元素
    elements: {
        eventName: null,
        conflictTabs: null,
        conflictActiveBackground: null,
        reviewContent: null,
        coreContent: null,
        emotionContent: null,
        dialogueContent: null,
        emotionValue: null,
        analysisCards: null
    },

    // 初始化
    init() {
        console.log('初始化冲突场景剖析页面...');
        this.bindElements();
        this.loadConflictData();
        this.bindEvents();
        this.initAnimations();
        this.initAudioPlayer();
    },

    // 绑定页面元素
    bindElements() {
        this.elements.eventName = document.getElementById('eventName');
        this.elements.conflictTabs = document.querySelectorAll('.conflict-tab');
        this.elements.conflictActiveBackground = document.querySelector('.conflict-active-bg');
        this.elements.reviewContent = document.getElementById('reviewContent');
        this.elements.coreContent = document.getElementById('coreContent');
        this.elements.emotionContent = document.getElementById('emotionContent');
        this.elements.dialogueContent = document.getElementById('dialogueContent');
        this.elements.emotionValue = document.getElementById('emotionValue');
        this.elements.analysisCards = document.querySelectorAll('.analysis-card');
    },

    // 加载冲突数据
    async loadConflictData() {
        try {
            // 从localStorage获取冲突上下文
            const conflictContext = localStorage.getItem('conflictContext');
            const conflictId = localStorage.getItem('selectedConflictId');
            
            if (conflictContext) {
                this.currentData = JSON.parse(conflictContext);
            } else {
                // 从API获取数据或使用默认数据
                this.currentData = await this.fetchConflictData();
            }
            
            if (conflictId) {
                this.currentConflictId = parseInt(conflictId);
            }
            
            // 渲染页面数据
            this.renderConflictData();
            this.switchConflict(this.currentConflictId);
            
        } catch (error) {
            console.error('加载冲突数据失败:', error);
            this.currentData = this.getDefaultConflictData();
            this.renderConflictData();
        }
    },

    // 从API获取冲突数据
    async fetchConflictData() {
        try {
            const reportId = localStorage.getItem('currentReportId');
            if (reportId) {
                const response = await fetch(`/api/reports/${reportId}/conflicts`);
                if (response.ok) {
                    return await response.json();
                }
            }
        } catch (error) {
            console.error('API获取数据失败:', error);
        }
        
        return this.getDefaultConflictData();
    },

    // 获取默认冲突数据
    getDefaultConflictData() {
        return {
            eventName: '关于作业和电视时间的亲子冲突',
            conflicts: {
                1: {
                    id: 1,
                    title: '冲突1',
                    time: '10:30',
                    emotionLevel: 0.59,
                    analysis: {
                        review: '此次冲突起因于孩子对作业时间的安排不合理，导致与看电视时间产生冲突。家长在发现问题后，采用了直接质疑的方式，孩子则表现出防御性回应。整个过程中，双方的情绪都有所波动，但最终孩子选择了妥协。',
                        core: '核心问题在于时间管理和期望设定的不一致。家长希望孩子能够准确完成作业，而孩子可能对时间概念还不够清晰。双方缺乏有效的沟通机制来解决这类分歧。',
                        emotion: '情绪波动主要体现在家长的质疑态度和孩子的防御反应上。家长的语气带有明显的不满情绪，而孩子从辩解转为解释，最后选择默认，显示出一定的情绪压抑。'
                    },
                    dialogue: [
                        {
                            role: '家长',
                            type: 'parent',
                            emotion: '质问',
                            content: '李晨曦就是这样撒谎吗？你这个6是6吗？'
                        },
                        {
                            role: '孩子',
                            type: 'child',
                            emotion: '辩解',
                            content: '不行吗？我记错了。'
                        },
                        {
                            role: '孩子',
                            type: 'child',
                            emotion: '解释',
                            content: '我不是故意的。'
                        },
                        {
                            role: '孩子',
                            type: 'child',
                            emotion: '默认',
                            content: '我以后会注意的。'
                        },
                        {
                            role: '家长',
                            type: 'parent',
                            emotion: '情绪化指责',
                            content: '以后你就得不到姥姥的爱了。那就这样吧。'
                        },
                        {
                            role: '家长',
                            type: 'parent',
                            emotion: '情绪化指责',
                            content: '姥姥最讨厌撒谎的人了。'
                        }
                    ]
                },
                2: {
                    id: 2,
                    title: '冲突2',
                    time: '14:20',
                    emotionLevel: 0.73,
                    analysis: {
                        review: '第二次冲突发生在下午，主要围绕孩子的学习安排和休息时间分配。家长对孩子的自主安排表示不满，孩子则表现出一定的抵触情绪。',
                        core: '核心问题是自主权与监管权的平衡。孩子希望有更多的自主选择权，而家长担心孩子的自控能力不足。',
                        emotion: '情绪强度较第一次冲突有所增加，双方都表现出更明显的情绪波动。'
                    },
                    dialogue: [
                        {
                            role: '家长',
                            type: 'parent',
                            emotion: '担忧',
                            content: '你这样安排时间真的合适吗？'
                        },
                        {
                            role: '孩子',
                            type: 'child',
                            emotion: '抵触',
                            content: '我觉得没问题啊。'
                        },
                        {
                            role: '家长',
                            type: 'parent',
                            emotion: '坚持',
                            content: '但是这样会影响你的学习效果。'
                        },
                        {
                            role: '孩子',
                            type: 'child',
                            emotion: '妥协',
                            content: '那我调整一下吧。'
                        }
                    ]
                },
                3: {
                    id: 3,
                    title: '冲突3',
                    time: '16:45',
                    emotionLevel: 0.42,
                    analysis: {
                        review: '第三次冲突相对温和，主要是关于日常生活习惯的小分歧。双方都表现出较好的沟通意愿，冲突得到了较快的解决。',
                        core: '核心问题是生活习惯的养成和规则的执行。虽然有分歧，但双方都愿意通过沟通来解决。',
                        emotion: '情绪波动最小，显示出良好的情绪管理能力。'
                    },
                    dialogue: [
                        {
                            role: '家长',
                            type: 'parent',
                            emotion: '提醒',
                            content: '记得要按时整理房间哦。'
                        },
                        {
                            role: '孩子',
                            type: 'child',
                            emotion: '承诺',
                            content: '好的，我等会就整理。'
                        },
                        {
                            role: '家长',
                            type: 'parent',
                            emotion: '鼓励',
                            content: '很好，你这样做妈妈很开心。'
                        }
                    ]
                }
            }
        };
    },

    // 渲染冲突数据
    renderConflictData() {
        if (!this.currentData) return;

        // 更新事件名称
        if (this.elements.eventName) {
            this.elements.eventName.textContent = this.currentData.eventName;
        }
    },

    // 切换冲突
    switchConflict(conflictId) {
        this.currentConflictId = conflictId;
        const conflictData = this.currentData.conflicts[conflictId];
        
        if (!conflictData) return;

        // 更新标签状态
        this.updateConflictTabs(conflictId);
        
        // 更新分析内容
        this.updateAnalysisContent(conflictData);
        
        // 更新对话内容
        this.updateDialogueContent(conflictData);
        
        // 更新情绪值
        this.updateEmotionGauge(conflictData.emotionLevel);
        
        // 添加动画效果
        this.animateCardUpdate();
    },

    // 更新冲突标签状态
    updateConflictTabs(activeId) {
        this.elements.conflictTabs.forEach(tab => {
            tab.classList.remove('active');
            if (parseInt(tab.dataset.conflict) === activeId) {
                tab.classList.add('active');
            }
        });
        
        // 更新背景位置
        if (this.elements.conflictActiveBackground) {
            this.elements.conflictActiveBackground.className = 
                `conflict-active-bg tab-${activeId}`;
        }
    },

    // 更新分析内容
    updateAnalysisContent(conflictData) {
        const { analysis } = conflictData;
        
        if (this.elements.reviewContent && analysis.review) {
            this.elements.reviewContent.textContent = analysis.review;
        }
        
        if (this.elements.coreContent && analysis.core) {
            this.elements.coreContent.textContent = analysis.core;
        }
        
        if (this.elements.emotionContent && analysis.emotion) {
            this.elements.emotionContent.textContent = analysis.emotion;
        }
    },

    // 更新对话内容
    updateDialogueContent(conflictData) {
        if (!this.elements.dialogueContent || !conflictData.dialogue) return;

        const dialogueHTML = conflictData.dialogue.map(message => {
            const messageClass = message.type === 'parent' ? 'parent' : 'child';
            return `
                <div class="dialogue-message ${messageClass}">
                    <div class="message-bubble ${messageClass}">
                        <div class="message-header">
                            <div class="message-role">${message.role}（${message.emotion}）</div>
                            <p class="message-content">${message.content}</p>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        this.elements.dialogueContent.innerHTML = dialogueHTML;
    },

    // 更新情绪仪表盘
    updateEmotionGauge(emotionLevel) {
        if (this.elements.emotionValue) {
            this.elements.emotionValue.textContent = emotionLevel.toFixed(2);
        }
        
        // 更新仪表盘位置
        const gaugeHandle = document.querySelector('.gauge-handle');
        if (gaugeHandle) {
            const maxOffset = 250; // 最大偏移量
            const offset = emotionLevel * maxOffset;
            gaugeHandle.style.left = `${7 + offset}px`;
        }
        
        // 更新点的位置
        const gaugeDot = document.querySelector('.gauge-dot');
        if (gaugeDot) {
            const maxOffset = 250;
            const offset = emotionLevel * maxOffset;
            gaugeDot.style.right = `${43 + (maxOffset - offset)}px`;
        }
    },

    // 绑定事件
    bindEvents() {
        // 冲突标签点击事件
        this.elements.conflictTabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const conflictId = parseInt(tab.dataset.conflict);
                this.switchConflict(conflictId);
            });
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
                localStorage.removeItem('conflictContext');
                localStorage.removeItem('selectedConflictId');
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

    // 切换对话详情显示
    toggleDialogue() {
        const dialogueContent = document.getElementById('dialogueContent');
        const expandButton = document.querySelector('.dialogue-expand');
        
        if (dialogueContent && expandButton) {
            const isExpanded = dialogueContent.classList.contains('expanded');
            
            if (isExpanded) {
                dialogueContent.classList.remove('expanded');
                dialogueContent.classList.add('collapsed');
                expandButton.style.transform = 'rotate(0deg)';
            } else {
                dialogueContent.classList.remove('collapsed');
                dialogueContent.classList.add('expanded');
                expandButton.style.transform = 'rotate(180deg)';
            }
        }
    },

    // 初始化动画
    initAnimations() {
        // 为分析卡片添加进入动画
        this.elements.analysisCards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(30px)';
            
            setTimeout(() => {
                card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 200);
        });

        // 为对话区域添加动画
        const dialogueSection = document.querySelector('.dialogue-section');
        if (dialogueSection) {
            dialogueSection.style.opacity = '0';
            dialogueSection.style.transform = 'translateY(30px)';
            
            setTimeout(() => {
                dialogueSection.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                dialogueSection.style.opacity = '1';
                dialogueSection.style.transform = 'translateY(0)';
            }, this.elements.analysisCards.length * 200);
        }
    },

    // 卡片更新动画
    animateCardUpdate() {
        this.elements.analysisCards.forEach(card => {
            card.classList.add('loading');
            
            setTimeout(() => {
                card.classList.remove('loading');
            }, 1000);
        });
    },

    // 刷新数据
    async refreshData() {
        console.log('刷新冲突分析数据...');
        await this.loadConflictData();
    },

    // 导出分析
    exportAnalysis() {
        if (!this.currentData) {
            this.showNotification('没有可导出的分析数据', 'error');
            return;
        }
        
        const currentConflict = this.currentData.conflicts[this.currentConflictId];
        if (!currentConflict) {
            this.showNotification('当前冲突数据不存在', 'error');
            return;
        }
        
        const exportData = {
            eventName: this.currentData.eventName,
            conflictId: this.currentConflictId,
            conflictData: currentConflict,
            exportTime: new Date().toISOString(),
            pageType: 'conflict-analysis',
            version: '1.0'
        };
        
        const blob = new Blob([JSON.stringify(exportData, null, 2)], {
            type: 'application/json'
        });
        
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `冲突分析_${currentConflict.title}_${new Date().toISOString().split('T')[0]}.json`;
        link.click();
        
        URL.revokeObjectURL(url);
        
        this.showNotification('分析数据导出成功！', 'success');
    },

    // 生成建议
    generateSuggestions() {
        if (!this.currentData) {
            this.showNotification('没有可分析的数据', 'error');
            return;
        }
        
        const currentConflict = this.currentData.conflicts[this.currentConflictId];
        if (!currentConflict) {
            this.showNotification('当前冲突数据不存在', 'error');
            return;
        }
        
        // 基于分析生成建议
        const suggestions = this.generateSuggestionsFromAnalysis(currentConflict);
        
        // 显示建议弹窗
        this.showSuggestionsModal(suggestions);
    },

    // 基于分析生成建议
    generateSuggestionsFromAnalysis(conflictData) {
        const suggestions = {
            communication: [],
            emotion: [],
            strategy: []
        };
        
        // 根据情绪水平生成建议
        if (conflictData.emotionLevel > 0.6) {
            suggestions.emotion.push('情绪波动较大，建议先让双方冷静一下再进行沟通');
            suggestions.communication.push('使用更温和的语调，避免直接指责');
        } else if (conflictData.emotionLevel > 0.4) {
            suggestions.emotion.push('情绪有一定波动，可以通过深呼吸来调节');
            suggestions.communication.push('保持耐心，给孩子更多表达的机会');
        } else {
            suggestions.emotion.push('情绪控制良好，继续保持这种沟通方式');
            suggestions.communication.push('当前沟通方式效果不错，可以继续使用');
        }
        
        // 根据对话内容生成建议
        const parentMessages = conflictData.dialogue.filter(msg => msg.type === 'parent');
        const childMessages = conflictData.dialogue.filter(msg => msg.type === 'child');
        
        if (parentMessages.some(msg => msg.emotion.includes('指责'))) {
            suggestions.strategy.push('尝试用"我"语句表达感受，而不是"你"语句进行指责');
        }
        
        if (childMessages.some(msg => msg.emotion.includes('默认'))) {
            suggestions.strategy.push('注意孩子是否真正理解，避免表面妥协');
        }
        
        // 通用建议
        suggestions.communication.push('倾听孩子的想法和感受');
        suggestions.strategy.push('制定明确的规则和期望');
        suggestions.emotion.push('保持积极正面的态度');
        
        return suggestions;
    },

    // 显示建议弹窗
    showSuggestionsModal(suggestions) {
        const modal = document.createElement('div');
        modal.className = 'suggestions-modal';
        modal.innerHTML = `
            <div class="modal-overlay" onclick="this.parentElement.remove()"></div>
            <div class="modal-content">
                <div class="modal-header">
                    <h3>个性化建议</h3>
                    <button class="modal-close" onclick="this.closest('.suggestions-modal').remove()">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                        </svg>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="suggestion-section">
                        <h4>沟通建议</h4>
                        <ul>
                            ${suggestions.communication.map(item => `<li>${item}</li>`).join('')}
                        </ul>
                    </div>
                    <div class="suggestion-section">
                        <h4>情绪管理</h4>
                        <ul>
                            ${suggestions.emotion.map(item => `<li>${item}</li>`).join('')}
                        </ul>
                    </div>
                    <div class="suggestion-section">
                        <h4>策略建议</h4>
                        <ul>
                            ${suggestions.strategy.map(item => `<li>${item}</li>`).join('')}
                        </ul>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="action-button secondary" onclick="this.closest('.suggestions-modal').remove()">
                        关闭
                    </button>
                    <button class="action-button primary" onclick="ConflictAnalysis.saveSuggestions(${JSON.stringify(suggestions).replace(/"/g, '&quot;')})">
                        保存建议
                    </button>
                </div>
            </div>
        `;
        
        // 添加样式
        const style = document.createElement('style');
        style.textContent = `
            .suggestions-modal {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                z-index: 9999;
                display: flex;
                align-items: center;
                justify-content: center;
                animation: fadeIn 0.3s ease;
            }
            
            .modal-overlay {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.5);
            }
            
            .modal-content {
                background: white;
                border-radius: 12px;
                padding: 0;
                max-width: 90%;
                max-height: 80%;
                overflow-y: auto;
                position: relative;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
                animation: slideUp 0.3s ease;
            }
            
            .modal-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 20px 24px;
                border-bottom: 1px solid #E5E5E5;
            }
            
            .modal-header h3 {
                margin: 0;
                color: var(--primary-color);
                font-size: 18px;
                font-weight: 600;
            }
            
            .modal-close {
                background: none;
                border: none;
                color: #666;
                cursor: pointer;
                padding: 4px;
                border-radius: 4px;
                transition: background 0.2s;
            }
            
            .modal-close:hover {
                background: #F5F5F5;
            }
            
            .modal-close svg {
                width: 20px;
                height: 20px;
            }
            
            .modal-body {
                padding: 24px;
            }
            
            .suggestion-section {
                margin-bottom: 24px;
            }
            
            .suggestion-section:last-child {
                margin-bottom: 0;
            }
            
            .suggestion-section h4 {
                margin: 0 0 12px 0;
                color: var(--primary-color);
                font-size: 16px;
                font-weight: 600;
            }
            
            .suggestion-section ul {
                margin: 0;
                padding: 0;
                list-style: none;
            }
            
            .suggestion-section li {
                padding: 8px 0;
                border-bottom: 1px solid #F5F5F5;
                color: var(--text-color);
                line-height: 1.5;
            }
            
            .suggestion-section li:last-child {
                border-bottom: none;
            }
            
            .suggestion-section li::before {
                content: "•";
                color: var(--primary-color);
                font-weight: bold;
                margin-right: 8px;
            }
            
            .modal-footer {
                display: flex;
                gap: 12px;
                padding: 20px 24px;
                border-top: 1px solid #E5E5E5;
                background: #F9F9F9;
                border-radius: 0 0 12px 12px;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            
            @keyframes slideUp {
                from { transform: translateY(30px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
        `;
        
        document.head.appendChild(style);
        document.body.appendChild(modal);
        
        // 阻止背景滚动
        document.body.style.overflow = 'hidden';
        
        // 清理函数
        const cleanup = () => {
            document.body.style.overflow = '';
            document.head.removeChild(style);
        };
        
        modal.addEventListener('remove', cleanup);
    },

    // 保存建议
    saveSuggestions(suggestions) {
        const savedSuggestions = {
            conflictId: this.currentConflictId,
            suggestions: suggestions,
            timestamp: new Date().toISOString()
        };
        
        localStorage.setItem('conflictSuggestions', JSON.stringify(savedSuggestions));
        this.showNotification('建议已保存！', 'success');
        
        // 关闭弹窗
        const modal = document.querySelector('.suggestions-modal');
        if (modal) {
            modal.remove();
        }
    },

    // 显示通知
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? 'var(--primary-color)' : type === 'error' ? '#f44336' : '#2196F3'};
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            z-index: 9999;
            opacity: 0;
            transform: translateY(-20px);
            transition: opacity 0.3s ease, transform 0.3s ease;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateY(0)';
        }, 100);
        
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateY(-20px)';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
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
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    ConflictAnalysis.init();
});

// 导出为全局对象
window.ConflictAnalysis = ConflictAnalysis; 