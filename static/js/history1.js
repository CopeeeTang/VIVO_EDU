document.addEventListener('DOMContentLoaded', function() {
    // 页面加载时自动获取历史数据
    fetchHistoryData();
    fetchStatsData();
    initTabButtons();
    initFullscreenViewer(); // 初始化全屏查看器
    
    function fetchHistoryData() {
        const token = localStorage.getItem('jwtToken');
        if (!token) {
            window.location.href = '/login';
            return;
        }
        
        axios.get('/api/audio/history', {
            headers: { 'Authorization': `Bearer ${token}` }
        })
        .then(response => {
            if (response.data.code === 200) {
                if (response.data.data && response.data.data.length > 0) {
                    renderImages(response.data.data);
                    initPortraitButton(response.data.data);
                } else {
                    displayNoDataMessage();
                }
            }
        })
        .catch(handleFetchError);
    }
    // 获取统计数据
    function fetchStatsData() {
        const token = localStorage.getItem('jwtToken');
        axios.get('/api/audio/stats', {
            headers: { 'Authorization': `Bearer ${token}` }
        })
        .then(response => {
            if (response.data.code === 200) {
                renderStats(response.data.data);
            }
        })
        .catch(error => {
            console.error('获取统计数据失败:', error);
        });
    }

function renderImages(data) {
    const conflictContainer = document.getElementById('image-strip');
    const behaviorContainer = document.getElementById('behavior-strip');
    const fullscreenOverlay = document.getElementById('fullscreen-overlay');
    const fullscreenImage = document.getElementById('fullscreen-image');

    if (!conflictContainer || !behaviorContainer || !fullscreenOverlay || !fullscreenImage) {
        console.error("Required elements for image rendering or fullscreen view are missing.");
        return;
    }
    
    conflictContainer.innerHTML = '';
    behaviorContainer.innerHTML = '';
    
    if (data.length === 0) {
        displayNoDataMessage();
        return;
    }
    
    const latestData = data[0]; 
    
    const addImage = (container, src, alt, category) => {
        if (!src) return;
        
        const imgWrapper = document.createElement('div');
        imgWrapper.className = 'image-item';
        
        const img = document.createElement('img');
        img.className = 'analysis-image';
        img.src = src;
        img.alt = alt;
        img.loading = 'lazy'; 
        
        img.onerror = () => {
            // 修复占位图逻辑，使用更清晰的默认图
            let defaultSrc = '../static/images/severity.png'; // 默认占位图
            if (category.includes('冲突')) {
                defaultSrc = '../static/images/conflict_dist.png';
            } else if (category.includes('行为')) {
                defaultSrc = '../static/images/trend.png';
            }
            img.src = defaultSrc;
            img.alt = '图片加载失败';
            imgWrapper.style.cursor = 'default'; // 无法放大的图片禁用手型光标
        };
        
        const label = document.createElement('div');
        label.className = 'image-label';
        label.textContent = category;
        
        imgWrapper.appendChild(img);
        imgWrapper.appendChild(label);
        container.appendChild(imgWrapper);
        
        // 为图片添加点击事件，用于全屏显示
        img.addEventListener('click', function() {
            // 只有图片成功加载才允许放大
            if (this.naturalWidth > 0 && this.src !== img.onerror) { // 确保图片已加载且不是错误占位符
                fullscreenImage.src = this.src;
                fullscreenOverlay.style.display = 'flex';
            } else {
                console.log("Cannot enlarge image: not loaded or is a placeholder.");
            }
        });

        imgWrapper.style.cursor = 'pointer'; // 为可点击的图片添加手型光标
        
        img.onload = () => {
            container.parentElement.scrollLeft = 0;
        };
    };
    
    let conflictImagesCount = 0;
    let behaviorImagesCount = 0;
    
    // 加载冲突分析图表
    if (latestData.conflict_distribution) {
        addImage(conflictContainer, latestData.conflict_distribution, '冲突类型分布图', '冲突类型分布');
        conflictImagesCount++;
    }
    if (latestData.conflict_trend) {
        addImage(conflictContainer, latestData.conflict_trend, '冲突趋势图', '冲突趋势');
        conflictImagesCount++;
    }
    if (latestData.conflict_type_trend) {
        addImage(conflictContainer, latestData.conflict_type_trend, '冲突类型趋势图', '冲突类型趋势');
        conflictImagesCount++;
    }
    if (latestData.severity_distribution) {
        addImage(conflictContainer, latestData.severity_distribution, '冲突严重度分布图', '严重程度分布');
        conflictImagesCount++;
    }
    
    // 添加行为分析图表
    if (latestData.behavior_distribution) {
        addImage(behaviorContainer, latestData.behavior_distribution, '行为类型分布图', '行为类型分布');
        behaviorImagesCount++;
    }
    if (latestData.behavior_trend) {
        addImage(behaviorContainer, latestData.behavior_trend, '行为趋势图', '行为趋势');
        behaviorImagesCount++;
    }
    // 注意：这里的类别名称可能需要根据实际情况调整
    if (latestData.behavior_type_distribution) { // 假设这个是行为类型分布
        addImage(behaviorContainer, latestData.behavior_type_distribution, '行为类型分布图', '行为类型分布');
        behaviorImagesCount++;
    }
    if (latestData.behavior_percentage_trend) {
        addImage(behaviorContainer, latestData.behavior_percentage_trend, '行为类型百分比趋势图', '行为类型比例');
        behaviorImagesCount++;
    }
    
    if (conflictImagesCount === 0) {
        conflictContainer.innerHTML = '<div class="no-data-message">暂无冲突分析数据</div>';
    }
    if (behaviorImagesCount === 0) {
        behaviorContainer.innerHTML = '<div class="no-data-message">暂无行为分析数据</div>';
    }
}

    function initTabButtons() {
        const tabButtons = document.querySelectorAll('.tab-button');
        if (tabButtons.length === 0) return;
        
        tabButtons.forEach(button => {
            button.addEventListener('click', function() {
                // 移除所有按钮的active类
                tabButtons.forEach(btn => btn.classList.remove('active'));
                // 添加当前按钮的active类
                this.classList.add('active');
                
                // 隐藏所有内容面板
                const tabPanes = document.querySelectorAll('.tab-pane');
                tabPanes.forEach(pane => pane.classList.remove('active'));
                
                // 显示对应的内容面板
                const targetId = this.getAttribute('data-target');
                document.getElementById(targetId).classList.add('active');
            });
        });
    }

    function initPortraitButton(data) {
        const portraitBtn = document.getElementById('portrait-btn');
        if (!portraitBtn) return;
        
        if (data.length > 0) {
            // 按时间排序获取最新记录
            const sortedData = data.sort((a, b) => b.timestamp - a.timestamp);
            const latestFile = sortedData[0];
            
            // 为亲子画像按钮添加点击事件
            portraitBtn.style.cursor = 'pointer';
            portraitBtn.onclick = () => generateReport(latestFile.file_id);
        } else {
            portraitBtn.style.cursor = 'not-allowed';
            portraitBtn.onclick = () => alert('暂无可用报告');
        }
    }

    async function generateReport(fileId) {
        try {
            const token = localStorage.getItem('jwtToken');
            const response = await axios.get(`/api/audio/history2/${fileId}`, {
                headers: { 
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            // 如果是重定向响应，直接跳转到新URL
            if (response.request.responseURL) {
                window.location.href = response.request.responseURL;
            }
            
        } catch (error) {
            handleReportError(error);
        }
    }

    function handleFetchError(error) {
        if (error.response?.status === 401) {
            window.location.href = '/login';
        } else {
            console.error('获取数据失败:', error);
        }
    }

    function handleReportError(error) {
        if (error.response) {
            alert(`生成报告失败: ${error.response.data.msg}`);
        } else {
            alert('网络连接异常，请检查后重试');
        }
    }
    
    // 渲染统计数据
    function renderStats(data) {
        const conflictCountElem = document.getElementById('conflict-count');
        const conflictChangeElem = document.getElementById('conflict-change');
        const behaviorCountElem = document.getElementById('behavior-count');
        const behaviorChangeElem = document.getElementById('behavior-change');

        if (conflictCountElem && conflictChangeElem && behaviorCountElem && behaviorChangeElem) {
            conflictCountElem.innerText = data.conflict_count || 0;
            
            // 处理变化显示，使其更友好
            if (data.conflict_change === 'N/A') {
                conflictChangeElem.innerText = '首次分析';
                conflictChangeElem.style.color = '#888';
            } else {
                const changeValue = parseFloat(data.conflict_change);
                if (!isNaN(changeValue)) {
                    if (changeValue > 0) {
                        conflictChangeElem.innerText = `↑ ${data.conflict_change}`;
                        conflictChangeElem.style.color = '#f55';
                    } else if (changeValue < 0) {
                        conflictChangeElem.innerText = `↓ ${data.conflict_change.replace('-', '')}`;
                        conflictChangeElem.style.color = '#5a5';
                    } else {
                        conflictChangeElem.innerText = `${data.conflict_change}`;
                        conflictChangeElem.style.color = '#888';
                    }
                } else {
                    conflictChangeElem.innerText = data.conflict_change;
                }
            }
            
            behaviorCountElem.innerText = data.behavior_count || 0;
            
            // 行为变化处理同上
            if (data.behavior_change === 'N/A') {
                behaviorChangeElem.innerText = '首次分析';
                behaviorChangeElem.style.color = '#888';
            } else {
                const changeValue = parseFloat(data.behavior_change);
                if (!isNaN(changeValue)) {
                    if (changeValue > 0) {
                        behaviorChangeElem.innerText = `↑ ${data.behavior_change}`;
                        behaviorChangeElem.style.color = '#f55';
                    } else if (changeValue < 0) {
                        behaviorChangeElem.innerText = `↓ ${data.behavior_change.replace('-', '')}`;
                        behaviorChangeElem.style.color = '#5a5';
                    } else {
                        behaviorChangeElem.innerText = `${data.behavior_change}`;
                        behaviorChangeElem.style.color = '#888';
                    }
                } else {
                    behaviorChangeElem.innerText = data.behavior_change;
                }
            }
        }
    }

    function displayNoDataMessage() {
        const conflictContainer = document.getElementById('image-strip');
        const behaviorContainer = document.getElementById('behavior-strip');
        
        if (conflictContainer) {
            conflictContainer.innerHTML = '<div class="no-data-message">暂无冲突分析数据，请先上传录音文件进行分析</div>';
        }
        
        if (behaviorContainer) {
            behaviorContainer.innerHTML = '<div class="no-data-message">暂无行为分析数据，请先上传录音文件进行分析</div>';
        }
        
        const portraitBtn = document.getElementById('portrait-btn');
        if (portraitBtn) {
            portraitBtn.style.cursor = 'not-allowed';
            portraitBtn.classList.add('disabled');
        }
    }

    // 新增：初始化全屏查看器的关闭功能
    function initFullscreenViewer() {
        const fullscreenOverlay = document.getElementById('fullscreen-overlay');
        const closeButton = document.getElementById('close-fullscreen');

        if (!fullscreenOverlay || !closeButton) {
            console.error("Fullscreen viewer elements not found.");
            return;
        }

        // 点击关闭按钮或覆盖层背景时关闭全屏视图
        closeButton.addEventListener('click', closeFullscreen);
        fullscreenOverlay.addEventListener('click', function(event) {
            // 确保点击的是覆盖层本身，而不是图片
            if (event.target === fullscreenOverlay) {
                closeFullscreen();
            }
        });
    }

    // 新增：关闭全屏视图的函数
    function closeFullscreen() {
        const fullscreenOverlay = document.getElementById('fullscreen-overlay');
        if (fullscreenOverlay) {
            fullscreenOverlay.style.display = 'none';
            // 清除图片src，避免旧图片闪烁
            const fullscreenImage = document.getElementById('fullscreen-image');
            if(fullscreenImage) fullscreenImage.src = ""; 
        }
    }
});
