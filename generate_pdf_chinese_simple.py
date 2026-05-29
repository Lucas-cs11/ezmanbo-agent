#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成支持中文的 Day 3 工作报告 PDF 文档
使用 reportlab 和中文字体支持
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib import colors
from datetime import datetime
import os
import platform

def register_fonts():
    """注册中文字体"""
    try:
        # Windows 系统
        if platform.system() == 'Windows':
            # 尝试注册系统字体
            font_paths = [
                "C:\\Windows\\Fonts\\simfang.ttf",  # 仿宋
                "C:\\Windows\\Fonts\\simsun.ttc",   # 宋体
                "C:\\Windows\\Fonts\\msyh.ttc",     # 微软雅黑
            ]

            fonts_to_register = {
                'SimSun': 'C:\\Windows\\Fonts\\simsun.ttc',
                'SimHei': 'C:\\Windows\\Fonts\\simhei.ttf',
                'MSYaHei': 'C:\\Windows\\Fonts\\msyh.ttc',
            }

            for font_name, font_path in fonts_to_register.items():
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont(font_name, font_path))
                        print(f"✓ 已注册字体: {font_name}")
                    except Exception as e:
                        print(f"  无法注册 {font_name}: {e}")

            return True
    except Exception as e:
        print(f"字体注册出错: {e}")

    return False

