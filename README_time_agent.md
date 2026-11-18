# 时间感知 Agent 最小可运行版

## 环境
Python 3.10+，只使用标准库。Windows PowerShell、macOS、Linux 均可运行。
解压后在同一目录执行命令，默认数据库为当前目录的 time_agent.db。
不同终端必须使用同一个数据库路径；也可以在子命令前指定 --db 绝对路径。
本示例是单用户原型，请勿让多个 chat 进程同时处理同一用户。

## 架构
用户 -> CLI -> 时间上下文 + SQLite 最近12条消息 -> LLM
LLM -> get_time 工具 -> 系统时钟 + SQLite -> LLM 回答
CLI add -> SQLite jobs -> worker每秒检查 -> notifications持久记录 + 终端输出

## 1. 无 API 验证
python time_agent.py now
python time_agent.py chat "你好" --offline
等待几秒，关闭终端后重新打开，在同一目录执行：
python time_agent.py chat "距离上次多久" --offline
检查 seconds_since_last_user。offline只输出真实上下文，不是大模型。

## 2. 到期触发
终端A：
python time_agent.py worker
终端B，同一目录：
python time_agent.py add --seconds 10 --text "检查任务是否完成"
python time_agent.py jobs
十秒后终端A输出通知。持久记录：
python time_agent.py notifications
提醒只是通知文本，不会实际检查其他程序的任务状态。
可以先停止worker，创建10秒提醒，等15秒再启动worker，验证补发和late_seconds。

## 3. 接入模型（Windows PowerShell）
$env:OPENAI_API_KEY="你的API密钥"
$env:OPENAI_MODEL="你账户可用且支持Responses函数调用的模型ID"
python time_agent.py chat "现在几点？距离我上次找你多久？请调用get_time确认。"

macOS/Linux：
export OPENAI_API_KEY="你的API密钥"
export OPENAI_MODEL="你账户可用且支持Responses函数调用的模型ID"
python time_agent.py chat "现在几点？距离我上次找你多久？请调用get_time确认。"

模型通过OpenAI Responses API调用，最多4轮工具交互，单次请求超时45秒。
没有配置密钥时不会自动伪装成AI回答，必须显式使用--offline。
网络、账户权限、额度和模型可用性需在你的环境验证，本包未执行真实API调用。
API模式会发送本轮输入、时间上下文、最近12条本地消息；请勿输入公司机密。
store=False不是对供应商所有日志或保留政策的承诺。

## 4. 测试
python -m unittest -v test_time_agent
4项测试：首次交互、跨会话恢复、重启补发与去重、无效延迟。
测试通过mock时钟完成，不代表真实等待，也不测试远程API。

## 边界和后续扩展
- 时区固定为上海UTC+08:00，针对当前现实时间，不处理历史夏令时。
- 依赖操作系统时钟准确；程序没有独立NTP同步。
- monotonic用于进程内轮询耗时；持久截止时间使用Unix时间。系统调时会影响截止判断。
- worker是确定性调度器，到期不调用LLM。需要AI推理时，可扩展持久事件队列，由独立AI worker消费。
- get_time是模型可调用的真实工具；add目前只能由CLI调用，模型不能创建提醒。
- 每次chat启动加载最近12条消息，非完整长期语义记忆系统。
- 后台程序停止或电脑休眠时不能即时提醒，恢复后补发。关闭终端通常也会停止worker。
- notifications表与jobs完成状态在同一事务提交，防止数据库内重复生成通知。
- 终端输出不是可靠外部投递：提交后崩溃可能未打印，但可用notifications查询。
- 若扩展邮件/Teams投递，需outbox、重试、投递状态和幂等键，不承诺exactly-once。
- 当前只有本地终端通知，无邮件、Teams、任意命令执行或后台安装。
- 运行时会生成SQLite数据库，保存明文聊天；不应提交到Git或共享给他人。
- 本原型不提供服务管理、身份认证、多用户隔离、加密、自动API重试或生产监控。

## 参考
OpenAI Responses API：https://platform.openai.com/docs/api-reference/responses/create
