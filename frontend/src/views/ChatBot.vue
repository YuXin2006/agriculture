<script setup>
import { nextTick, ref } from "vue";
import { sendChatMessage } from "../api/dashboard";

const inputText = ref("");
const sending = ref(false);
const messagesEndRef = ref(null);
const sessionId = ref("");

const quickPrompts = [
  "当前基地温湿度是否正常？",
  "土壤湿度偏低该怎么处理？",
  "最近有哪些告警需要关注？",
  "帮我分析一下设备在线情况",
];

const messages = ref([
  {
    id: 1,
    role: "assistant",
    content:
      "你好，我是智慧农业助手。你可以向我咨询作物监测、环境数据、设备状态、告警分析等问题，我会结合系统数据为你解答。",
    time: formatTime(new Date()),
  },
]);

function formatTime(date) {
  const h = String(date.getHours()).padStart(2, "0");
  const m = String(date.getMinutes()).padStart(2, "0");
  return `${h}:${m}`;
}

async function scrollToBottom() {
  await nextTick();
  messagesEndRef.value?.scrollIntoView({ behavior: "smooth" });
}

function mockReply(question) {
  const replies = [
    "根据当前监测数据，基地整体环境处于正常范围。如需查看具体传感器数值，建议前往「数据总览」页面。",
    "土壤湿度偏低时，建议检查灌溉系统是否正常运行，并适当调整浇水频率。若持续偏低，可排查传感器是否故障。",
    "你可以在「告警记录」页面查看完整告警列表。近期需重点关注温湿度异常和设备离线类告警。",
    "目前 Mesh 网络运行稳定，大部分节点在线。若有离线设备，请检查节点供电与信号覆盖。",
  ];
  const index = Math.abs(question.length) % replies.length;
  return replies[index];
}

async function sendMessage(text) {
  const content = (text ?? inputText.value).trim();
  if (!content || sending.value) return;

  messages.value.push({
    id: Date.now(),
    role: "user",
    content,
    time: formatTime(new Date()),
  });
  inputText.value = "";
  sending.value = true;
  await scrollToBottom();

  try {
    const data = await sendChatMessage({
      message: content,
      session_id: sessionId.value || undefined,
    });
    if (data?.session_id) {
      sessionId.value = data.session_id;
    }
    messages.value.push({
      id: Date.now() + 1,
      role: "assistant",
      content: data?.reply ?? data?.content ?? data?.message ?? "暂无回复",
      time: formatTime(new Date()),
    });
  } catch {
    messages.value.push({
      id: Date.now() + 1,
      role: "assistant",
      content: mockReply(content),
      time: formatTime(new Date()),
    });
  } finally {
    sending.value = false;
    await scrollToBottom();
  }
}

function onKeydown(event) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
}
</script>

<template>
  <section class="chat-page dash-card">
    <div class="chat-header">
      <div class="chat-header__info">
        <span class="chat-avatar">AI</span>
        <div>
          <h2>智慧农业助手</h2>
          <p>基于 LangChain · 可咨询监测数据与农事建议</p>
        </div>
      </div>
      <span class="chat-status">
        <span class="status-dot" />
        在线
      </span>
    </div>

    <div class="chat-body">
      <div class="chat-messages">
        <div
          v-for="msg in messages"
          :key="msg.id"
          class="message-row"
          :class="msg.role === 'user' ? 'message-row--user' : 'message-row--assistant'"
        >
          <span v-if="msg.role === 'assistant'" class="msg-avatar">AI</span>
          <div class="message-bubble">
            <p>{{ msg.content }}</p>
            <time>{{ msg.time }}</time>
          </div>
          <span v-if="msg.role === 'user'" class="msg-avatar msg-avatar--user">我</span>
        </div>

        <div v-if="sending" class="message-row message-row--assistant">
          <span class="msg-avatar">AI</span>
          <div class="message-bubble message-bubble--typing">
            <span class="typing-dot" />
            <span class="typing-dot" />
            <span class="typing-dot" />
          </div>
        </div>

        <div ref="messagesEndRef" />
      </div>

      <aside class="chat-sidebar">
        <h3>快捷提问</h3>
        <button
          v-for="prompt in quickPrompts"
          :key="prompt"
          type="button"
          class="prompt-chip"
          :disabled="sending"
          @click="sendMessage(prompt)"
        >
          {{ prompt }}
        </button>
        <p class="sidebar-hint">后端接入 LangChain 后，将返回基于实时数据的智能回答。</p>
      </aside>
    </div>

    <footer class="chat-input-bar">
      <textarea
        v-model="inputText"
        rows="1"
        placeholder="输入你的问题，Enter 发送，Shift+Enter 换行"
        :disabled="sending"
        @keydown="onKeydown"
      />
      <button type="button" class="send-btn" :disabled="!inputText.trim() || sending" @click="sendMessage()">
        发送
      </button>
    </footer>
  </section>
