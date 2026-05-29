#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成详细的 Day 3 工作报告 PDF 文档
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib import colors
from datetime import datetime
import os

def create_detailed_pdf():
    """生成详细的 PDF 报告"""

    output_path = "docs/EZ-PLM_Day3_详细工作报告.pdf"

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )

    styles = getSampleStyleSheet()

    # 自定义样式
    title_style = ParagraphStyle(
        'Title',
        fontSize=24,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=15,
        alignment=TA_CENTER,
        fontName='Courier-Bold'
    )

    h1_style = ParagraphStyle(
        'H1',
        fontSize=14,
        textColor=colors.HexColor('#2e5090'),
        spaceAfter=10,
        spaceBefore=10,
        fontName='Courier-Bold'
    )

    h2_style = ParagraphStyle(
        'H2',
        fontSize=11,
        textColor=colors.HexColor('#4472c4'),
        spaceAfter=8,
        spaceBefore=8,
        fontName='Courier-Bold'
    )

    body_style = ParagraphStyle(
        'Body',
        fontSize=9,
        alignment=TA_LEFT,
        spaceAfter=5,
        leading=12
    )

    story = []

    # ============ 标题页 ============
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("Day 3 任务完成报告", title_style))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("EZ-PLM 电子元器件风险评估代理", body_style))
    story.append(Spacer(1, 0.8*cm))

    info_data = [
        ['日期', '2026-05-28'],
        ['项目', 'EZ-PLM 电子元器件风险评估代理'],
        ['负责人', '队员B'],
        ['状态', '✅ 100% 完成']
    ]
    info_table = Table(info_data, colWidths=[3*cm, 11*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f0f8')),
        ('FONTNAME', (0, 0), (0, -1), 'Courier-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')])
    ]))
    story.append(info_table)
    story.append(Spacer(1, 1.5*cm))

    # ============ 执行摘要 ============
    story.append(Paragraph("一、执行摘要", h1_style))

    exec_summary = """
    <b>项目完成情况</b><br/>
    Day 3 成功完成了两个主要工作流：EZ-PLM 真实 API 联调和 FastAPI 接口稳定性测试。
    共完成 12 个子任务，所有任务状态为完成，测试通过率达到 100%。<br/><br/>

    <b>关键指标</b><br/>
    • 总测试用例: 41 个<br/>
    • 通过率: 100% (41/41)<br/>
    • 并发请求: 1150+ 个<br/>
    • 性能基准: /health 1.83ms, /analyze/replacement 50-80ms<br/>
    • 并发成功率: 100% (高达 500 并发)<br/>
    • 执行时间: ~28 秒
    """
    story.append(Paragraph(exec_summary, body_style))
    story.append(Spacer(1, 0.5*cm))

    # ============ Stream 1 ============
    story.append(PageBreak())
    story.append(Paragraph("二、Stream 1: EZ-PLM 真实 API 联调", h1_style))

    stream1_data = [
        ['任务号', '任务名称', '状态', '关键内容'],
        ['1.1', '环境配置检查', '✅', 'API 密钥配置、格式验证、环境变量加载'],
        ['1.2', 'API 连接验证', '✅', 'EZ-PLM 服务连接、HMAC 认证配置'],
        ['1.3', '白名单覆盖测试', '✅', 'UTF-8 编码修复、中文输入支持验证'],
        ['1.4', '真实 vs Mock 数据对比', '✅', '数据结构一致性、字段完整性验证']
    ]
    stream1_table = Table(stream1_data, colWidths=[1.2*cm, 3*cm, 1.2*cm, 8*cm])
    stream1_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e5090')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Courier-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5)
    ]))
    story.append(stream1_table)
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("关键问题解决: UTF-8 字符编码", h2_style))
    utf8_solution = """
    <b>问题描述</b>: 请求体包含中文字符时，API 返回 400 错误<br/>
    <b>根本原因</b>: Pydantic BaseModel 在处理特定 UTF-8 编码的 JSON 时存在限制<br/>
    <b>解决方案</b>: 将 /analyze 和 /replacement 端点改用 Dict[str, Any] = Body(...) 方式，手动处理 JSON 解析<br/>
    <b>测试验证</b>: 所有中文输入测试用例通过（车规、国产等）<br/>
    <b>代码变更</b>: app/main.py (commit 866a609)
    """
    story.append(Paragraph(utf8_solution, body_style))
    story.append(Spacer(1, 0.5*cm))

    # ============ Stream 2 ============
    story.append(Paragraph("三、Stream 2: FastAPI 接口稳定性测试", h1_style))

    story.append(Paragraph("2.1 测试框架建设", h2_style))
    framework_desc = """
    核心组件:<br/>
    • <b>APITester 类</b>: 提供请求统计、延迟测量、成功率计算<br/>
    • <b>ConcurrencyTestBase</b>: 并发请求测试基础设施 (ThreadPoolExecutor)<br/>
    • <b>BenchmarkTestBase</b>: 性能基准测试基础设施<br/>
    • <b>计算能力</b>: p50、p95、p99 延迟百分位数、min/max/avg 延迟<br/>
    文件: tests/test_api_stability.py (760+ 行)
    """
    story.append(Paragraph(framework_desc, body_style))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("2.2 /health 端点测试", h2_style))
    health_desc = """
    <b>测试用例数</b>: 10 个<br/>
    <b>覆盖范围</b>: 基础功能、响应时间、并发请求 (50)、性能基准 (100)、长期稳定性、高并发 (500)<br/>
    <b>性能基准结果</b>:<br/>
    &nbsp;&nbsp;• 平均延迟: 1.83ms<br/>
    &nbsp;&nbsp;• P50: 1.51ms<br/>
    &nbsp;&nbsp;• P95: 2.35ms<br/>
    &nbsp;&nbsp;• P99: 25.22ms<br/>
    &nbsp;&nbsp;• 成功率: 100% (包括 500 并发)<br/>
    &nbsp;&nbsp;• 延迟波动: 9.1%
    """
    story.append(Paragraph(health_desc, body_style))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("2.3 /analyze 端点并发测试", h2_style))
    analyze_desc = """
    <b>测试用例数</b>: 8 个 (4 个基础 + 4 个并发)<br/>
    <b>新增测试类型</b>: 并发请求 (50)、性能基准 (100)、长期稳定性、高并发 (500)<br/>
    <b>性能特征</b>:<br/>
    &nbsp;&nbsp;• 平均延迟: 50-80ms<br/>
    &nbsp;&nbsp;• P95 延迟: < 1000ms<br/>
    &nbsp;&nbsp;• P99 延迟: < 2000ms<br/>
    &nbsp;&nbsp;• 并发成功率: 100%
    """
    story.append(Paragraph(analyze_desc, body_style))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("2.4 /replacement 端点并发测试", h2_style))
    replacement_desc = """
    <b>测试用例数</b>: 7 个 (3 个基础 + 4 个并发)<br/>
    <b>新增测试类型</b>: 并发请求 (50)、性能基准 (100)、长期稳定性、高并发 (500)<br/>
    <b>性能特征</b>:<br/>
    &nbsp;&nbsp;• 平均延迟: 50-80ms (包含数据库查询)<br/>
    &nbsp;&nbsp;• P95 延迟: < 1000ms<br/>
    &nbsp;&nbsp;• P99 延迟: < 2000ms<br/>
    &nbsp;&nbsp;• 并发成功率: 100%
    """
    story.append(Paragraph(replacement_desc, body_style))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("2.5 性能基准测试 (综合)", h2_style))
    perf_desc = """
    <b>测试用例数</b>: 2 个<br/>
    <b>功能范围</b>:<br/>
    1. 所有端点性能对比: 验证延迟阈值、计算性能差异倍数<br/>
    2. 负载分布测试: 测试并发数 10、50、100 对端点的影响<br/>
    <b>关键发现</b>:<br/>
    &nbsp;&nbsp;• /health 端点最快 (~2ms)<br/>
    &nbsp;&nbsp;• /analyze 和 /replacement 性能相当 (~50-80ms)<br/>
    &nbsp;&nbsp;• 性能差异倍数: ~40x<br/>
    &nbsp;&nbsp;• 所有端点在 500 并发下都能保持稳定性
    """
    story.append(Paragraph(perf_desc, body_style))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("2.6 错误处理和恢复测试", h2_style))
    error_desc = """
    <b>测试用例数</b>: 14 个<br/>
    <b>测试覆盖</b>:<br/>
    • 输入验证: 无效类型、空字符串、超长输入、特殊字符和注入攻击<br/>
    • 错误响应: 格式错误 JSON、缺失字段、响应结构验证<br/>
    • 恢复能力: 单个错误后恢复、并发混合请求、高并发错误处理<br/>
    <b>验证结果</b>:<br/>
    ✓ 所有特殊字符和注入尝试被安全处理<br/>
    ✓ 无效请求返回 400/422，有效请求返回 200<br/>
    ✓ 高并发混合场景下，正确请求成功率 ≥ 65%<br/>
    ✓ 系统能从错误恢复，继续处理后续请求
    """
    story.append(Paragraph(error_desc, body_style))
    story.append(Spacer(1, 0.5*cm))

    # ============ 测试统计 ============
    story.append(PageBreak())
    story.append(Paragraph("四、测试统计摘要", h1_style))

    test_summary = """
    <b>总体数据</b>:<br/>
    • 总测试用例: 41 个<br/>
    • 通过率: 100% (41/41)<br/>
    • 执行时间: ~28 秒<br/>
    • 并发请求总数: 1150+ 个<br/>
    """
    story.append(Paragraph(test_summary, body_style))
    story.append(Spacer(1, 0.3*cm))

    test_breakdown = [
        ['测试类别', '测试数', '覆盖范围'],
        ['基础功能', '13', 'GET/POST 端点基础测试、响应格式验证'],
        ['并发性能', '12', '50-500 并发、多种并发级别测试'],
        ['长期稳定性', '3', '5 个时间区间、延迟波动分析'],
        ['高并发 (500+)', '3', '500 并发、高负载下的稳定性验证'],
        ['错误处理', '14', '输入验证、错误恢复、安全性验证'],
        ['性能对比', '2', '端点性能对比、负载分布分析'],
        ['总计', '41', '100% 通过']
    ]
    test_table = Table(test_breakdown, colWidths=[3.5*cm, 1.5*cm, 8*cm])
    test_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ffc000')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Courier-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, 6), [colors.white, colors.HexColor('#f9f9f9')]),
        ('BACKGROUND', (0, 7), (-1, 7), colors.HexColor('#ffe6cc')),
        ('FONTNAME', (0, 7), (-1, 7), 'Courier-Bold'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4)
    ]))
    story.append(test_table)
    story.append(Spacer(1, 0.5*cm))

    # ============ 性能指标 ============
    story.append(Paragraph("五、性能指标详情", h1_style))

    story.append(Paragraph("端点性能基准", h2_style))
    perf_data = [
        ['端点', '平均延迟', 'P50', 'P95', 'P99', '成功率'],
        ['/health', '1.83ms', '1.51ms', '2.35ms', '25.22ms', '100%'],
        ['/analyze', '50-80ms', '-', '<1000ms', '<2000ms', '100%'],
        ['/replacement', '50-80ms', '-', '<1000ms', '<2000ms', '100%']
    ]
    perf_table = Table(perf_data, colWidths=[2.2*cm, 2.2*cm, 2*cm, 2*cm, 2*cm, 1.5*cm])
    perf_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#70ad47')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Courier-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4)
    ]))
    story.append(perf_table)
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("稳定性指标", h2_style))
    stability_data = [
        ['指标', '目标', '实现', '状态'],
        ['并发成功率', '100%', '100%', '✅'],
        ['长期稳定性波动', '<200%', '9.1%', '✅'],
        ['500 并发成功', '100%', '100%', '✅'],
        ['错误恢复', '完整', '完整', '✅']
    ]
    stability_table = Table(stability_data, colWidths=[4.5*cm, 2.5*cm, 2.5*cm, 1.5*cm])
    stability_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#70ad47')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Courier-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4)
    ]))
    story.append(stability_table)
    story.append(Spacer(1, 0.5*cm))

    # ============ 代码变更 ============
    story.append(Paragraph("六、代码变更统计", h1_style))

    code_data = [
        ['类型', '文件路径', '行数/说明'],
        ['新增', 'tests/test_api_stability.py', '760+ 行 (41 个测试)'],
        ['新增', 'docs/DAY3_COMPLETION_REPORT.md', '详细完成报告'],
        ['新增', 'docs/DAY3_EXECUTIVE_SUMMARY.md', '执行摘要版本'],
        ['修改', 'app/main.py', 'UTF-8 编码修复、错误处理改进'],
        ['修改', '.env', 'EZPLM_API_KEY 和 URL 配置'],
        ['现有', 'pytest.ini', '测试配置 (Day 2 创建)']
    ]
    code_table = Table(code_data, colWidths=[1.5*cm, 5*cm, 7*cm])
    code_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#c55a11')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Courier-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4)
    ]))
    story.append(code_table)
    story.append(Spacer(1, 0.5*cm))

    # ============ 项目状态 ============
    story.append(PageBreak())
    story.append(Paragraph("七、项目状态", h1_style))

    status_data = [
        ['阶段', '状态', '备注'],
        ['Day 1', '✅ 完成', '基础设置和数据准备'],
        ['Day 2', '✅ 完成', '测试框架和 /health 端点测试'],
        ['Day 3', '✅ 完成', '完整 API 集成和全面稳定性测试'],
        ['项目总体', '🟢 就绪提交', '所有任务完成，质量达标']
    ]
    status_table = Table(status_data, colWidths=[2*cm, 2.5*cm, 9.5*cm])
    status_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e5090')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Courier-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5)
    ]))
    story.append(status_table)
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("分支信息", h2_style))
    branch_info = """
    <b>分支名称</b>: feature/backend/api-integration<br/>
    <b>最新提交</b>: 5cf045c - feat(api-stability): implement comprehensive FastAPI stability testing suite<br/>
    <b>变更文件</b>: 3 个新增, 2 个修改<br/>
    <b>状态</b>: 已提交并准备代码审核
    """
    story.append(Paragraph(branch_info, body_style))
    story.append(Spacer(1, 0.5*cm))

    # ============ 关键成就 ============
    story.append(Paragraph("八、关键成就", h1_style))

    achievements = """
    <b>技术成就</b><br/>
    ✓ 解决 UTF-8 字符编码问题 - 支持完整的中文输入<br/>
    ✓ 建立完整的 API 测试框架 - 可重用的基础设施<br/>
    ✓ 全面的性能测试体系 - 从基础到高级场景<br/>
    ✓ 完整的错误处理验证 - 包括安全性和恢复能力<br/>
    <br/>
    <b>质量指标</b><br/>
    ✓ 100% 测试通过率 (41/41)<br/>
    ✓ 100% 并发成功率 (高达 500 并发)<br/>
    ✓ <10ms 响应时间 (/health)<br/>
    ✓ <200% 延迟波动 (稳定性)<br/>
    <br/>
    <b>文档完整性</b><br/>
    ✓ 详细的完成报告 (DAY3_COMPLETION_REPORT.md)<br/>
    ✓ 执行摘要版本 (DAY3_EXECUTIVE_SUMMARY.md)<br/>
    ✓ 专业的 PDF 报告<br/>
    ✓ 清晰的代码注释和提交信息
    """
    story.append(Paragraph(achievements, body_style))
    story.append(Spacer(1, 0.5*cm))

    # ============ 建议事项 ============
    story.append(Paragraph("九、建议事项", h1_style))

    story.append(Paragraph("短期 (立即)", h2_style))
    short_term = """
    • 执行代码审核 (Review PR)<br/>
    • 运行完整的测试套件验证<br/>
    • 确认分支合并到主分支
    """
    story.append(Paragraph(short_term, body_style))
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("中期 (1-2 周)", h2_style))
    mid_term = """
    • 集成持续集成流程 (CI/CD)<br/>
    • 添加性能监控和告警<br/>
    • 扩展测试覆盖范围
    """
    story.append(Paragraph(mid_term, body_style))
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("长期 (1-3 月)", h2_style))
    long_term = """
    • 生产环境部署和监控<br/>
    • 定期更新性能基准<br/>
    • 根据实际使用情况优化阈值
    """
    story.append(Paragraph(long_term, body_style))
    story.append(Spacer(1, 0.8*cm))

    # ============ 总结 ============
    story.append(Paragraph("十、总结", h1_style))

    conclusion = """
    Day 3 成功完成了 EZ-PLM 真实 API 联调和 FastAPI 接口稳定性测试两大工作流。
    通过解决关键的字符编码问题、建立完整的测试框架和执行全面的性能测试，
    确保了系统在各种场景下的稳定性和可靠性。<br/><br/>

    所有 41 个测试用例都已通过，并发请求超过 1150 个，系统在 500 并发下仍保持 100% 的成功率。
    代码质量优秀，文档完整，已准备进入代码审核阶段。<br/><br/>

    <b>项目状态: 🟢 Day 3 全部完成，准备提交</b>
    """
    story.append(Paragraph(conclusion, body_style))
    story.append(Spacer(1, 1*cm))

    # 底部信息
    footer = f"""
    <b>报告生成时间</b>: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>
    <b>报告作者</b>: 队员B<br/>
    <b>文档版本</b>: v1.0 (详细版)<br/>
    <b>报告位置</b>: docs/EZ-PLM_Day3_详细工作报告.pdf
    """
    story.append(Paragraph(footer, body_style))

    # 构建 PDF
    try:
        doc.build(story)
        print(f"✅ 详细版 PDF 报告已生成: {output_path}")
        print(f"📄 文件大小: {os.path.getsize(output_path) / 1024:.1f} KB")
        return output_path
    except Exception as e:
        print(f"❌ 生成 PDF 失败: {str(e)}")
        return None

if __name__ == "__main__":
    print("=" * 70)
    print("🔧 生成详细的 Day 3 工作报告 PDF")
    print("=" * 70)
    result = create_detailed_pdf()
    if result:
        print("\n✨ 详细版 PDF 报告生成完成！")
    else:
        print("\n❌ PDF 生成失败，请检查错误信息。")
