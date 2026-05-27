chatbot 功能核心文件

dashboard/services/chat_agent.py — LangChain + ChatOpenAI，多轮对话写入数据库
dashboard/services/chat_context.py — 注入设备、环境、土壤、告警等实时数据 汇总当前监测数据，供 LangChain 系统提示词使用。
dashboard/models.py — ChatSession、ChatMessage 持久化会话
dashboard/views/chat.py — 三个 API 视图