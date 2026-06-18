/**
 * tokenBudget.ts — 对话 Token 预算管理与自动压缩
 *
 * 策略：
 *   - estimateTokens(): 粗略估算文本 token 数（中文字符 ~1.5 token，英文 ~0.75 token）
 *   - COMPACT_THRESHOLD = 4000 tokens — 超过此阈值触发自动压缩
 *   - HARD_LIMIT = 6000 tokens — 超过此阈值强制截断
 *   - compactMessages(): 保留系统消息 + 最近 N 轮，其余用摘要替代
 */

const CHARS_PER_TOKEN_CN = 0.67;  // 中文字符 ≈ 1.5 token
const CHARS_PER_TOKEN_EN = 4.0;   // 英文字符 ≈ 0.25 token

export const COMPACT_THRESHOLD = 4000;
export const HARD_LIMIT = 6000;

export function estimateTokens(text: string): number {
  let cn = 0, en = 0;
  for (const ch of text) {
    if (/[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]/.test(ch)) {
      cn++;
    } else if (/[a-zA-Z0-9]/.test(ch)) {
      en++;
    }
  }
  return Math.ceil(cn / CHARS_PER_TOKEN_CN + en / CHARS_PER_TOKEN_EN);
}

export function estimateConversationTokens(messages: { content: string }[]): number {
  return messages.reduce((sum, m) => sum + estimateTokens(m.content || ""), 0);
}

/**
 * 压缩对话历史：保留首条系统消息 + 最近 keepTurns 轮，其余用 compactNote 替代。
 * 一轮 = 一条 user 消息 + 紧随的 assistant 消息
 */
export function compactMessages(
  messages: { role: string; content: string }[],
  keepTurns: number = 3
): { role: string; content: string }[] {
  if (messages.length <= keepTurns * 2 + 2) return messages;

  const result: { role: string; content: string }[] = [];
  let i = 0;

  // 保留第一条（系统消息或首条用户消息）
  if (messages.length > 0) {
    result.push(messages[0]);
    i = 1;
  }

  // 跳过中间轮次，插入摘要
  const skipped = messages.slice(i, -keepTurns * 2);
  if (skipped.length > 0) {
    const summaryParts: string[] = [];
    for (const m of skipped) {
      const preview = (m.content || "").slice(0, 80).replace(/\n/g, " ");
      if (preview.trim()) summaryParts.push(`[${m.role}]: ${preview}`);
    }
    result.push({
      role: "system",
      content: `[对话历史摘要 — ${skipped.length} 条消息已压缩]\n${summaryParts.slice(0, 5).join(" | ")}`,
    });
  }

  // 保留最后 keepTurns 轮
  const lastMessages = messages.slice(-keepTurns * 2);
  result.push(...lastMessages);

  return result;
}

/**
 * 工具结果截断（Claude Code 的 toolResultBudget 等价）
 */
export function truncateToolResult(text: string, maxChars: number = 2000): string {
  if (text.length <= maxChars) return text;
  return text.slice(0, maxChars) + `\n\n... [截断，原 ${text.length} 字符]`;
}