</template>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 56px - 48px);
  max-height: calc(100vh - 56px - 48px);
  overflow: hidden;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.chat-header__info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-avatar {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #4da3ff, #7b5cff);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
}

.chat-header__info h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.chat-header__info p {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--text-secondary);
}

.chat-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--accent-green);
}

.chat-body {
  flex: 1;
  display: flex;
  min-height: 0;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.chat-sidebar {
  width: 220px;
  flex-shrink: 0;
  border-left: 1px solid var(--border);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chat-sidebar h3 {
  margin: 0 0 4px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}

.prompt-chip {
  text-align: left;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-primary);
  font-size: 12px;
  line-height: 1.45;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}

.prompt-chip:hover:not(:disabled) {
  background: rgba(77, 163, 255, 0.1);
  border-color: rgba(77, 163, 255, 0.35);
}

.prompt-chip:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.sidebar-hint {
  margin-top: auto;
  font-size: 11px;
  line-height: 1.5;
  color: var(--text-secondary);
}

.message-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  max-width: 85%;
}

.message-row--user {
  align-self: flex-end;
  flex-direction: row;
}

.message-row--assistant {
  align-self: flex-start;
}

.msg-avatar {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: linear-gradient(135deg, #4da3ff, #7b5cff);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
}

.msg-avatar--user {
  background: linear-gradient(135deg, #2ecc71, #1a9b52);
}

.message-bubble {
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
}

.message-row--user .message-bubble {
  background: rgba(46, 204, 113, 0.12);
  border-color: rgba(61, 220, 132, 0.25);
}

.message-bubble p {
  margin: 0;
  font-size: 14px;
  line-height: 1.55;
  white-space: pre-wrap;
  word-break: break-word;
}

.message-bubble time {
  display: block;
  margin-top: 6px;
  font-size: 11px;
  color: var(--text-secondary);
}

.message-bubble--typing {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 14px 18px;
}

.typing-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--text-secondary);
  animation: typing 1.2s infinite ease-in-out;
}

.typing-dot:nth-child(2) {
  animation-delay: 0.15s;
}

.typing-dot:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes typing {
  0%,
  80%,
  100% {
    opacity: 0.35;
    transform: translateY(0);
  }
  40% {
    opacity: 1;
    transform: translateY(-3px);
  }
}

.chat-input-bar {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  padding: 14px 20px;
  border-top: 1px solid var(--border);
  background: rgba(15, 23, 41, 0.4);
}

.chat-input-bar textarea {
  flex: 1;
  resize: none;
  min-height: 42px;
  max-height: 120px;
  padding: 10px 14px;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-primary);
  font-family: inherit;
  font-size: 14px;
  line-height: 1.5;
  outline: none;
  transition: border-color 0.15s;
}

.chat-input-bar textarea:focus {
  border-color: rgba(77, 163, 255, 0.5);
}

.chat-input-bar textarea::placeholder {
  color: var(--text-secondary);
}

.chat-input-bar textarea:disabled {
  opacity: 0.6;
}

.send-btn {
  padding: 10px 22px;
  border-radius: 10px;
  border: none;
  background: linear-gradient(135deg, #3ddc84, #2ecc71);
  color: #0b1220;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s;
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.send-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
</style>
