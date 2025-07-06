Figma -> 前端稿 
由Figma生成前端代码，确保页面跳转逻辑正确，同时很多地方需要js逻辑参与，调用后端数据库填入对应数据，可留空

页面1：注册页面，注册成功跳到登录页面 https://www.figma.com/design/JfUBxPzyQkNYvIDFOxv8qp/Template--Only-?node-id=54718-2064&t=LeencTXGHbWWwcxa-4

页面2：登录页面，登录成功弹窗，随后跳转到主页面
https://www.figma.com/design/JfUBxPzyQkNYvIDFOxv8qp/Template--Only-?node-id=54718-2117&t=LeencTXGHbWWwcxa-4
页面3：错误页面，暂不支持页面
https://www.figma.com/design/JfUBxPzyQkNYvIDFOxv8qp/Template--Only-?node-id=54718-2252&t=LeencTXGHbWWwcxa-4
页面4：主页面，主页面上方是问候语，下方是主页面点击开始录音跳转到录音页面，点击上传文件跳转到文件上传页面，主页面的历史录音报告会展示最近的两份报告(js逻辑填入后续),下方查看全部报告可跳转历史报告页面
https://www.figma.com/design/JfUBxPzyQkNYvIDFOxv8qp/Template--Only-?node-id=54788-247&t=LeencTXGHbWWwcxa-4
页面5：录音页面：录音页面下方的icon和上方的icon动态改变代表录音是否开始，录音结束后选择取消或者上传，上传后出现弹窗，包括儿童姓名和日期选择器，成功后跳转历史录音报告页面
https://www.figma.com/design/JfUBxPzyQkNYvIDFOxv8qp/Template--Only-?node-id=54742-132&t=LeencTXGHbWWwcxa-4
https://www.figma.com/design/JfUBxPzyQkNYvIDFOxv8qp/Template--Only-?node-id=54742-176&t=LeencTXGHbWWwcxa-4
https://www.figma.com/design/JfUBxPzyQkNYvIDFOxv8qp/Template--Only-?node-id=54742-206&t=LeencTXGHbWWwcxa-4
页面6：文件上传页面，选择文件上传本地录音，上传后同样出现弹窗，跳转历史录音报告页面
https://www.figma.com/design/JfUBxPzyQkNYvIDFOxv8qp/Template--Only-?node-id=54752-168&t=LeencTXGHbWWwcxa-4
页面7：历史录音报告页面(js逻辑呈现用户历史报告，包含听录音和看报告两个选项，同时右滑删除报告)
https://www.figma.com/design/JfUBxPzyQkNYvIDFOxv8qp/Template--Only-?node-id=54790-1277&t=LeencTXGHbWWwcxa-4
页面8：报告主页面，需从数据库/后端获取的数据
https://www.figma.com/design/JfUBxPzyQkNYvIDFOxv8qp/Template--Only-?node-id=54714-1033&t=LeencTXGHbWWwcxa-4
页面8-1：报告子页面，点击家庭教育全家跳转子模块
https://www.figma.com/design/JfUBxPzyQkNYvIDFOxv8qp/Template--Only-?node-id=54730-390&t=LeencTXGHbWWwcxa-4
页面8-2：冲突场景剖析，点击冲突场景图跳转子模块
https://www.figma.com/design/JfUBxPzyQkNYvIDFOxv8qp/Template--Only-?node-id=54730-576&t=LeencTXGHbWWwcxa-4

报告页面涉及到的数据：
1.录音时长 2.冲突场景数量 3.优势（精炼+全部） 4.劣势
5.家庭教育全景三方面 精炼+全部
6.每种冲突(横轴时间+纵轴情绪) +冲突具体发生的什么东西
7.每次冲突的核心+冲突回顾 对话详情
8.情绪冲突
9.积极行为（新增的
10.消极行为（新增的
11.问题及策略
