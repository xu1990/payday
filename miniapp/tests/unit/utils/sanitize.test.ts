/**
 * sanitize 工具函数测试
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import {
  escapeHtml,
  sanitizeContent,
  sanitizeNickname,
  isValidImageUrl,
  sanitizeComment,
  sanitizePost,
  removeControlChars,
} from '@/utils/sanitize'

describe('escapeHtml', () => {
  // Mock document.createElement for escapeHtml tests
  // happy-dom doesn't properly simulate browser textContent behavior
  const mockDocument = {
    createElement: vi.fn(() => ({
      textContent: '',
      get innerHTML() {
        // Simulate browser behavior: escape HTML entities when reading innerHTML
        return this.textContent
          .replace(/&/g, '&amp;')
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;')
          .replace(/"/g, '&quot;')
          .replace(/'/g, '&#39;')
      },
      set textContent(value: string) {
        this._textContent = value
      },
      get textContent() {
        return this._textContent
      },
    })),
  }

  beforeEach(() => {
    // Setup mock
    vi.stubGlobal('document', mockDocument)
  })

  it('应该移除 HTML 标签', () => {
    const result1 = escapeHtml('<div>Hello</div>')
    // 验证标签被转义
    expect(result1).not.toContain('<div>')
    expect(result1).toContain('Hello')
  })

  it('应该移除 script 标签', () => {
    const result2 = escapeHtml('<script>alert("xss")</script>')
    expect(result2).not.toContain('<script>')
  })

  it('应该保留纯文本', () => {
    expect(escapeHtml('Hello World')).toBe('Hello World')
    expect(escapeHtml('123')).toBe('123')
  })

  it('应该处理空字符串', () => {
    expect(escapeHtml('')).toBe('')
  })

  it('应该处理包含 & 的文本', () => {
    const result = escapeHtml('Tom & Jerry')
    expect(result).toContain('Tom')
    expect(result).toContain('Jerry')
  })

  it('应该处理引号', () => {
    const result1 = escapeHtml('"test"')
    expect(result1).toContain('test')

    const result2 = escapeHtml("'test'")
    expect(result2).toContain('test')
  })
})

describe('sanitizeContent', () => {
  it('应该移除 script 标签', () => {
    const result = sanitizeContent('Hello <script>alert("xss")</script> World')
    expect(result).not.toContain('<script>')
    expect(result).not.toContain('</script>')
  })

  it('应该移除危险的协议', () => {
    expect(sanitizeContent('javascript:alert(1)')).not.toContain('javascript:')
    expect(sanitizeContent('data:text/html,<script>')).not.toContain('data:')
  })

  it('应该移除事件处理器', () => {
    const result = sanitizeContent('<div onclick="alert(1)">Click</div>')
    expect(result).not.toContain('onclick=')
  })

  it('应该截断超长内容', () => {
    const longText = 'a'.repeat(15000)
    const result = sanitizeContent(longText, { maxLength: 100 })
    expect(result.length).toBeLessThanOrEqual(100)
  })

  it('应该使用默认最大长度', () => {
    const longText = 'b'.repeat(15000)
    const result = sanitizeContent(longText)
    expect(result.length).toBe(10000)
  })

  it('应该保留换行符当允许时', () => {
    const result = sanitizeContent('Line 1\nLine 2\nLine 3', { allowLineBreaks: true })
    expect(result).toContain('\n')
  })

  it('应该移除换行符当不允许时', () => {
    const result = sanitizeContent('Line 1\nLine 2\nLine 3', { allowLineBreaks: false })
    expect(result).not.toContain('\n')
    expect(result).not.toContain('\r')
  })

  it('应该处理空字符串', () => {
    expect(sanitizeContent('')).toBe('')
  })
})

describe('sanitizeNickname', () => {
  it('应该截断超长昵称', () => {
    const longNickname = 'a'.repeat(100)
    const result = sanitizeNickname(longNickname)
    expect(result.length).toBeLessThanOrEqual(50)
  })

  it('应该移除 HTML 标签', () => {
    expect(sanitizeNickname('<b>Name</b>')).not.toContain('<b>')
    expect(sanitizeNickname('Name')).toBe('Name')
  })

  it('应该转义特殊字符', () => {
    expect(sanitizeNickname('<script>')).not.toContain('<script>')
  })

  it('应该处理空字符串', () => {
    expect(sanitizeNickname('')).toBe('')
  })

  it('应该保留正常长度的昵称', () => {
    const nickname = 'TestUser123'
    expect(sanitizeNickname(nickname)).toBe(nickname)
  })
})

describe('isValidImageUrl', () => {
  it('应该接受 https URL', () => {
    expect(isValidImageUrl('https://example.com/image.jpg')).toBe(true)
  })

  it('应该接受 http URL', () => {
    expect(isValidImageUrl('http://example.com/image.jpg')).toBe(true)
  })

  it('应该拒绝 javascript: 协议', () => {
    expect(isValidImageUrl('javascript:alert(1)')).toBe(false)
  })

  it('应该拒绝 data: 协议', () => {
    expect(isValidImageUrl('data:image/svg+xml,<svg>')).toBe(false)
  })

  it('应该拒绝空字符串', () => {
    expect(isValidImageUrl('')).toBe(false)
  })

  it('应该拒绝 null', () => {
    expect(isValidImageUrl(null as any)).toBe(false)
  })

  it('应该拒绝 vbscript: 协议', () => {
    expect(isValidImageUrl('vbscript:msgbox(1)')).toBe(false)
  })

  it('应该拒绝 file: 协议', () => {
    expect(isValidImageUrl('file:///etc/passwd')).toBe(false)
  })

  it('应该区分大小写', () => {
    expect(isValidImageUrl('HTTP://example.com/img.jpg')).toBe(true)
    expect(isValidImageUrl('HTTPS://example.com/img.jpg')).toBe(true)
    expect(isValidImageUrl('JAVASCRIPT:alert(1)')).toBe(false)
  })
})

describe('sanitizeComment', () => {
  it('应该使用 1000 字符限制', () => {
    const longComment = 'a'.repeat(2000)
    const result = sanitizeComment(longComment)
    expect(result.length).toBeLessThanOrEqual(1000)
  })

  it('应该保留换行符', () => {
    const comment = 'Line 1\nLine 2\nLine 3'
    const result = sanitizeComment(comment)
    expect(result).toContain('\n')
  })

  it('应该移除危险内容', () => {
    const comment = '<script>alert(1)</script>Hello'
    const result = sanitizeComment(comment)
    expect(result).not.toContain('<script>')
  })

  it('应该处理空字符串', () => {
    expect(sanitizeComment('')).toBe('')
  })
})

describe('sanitizePost', () => {
  it('应该使用 10000 字符限制', () => {
    const longPost = 'a'.repeat(20000)
    const result = sanitizePost(longPost)
    expect(result.length).toBeLessThanOrEqual(10000)
  })

  it('应该保留换行符', () => {
    const post = 'Line 1\n\nLine 2'
    const result = sanitizePost(post)
    expect(result).toContain('\n')
  })

  it('应该移除危险内容', () => {
    const post = '<img src=x onerror="alert(1)">'
    const result = sanitizePost(post)
    expect(result).not.toContain('onerror=')
  })

  it('应该处理空字符串', () => {
    expect(sanitizePost('')).toBe('')
  })
})

describe('removeControlChars', () => {
  it('应该移除控制字符', () => {
    expect(removeControlChars('Hello\x00World\x1F')).toBe('HelloWorld')
  })

  it('应该保留换行符', () => {
    expect(removeControlChars('Line 1\nLine 2\tTab')).toBe('Line 1\nLine 2\tTab')
  })

  it('应该保留制表符', () => {
    expect(removeControlChars('\t\t')).toBe('\t\t')
  })

  it('应该保留回车符', () => {
    expect(removeControlChars('\r\n')).toBe('\r\n')
  })

  it('应该移除 DEL 字符 (0x7F)', () => {
    expect(removeControlChars('Hello\x7F')).toBe('Hello')
  })

  it('应该处理空字符串', () => {
    expect(removeControlChars('')).toBe('')
  })

  it('应该移除所有控制字符范围', () => {
    // 0x00-0x08, 0x0B-0x0C, 0x0E-0x1F, 0x7F
    const text = '\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0B\x0C\x0E\x0F\x1F\x7F'
    const result = removeControlChars(text)
    expect(result).toBe('')
  })
})