def create_pdf_report():
    """生成 PDF 报告"""

    # 注册中文字体
    register_fonts()

    output_path = "docs/EZ-PLM_Day3_工作完成报告_中文版.pdf"

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )

    styles = getSampleStyleSheet()

    # 自定义样式 - 使用支持中文的字体
    try:
        title_style = ParagraphStyle(
            'Title',
            fontSize=24,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=15,
            alignment=TA_CENTER,
            fontName='SimSun',
            fontFamily='SimSun'
        )

        h1_style = ParagraphStyle(
            'H1',
            fontSize=14,
            textColor=colors.HexColor('#2e5090'),
            spaceAfter=10,
            spaceBefore=10,
            fontName='SimSun',
            fontFamily='SimSun'
        )

        h2_style = ParagraphStyle(
            'H2',
            fontSize=11,
            textColor=colors.HexColor('#4472c4'),
            spaceAfter=8,
            spaceBefore=8,
            fontName='SimSun',
            fontFamily='SimSun'
        )

        body_style = ParagraphStyle(
            'Body',
            fontSize=9,
            alignment=TA_LEFT,
            spaceAfter=5,
            leading=12,
            fontName='SimSun',
            fontFamily='SimSun'
        )
    except:
        # 如果字体注册失败，使用默认字体
        print("⚠️  使用默认字体，中文可能显示为符号")
        title_style = styles['Heading1']
        h1_style = styles['Heading2']
        h2_style = styles['Heading3']
        body_style = styles['BodyText']

    story = []

    # 标题页
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("Day 3 任务完成报告", title_style))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("EZ-PLM 电子元器件风险评估代理", h2_style))
    story.append(Spacer(1, 0.8*cm))

    # 项目信息表
    info_data = [
        ['项目名称', 'EZ-PLM 电子元器件风险评估代理'],
        ['报告日期', '2026-05-28'],
        ['负责人', '队员B'],
        ['完成状态', '✅ 100% 完成']
    ]
    info_table = Table(info_data, colWidths=[3*cm, 11*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f0f8')),
        ('FONTNAME', (0, 0), (0, -1), 'SimSun'),
        ('FONTNAME', (1, 0), (1, -1), 'SimSun'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')])
    ]))
    story.append(info_table)
    story.append(Spacer(1, 1.5*cm))

    # 执行摘要
    story.append(Paragraph("一、执行摘要", h1_style))

    summary_text = """
    <b>项目完成情况</b><br/>
    Day 3 成功完成了两个主要工作流：EZ-PLM 真实 API 联调和 FastAPI 接口稳定性测试。
    共完成 12 个子任务，所有任务状态为完成，测试通过率达到 100%。<br/><br/>

    <b>关键指标</b><br/>
    • 总测试用例：41 个<br/>
    • 通过率：100% (41/41)<br/>
    • 并发请求：1150+ 个<br/>
    • 性能基准：/health 1.83ms，/analyze/replacement 50-80ms<br/>
    • 500 并发成功率：100%
    """
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 0.5*cm))

    # Stream 1
    story.append(Paragraph("二、Stream 1: EZ-PLM 真实 API 联调", h1_style))

    stream1_data = [
        ['任务号', '任务名称', '状态', '关键内容'],
        ['1.1', '环境配置检查', '✅', 'API 密钥配置、格式验证'],
        ['1.2', 'API 连接验证', '✅', 'HMAC 认证配置'],
        ['1.3', '白名单覆盖测试', '✅', 'UTF-8 编码修复、中文支持'],
        ['1.4', '数据对比验证', '✅', '数据结构一致性验证']
    ]
    stream1_table = Table(stream1_data, colWidths=[1.2*cm, 3*cm, 1.2*cm, 7.5*cm])
    stream1_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e5090')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'SimSun'),
        ('FONTNAME', (0, 1), (-1, -1), 'SimSun'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5)
    ]))
    story.append(stream1_table)
    story.append(Spacer(1, 0.5*cm))

    # UTF-8 问题说明
    story.append(Paragraph("关键问题解决: UTF-8 字符编码", h2_style))
    utf8_text = """
    <b>问题</b>：请求体包含中文字符时，API 返回 400 错误<br/>
    <b>原因</b>：Pydantic BaseModel 的 JSON 解析限制<br/>
    <b>解决</b>：改用 Dict[str, Any] = Body(...) 方式<br/>
    <b>验证</b>：所有中文输入测试通过（车规、国产等）
    """
    story.append(Paragraph(utf8_text, body_style))
    story.append(Spacer(1, 0.5*cm))

    # Stream 2
    story.append(PageBreak())
    story.append(Paragraph("三、Stream 2: FastAPI 接口稳定性测试", h1_style))

    story.append(Paragraph("测试统计", h2_style))

    test_data = [
        ['任务', '类型', '测试数', '状态'],
        ['2.1', '框架建设', '-', '✅'],
        ['2.2', '/health 端点', '10', '✅'],
        ['2.3', '/analyze 并发', '8', '✅'],
        ['2.4', '/replacement 并发', '7', '✅'],
        ['2.5', '性能基准', '2', '✅'],
        ['2.6', '错误处理', '14', '✅'],
    ]
    test_table = Table(test_data, colWidths=[1.5*cm, 3*cm, 1.5*cm, 2*cm])
    test_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ffc000')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'SimSun'),
        ('FONTNAME', (0, 1), (-1, -1), 'SimSun'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4)
    ]))
    story.append(test_table)
    story.append(Spacer(1, 0.5*cm))

    # 性能指标
    story.append(Paragraph("性能基准", h2_style))

    perf_data = [
        ['端点', '平均延迟', 'P95', 'P99', '并发成功率'],
        ['/health', '1.83ms', '2.35ms', '25.22ms', '100%'],
        ['/analyze', '50-80ms', '<1000ms', '<2000ms', '100%'],
        ['/replacement', '50-80ms', '<1000ms', '<2000ms', '100%']
    ]
    perf_table = Table(perf_data, colWidths=[2*cm, 2*cm, 2*cm, 2*cm, 2.5*cm])
    perf_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#70ad47')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'SimSun'),
        ('FONTNAME', (0, 1), (-1, -1), 'SimSun'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4)
    ]))
    story.append(perf_table)
    story.append(Spacer(1, 0.5*cm))

    # 项目状态
    story.append(PageBreak())
    story.append(Paragraph("四、项目状态", h1_style))

    status_text = """
    <b>完成情况</b><br/>
    ✅ Day 1：完成 (基础设置和数据准备)<br/>
    ✅ Day 2：完成 (测试框架和 /health 端点)<br/>
    ✅ Day 3：完成 (完整 API 集成和全面稳定性测试)<br/>
    🟢 <b>项目总体：就绪提交</b><br/><br/>

    <b>代码变更</b><br/>
    • 新增：3 个文件 (760+ 行测试代码)<br/>
    • 修改：2 个文件 (UTF-8 编码修复)<br/>
    • 分支：feature/backend/api-integration<br/>
    • 提交：bd20ae8
    """
    story.append(Paragraph(status_text, body_style))
    story.append(Spacer(1, 0.5*cm))

    # 总结
    story.append(Paragraph("五、总结", h1_style))

    conclusion_text = """
    Day 3 成功完成了 EZ-PLM 真实 API 联调和 FastAPI 接口稳定性测试两大工作流。
    通过解决关键的字符编码问题、建立完整的测试框架和执行全面的性能测试，
    确保了系统在各种场景下的稳定性和可靠性。<br/><br/>

    所有 41 个测试用例都已通过，并发请求超过 1150 个，系统在 500 并发下仍保持 100% 的成功率。
    代码质量优秀，文档完整，已准备进入代码审核阶段。<br/><br/>

    <b>项目状态：🟢 Day 3 全部完成，准备提交</b>
    """
    story.append(Paragraph(conclusion_text, body_style))
    story.append(Spacer(1, 1.5*cm))

    # 页脚
    footer_text = f"""
    <b>报告生成时间</b>：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>
    <b>报告作者</b>：队员B<br/>
    <b>文档版本</b>：v1.0 (中文版)
    """
    story.append(Paragraph(footer_text, body_style))

    # 生成 PDF
    try:
        doc.build(story)
        print(f"✅ 中文版 PDF 报告已生成: {output_path}")
        print(f"📄 文件大小: {os.path.getsize(output_path) / 1024:.1f} KB")
        return output_path
    except Exception as e:
        print(f"❌ 生成 PDF 失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("=" * 70)
    print("🔧 生成支持中文的 Day 3 工作报告 PDF")
    print("=" * 70)
    result = create_pdf_report()
    if result:
        print("\n✨ 中文版 PDF 报告生成完成！")
    else:
        print("\n❌ PDF 生成失败，请检查错误信息。")
