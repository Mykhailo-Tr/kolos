# pdf_generator.py
import os
import matplotlib
# Встановлюємо backend 'Agg' перед імпортом pyplot, щоб уникнути помилок на сервері
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

from io import BytesIO
from datetime import datetime
from decimal import Decimal

from django.conf import settings
from django.contrib.staticfiles import finders

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, Image, KeepTogether, PageBreak
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

class PDFReportGenerator:
    """Генератор PDF звітів з підтримкою графіків та української мови"""

    PRIMARY_COLOR = HexColor('#2563eb')
    SECONDARY_COLOR = HexColor('#64748b')
    HEADER_BG = HexColor('#f1f5f9')
    BORDER_COLOR = HexColor('#e2e8f0')
    SUCCESS_COLOR = '#10b981'   # зелений
    DANGER_COLOR = '#ef4444'    # червоний

    def __init__(self, title, orientation='portrait'):
        self.title = title
        self.orientation = orientation

        if orientation == 'landscape':
            self.pagesize = landscape(A4)
        else:
            self.pagesize = portrait(A4)

        self.page_width, self.page_height = self.pagesize
        self.margin_x = 1.5 * cm
        self.margin_y = 2.0 * cm
        self.content_width = self.page_width - (2 * self.margin_x)

        self.buffer = BytesIO()
        self.elements = []

        self.font_path = self._find_font_path()
        self._register_fonts()
        self.styles = self._create_styles()

    def _find_font_path(self):
        """Знаходить шлях до файлу шрифту"""
        font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'DejaVuSans.ttf')
        if not os.path.exists(font_path):
            found_path = finders.find('fonts/DejaVuSans.ttf')
            if found_path:
                font_path = found_path
        return font_path

    def _register_fonts(self):
        """Реєструє шрифт для PDF та Matplotlib"""
        try:
            if self.font_path and os.path.exists(self.font_path):
                # 1. Реєстрація для ReportLab
                pdfmetrics.registerFont(TTFont('Regular', self.font_path))
                # Нам підходить 'Regular' як основний і жирний, якщо немає Bold-файлу
                self.font_name = 'Regular'
                self.font_bold = 'Regular'

                # 2. Реєстрація для Matplotlib (щоб на графіках була кирилиця)
                font_manager.fontManager.addfont(self.font_path)
                plt.rcParams['font.family'] = 'DejaVu Sans'
            else:
                raise FileNotFoundError("Шрифт не знайдено")
        except Exception as e:
            # не кидаємо — fallback на стандартні шрифти
            print(f"Font warning: {e}")
            self.font_name = 'Helvetica'
            self.font_bold = 'Helvetica-Bold'

    def _create_styles(self):
        styles = getSampleStyleSheet()
        styles['Normal'].fontName = self.font_name
        styles['Normal'].fontSize = 10

        styles.add(ParagraphStyle(
            name='ReportTitle', parent=styles['Heading1'], fontSize=16,
            textColor=self.PRIMARY_COLOR, alignment=TA_CENTER, fontName=self.font_bold, spaceAfter=10
        ))

        styles.add(ParagraphStyle(
            name='SectionTitle', parent=styles['Heading2'], fontSize=12,
            textColor=HexColor('#1e293b'), spaceBefore=15, spaceAfter=10, fontName=self.font_bold
        ))

        styles.add(ParagraphStyle(
            name='TableHeader', parent=styles['Normal'], fontSize=9,
            textColor=colors.white, alignment=TA_CENTER, fontName=self.font_bold
        ))

        styles.add(ParagraphStyle(
            name='TableCell', parent=styles['Normal'], fontSize=9, alignment=TA_LEFT, fontName=self.font_name
        ))

        styles.add(ParagraphStyle(
            name='TableCellRight', parent=styles['Normal'], fontSize=9, alignment=TA_RIGHT, fontName=self.font_name
        ))

        # Допоміжні стилі
        styles.add(ParagraphStyle(
            name='Center', parent=styles['Normal'], alignment=TA_CENTER, fontName=self.font_name
        ))
        styles.add(ParagraphStyle(
            name='BoldSmall', parent=styles['Normal'], fontName=self.font_bold, fontSize=10
        ))

        return styles

    def _header_footer(self, canvas, doc):
        canvas.saveState()
        # Header
        canvas.setStrokeColor(self.PRIMARY_COLOR)
        canvas.setLineWidth(2)
        canvas.line(self.margin_x, self.page_height - 1.5*cm, self.page_width - self.margin_x, self.page_height - 1.5*cm)

        # Title at header left
        try:
            canvas.setFont(self.font_bold, 10)
        except Exception:
            canvas.setFont('Helvetica-Bold', 10)
        canvas.setFillColor(self.SECONDARY_COLOR)
        canvas.drawString(self.margin_x, self.page_height - 1.2*cm, "Система обліку зерна")

        # Generated timestamp at header right
        try:
            canvas.setFont(self.font_name, 9)
        except Exception:
            canvas.setFont('Helvetica', 9)
        date_str = datetime.now().strftime('%d.%m.%Y %H:%M')
        canvas.drawRightString(self.page_width - self.margin_x, self.page_height - 1.2*cm, f"Згенеровано: {date_str}")

        # Footer line
        canvas.setStrokeColor(self.BORDER_COLOR)
        canvas.setLineWidth(1)
        canvas.line(self.margin_x, 1.5*cm, self.page_width - self.margin_x, 1.5*cm)

        # Page number
        page_num = canvas.getPageNumber()
        try:
            canvas.setFont(self.font_name, 9)
        except Exception:
            canvas.setFont('Helvetica', 9)
        canvas.setFillColor(self.SECONDARY_COLOR)
        canvas.drawCentredString(self.page_width / 2, 1.0*cm, f"Сторінка {page_num}")
        canvas.restoreState()

    def add_subtitle(self, text, level=1):
        """Додає підзаголовок секції у PDF."""
        style = ParagraphStyle(
            name=f'SubtitleLevel{level}',
            parent=self.styles['Normal'],
            fontName=self.font_bold,
            fontSize=14 if level == 1 else 12,
            textColor=HexColor('#1e293b'),
            spaceBefore=12,
            spaceAfter=8,
        )
        self.elements.append(Paragraph(text, style))

    def add_spacer(self, size=12):
        """Додає вертикальний відступ (size у pts)."""
        self.elements.append(Spacer(1, size))

    def add_paragraph(self, text, style='Normal'):
        """Додає параграф у PDF."""
        paragraph_style = self.styles.get(style, self.styles['Normal'])
        self.elements.append(Paragraph(text, paragraph_style))

    def add_page_break(self):
        """Додає розрив сторінки."""
        self.elements.append(PageBreak())

    def get_paragraph(self, text, style='Normal'):
        """Повертає Paragraph (для вставки у таблиці)."""
        paragraph_style = self.styles.get(style, self.styles['Normal'])
        return Paragraph(text, paragraph_style)

    def add_header(self, subtitle=None, date_range=None):
        self.elements.append(Paragraph(self.title, self.styles['ReportTitle']))
        meta = []
        if subtitle:
            meta.append(subtitle)
        if date_range:
            if isinstance(date_range, tuple):
                meta.append(f"Період: {date_range[0]} - {date_range[1]}")
            else:
                meta.append(f"Дата: {date_range}")

        if meta:
            meta_style = ParagraphStyle(
                name='Meta', parent=self.styles['Normal'], alignment=TA_CENTER,
                textColor=self.SECONDARY_COLOR, spaceAfter=20, fontName=self.font_name
            )
            self.elements.append(Paragraph(" | ".join(meta), meta_style))

    def add_summary_box(self, summary_data):
        data = []
        for label, value in summary_data.items():
            style = self.styles['Normal']
            if not str(label).startswith(' '):
                style = ParagraphStyle('BoldLbl', parent=style, fontName=self.font_bold)
            data.append([Paragraph(label, style), Paragraph(str(value), self.styles['TableCellRight'])])

        width = min(12*cm, self.content_width)
        table = Table(data, colWidths=[width*0.6, width*0.4], hAlign='LEFT')
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.HEADER_BG),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.white),
            ('BOX', (0, 0), (-1, -1), 0.5, self.BORDER_COLOR),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        self.elements.append(Paragraph("Підсумки", self.styles['SectionTitle']))
        self.elements.append(table)
        self.elements.append(Spacer(1, 0.5*cm))

    def add_plot(self, figure):
        """Додає matplotlib figure у PDF"""
        img_buffer = BytesIO()
        figure.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)

        # Визначаємо розмір зображення, щоб воно влізло
        img_width = self.content_width
        img_height = img_width * 0.5  # Співвідношення 2:1

        im = Image(img_buffer, width=img_width, height=img_height)
        self.elements.append(Spacer(1, 0.5*cm))
        self.elements.append(im)
        self.elements.append(Spacer(1, 1*cm))
        plt.close(figure)

    def add_table(self, headers, data, col_widths=None, title=None, style=None):
        """
        headers: list of header strings
        data: list of rows (each row is list of cells). Cells can be Paragraph objects already.
        col_widths: list of widths in points or reportlab units (they will be scaled to content_width)
        title: optional section title
        style: optional list of TableStyle commands (ReportLab style tuples) to apply in addition to default
        """
        if title:
            self.elements.append(Paragraph(title, self.styles['SectionTitle']))

        header_row = [Paragraph(str(h), self.styles['TableHeader']) for h in headers]
        table_data = [header_row]
        for row in data:
            r_data = []
            for cell in row:
                # if cell is already a Paragraph instance, keep it
                if isinstance(cell, Paragraph):
                    r_data.append(cell)
                    continue

                if isinstance(cell, (int, float, Decimal)):
                    r_data.append(Paragraph(self._format_number(cell), self.styles['TableCellRight']))
                else:
                    r_data.append(Paragraph(str(cell) if cell is not None else '—', self.styles['TableCell']))
            table_data.append(r_data)

        # compute widths
        if not col_widths:
            widths = [self.content_width / len(headers)] * len(headers)
        else:
            # col_widths provided as numeric weights/absolute; we will scale weights to content_width
            try:
                total = sum(col_widths)
                widths = [w * (self.content_width / total) for w in col_widths]
            except Exception:
                widths = [self.content_width / len(headers)] * len(headers)

        table = Table(table_data, colWidths=widths, repeatRows=1)
        # default style
        base_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, self.BORDER_COLOR),
            ('BOX', (0, 0), (-1, -1), 0.5, self.BORDER_COLOR),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#f8fafc')]),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ])
        table.setStyle(base_style)

        # apply additional style rules if provided
        if style:
            try:
                table.setStyle(TableStyle(style))
            except Exception:
                # не падаємо, якщо стиль некоректний
                pass

        self.elements.append(table)
        self.elements.append(Spacer(1, 0.5*cm))

    def _format_number(self, value):
        if isinstance(value, Decimal):
            value = float(value)
        if isinstance(value, float):
            # формат: групування пробілами і кома як десятковий роздільник
            # якщо ціле число — показуємо без дробової частини
            if value.is_integer():
                return f"{int(value):,}".replace(',', ' ')
            return f"{value:,.3f}".replace(',', ' ').replace('.', ',')
        return str(value)

    def build(self):
        self.doc = SimpleDocTemplate(
            self.buffer, pagesize=self.pagesize,
            rightMargin=self.margin_x, leftMargin=self.margin_x,
            topMargin=self.margin_y, bottomMargin=self.margin_y,
            title=self.title
        )
        self.doc.build(self.elements, onFirstPage=self._header_footer, onLaterPages=self._header_footer)
        self.buffer.seek(0)
        return self.buffer


class ReportPDFBuilder:
    """Логіка побудови конкретних звітів та графіків"""

    @staticmethod
    def _create_bar_chart(labels, values, title, xlabel, ylabel):
        """Генерує стовпчасту діаграму"""
        fig, ax = plt.subplots(figsize=(10, 5))

        # Обмежимо кількість стовпчиків, щоб графік не був перевантажений
        if len(labels) > 15:
            labels = labels[:15]
            values = values[:15]
            title += " (Топ 15)"

        bars = ax.bar(labels, values, color='#2563eb', alpha=0.8)

        ax.set_title(title, pad=20)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)

        # Сітка
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        ax.set_axisbelow(True)

        # Поворот підписів
        plt.xticks(rotation=45, ha='right')

        # Додавання значень над стовпчиками
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.1f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=8)

        return fig

    @staticmethod
    def build_balance_report(data, date=None, filters=None):
        filters = filters or {}
        generator = PDFReportGenerator("Звіт по залишках", orientation=filters.get('orientation', 'landscape'))

        date_str = date.strftime('%d.%m.%Y') if date else datetime.now().strftime('%d.%m.%Y')
        generator.add_header(subtitle=f"Стан залишків на {date_str}")

        # Графік
        if filters.get('include_charts') and data.get('data'):
            # Групуємо дані для графіка (наприклад, сума по культурах)
            chart_data = {}
            for item in data['data']:
                name = f"{item['culture']} ({item['place']})"
                chart_data[name] = float(item['quantity'])

            # Сортуємо для краси
            sorted_items = sorted(chart_data.items(), key=lambda x: x[1], reverse=True)
            labels = [k for k, v in sorted_items]
            values = [v for k, v in sorted_items]

            fig = ReportPDFBuilder._create_bar_chart(
                labels, values,
                "Розподіл залишків", "Місце / Культура", "Кількість (т)"
            )
            generator.add_plot(fig)

        # Таблиця та підсумки (без змін)
        if data.get('aggregation'):
            summary = {
                'Загальна кількість': f"{data['aggregation'].get('total_quantity', 0):.3f} т",
                'Кількість позицій': data.get('total_rows', 0),
            }
            generator.add_summary_box(summary)

        headers = ['№', 'Місце', 'Культура', 'Тип', 'Кількість (т)']
        table_data = [[i, r.get('place'), r.get('culture'), r.get('type'), r.get('quantity')]
                      for i, r in enumerate(data.get('data', []), 1)]
        generator.add_table(headers, table_data, col_widths=[1.5*cm, 7*cm, 6*cm, 4*cm, 4*cm])

        return generator.build()

    @staticmethod
    def build_income_report(data, date_from, date_to, filters=None):
        filters = filters or {}
        generator = PDFReportGenerator("Звіт по приходу зерна", orientation=filters.get('orientation', 'landscape'))
        date_range = (date_from.strftime('%d.%m.%Y'), date_to.strftime('%d.%m.%Y'))
        generator.add_header(subtitle="Надходження з полів", date_range=date_range)

        # Графік: Динаміка по датах або Розподіл по культурах
        if filters.get('include_charts') and data.get('data'):
            # Спробуємо агрегацію по датах для графіка
            chart_data = {}
            for item in data['data']:
                d = item['date']
                chart_data[d] = chart_data.get(d, 0) + float(item['weight_net'])

            # Сортування дат
            sorted_dates = sorted(chart_data.items())  # Дати рядками, тому сортуються лексикографічно
            labels = [k for k, v in sorted_dates]
            values = [v for k, v in sorted_dates]

            fig = ReportPDFBuilder._create_bar_chart(
                labels, values,
                "Динаміка надходжень", "Дата", "Вага (т)"
            )
            generator.add_plot(fig)

        if data.get('aggregation'):
            summary = {'Всього': f"{data['aggregation'].get('total_weight', 0):.3f} т"}
            for k, v in data['aggregation'].get('by_culture', {}).items():
                summary[f"  {k}"] = f"{v:.3f} т"
            generator.add_summary_box(summary)

        headers = ['№', 'Дата', 'Поле', 'Культура', 'Місце', 'Вага (т)']
        table_data = [[i, r.get('date'), r.get('field'), r.get('culture'), r.get('place_to'), r.get('weight_net')]
                      for i, r in enumerate(data.get('data', []), 1)]
        generator.add_table(headers, table_data, col_widths=[1.5*cm, 2.5*cm, 5*cm, 4*cm, 5*cm, 3*cm])

        return generator.build()

    @staticmethod
    def build_balance_period_report(data, date_from, date_to, filters=None):
        filters = filters or {}
        generator = PDFReportGenerator("Динаміка залишків", orientation=filters.get('orientation', 'landscape'))
        date_range = (date_from.strftime('%d.%m.%Y'), date_to.strftime('%d.%m.%Y'))
        generator.add_header(subtitle="Порівняння залишків", date_range=date_range)

        # --- 1. Корекція та підготовка даних ---
        processed_data = []
        table_data = []

        for row in data:
            new_row = row.copy()

            try:
                start_qty_raw = row.get('start_quantity')
                end_qty_raw = row.get('end_quantity')
                start_qty = Decimal(str(start_qty_raw)) if start_qty_raw is not None and start_qty_raw != '' else Decimal(0)
                end_qty = Decimal(str(end_qty_raw)) if end_qty_raw is not None and end_qty_raw != '' else Decimal(0)
            except Exception:
                start_qty = Decimal(0)
                end_qty = Decimal(0)

            change = end_qty - start_qty
            change_percent_str = '0.00'
            change_percent = Decimal(0)
            if start_qty != Decimal(0):
                change_percent = (change / start_qty) * Decimal(100)
                change_percent_str = f"{change_percent.quantize(Decimal('0.01')):+.1f}"

            change_style = f"{change:,.3f}"
            if change > Decimal(0):
                change_style = f"<font color='{PDFReportGenerator.SUCCESS_COLOR}'>+{change:,.3f}</font>"
            elif change < Decimal(0):
                change_style = f"<font color='{PDFReportGenerator.DANGER_COLOR}'>{change:,.3f}</font>"

            change_paragraph = generator.get_paragraph(change_style, style='Center')

            table_data.append([
                row.get('place', '—'),
                row.get('culture', '—'),
                f"{start_qty:,.3f}",
                f"{end_qty:,.3f}",
                change_paragraph,
                f"{change_percent_str}%",
            ])

            new_row['change'] = float(change)
            new_row['change_percent'] = float(change_percent) if start_qty != 0 else 0.0
            processed_data.append(new_row)

        # --- 2. Генерація графіка ---
        if filters.get('include_charts') and processed_data:
            labels = []
            values = []
            sorted_data = sorted(processed_data, key=lambda x: abs(x['change']), reverse=True)[:10]
            for item in sorted_data:
                labels.append(f"{item.get('culture', '—')} ({item.get('place', '—')})")
                values.append(item['change'])

            fig, ax = plt.subplots(figsize=(10, 5))
            colors_list = ['#10b981' if v >= 0 else '#ef4444' for v in values]
            bars = ax.bar(labels, values, color=colors_list, alpha=0.8)
            ax.set_title("Топ змін залишків", pad=20)
            ax.axhline(0, color='black', linewidth=0.8)
            ax.grid(axis='y', linestyle='--', alpha=0.5)
            plt.xticks(rotation=45, ha='right')

            for bar in bars:
                height = bar.get_height()
                offset = 3 if height >= 0 else -12
                ax.annotate(f'{height:+.1f}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, offset),
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=8)

            generator.add_plot(fig)

        # --- 3. Таблиця ---
        headers = ['Місце', 'Культура', 'Початок (т)', 'Кінець (т)', 'Зміна (т)', 'Зміна (%)']
        generator.add_table(headers, table_data, col_widths=[6*cm, 6*cm, 3*cm, 3*cm, 3*cm, 2.5*cm])

        return generator.build()

    @staticmethod
    def build_shipment_summary(data, date_from, date_to, filters=None):
        filters = filters or {}
        generator = PDFReportGenerator("Звіт по ввезенню/вивезенню", orientation=filters.get('orientation', 'landscape'))
        date_range = (date_from.strftime('%d.%m.%Y'), date_to.strftime('%d.%m.%Y'))
        generator.add_header(subtitle="Зовнішні операції", date_range=date_range)

        if filters.get('include_charts') and data.get('aggregation'):
            agg = data['aggregation'].get('by_action', {})
            if agg:
                labels = list(agg.keys())
                values = list(agg.values())

                fig, ax = plt.subplots(figsize=(8, 4))
                ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90,
                       colors=['#3b82f6', '#10b981', '#f59e0b'],
                       textprops={'fontsize': 10})
                ax.set_title("Співвідношення операцій")

                generator.add_plot(fig)

        headers = ['Дата', 'Тип', 'Культура', 'Звідки', 'Куди', 'Вага']
        table_data = [[r.get('date'), r.get('action_type'), r.get('culture'),
                       r.get('place_from'), r.get('place_to'), r.get('weight_net')]
                      for r in data.get('data', [])]
        generator.add_table(headers, table_data, col_widths=[2.5*cm, 3*cm, 4*cm, 4.5*cm, 4.5*cm, 3*cm])

        return generator.build()
    
    @staticmethod
    def build_total_income_period_report(data, date_from, date_to, filters=None):
        """Створює звіт 'Прихід зерна (Загальний за період)'."""

        filters = filters or {}

        generator = PDFReportGenerator(
            "Прихід зерна (Загальний за період)",
            orientation=filters.get('orientation', 'portrait')
        )

        date_range = (
            date_from.strftime('%d.%m.%Y'),
            date_to.strftime('%d.%m.%Y')
        )

        generator.add_header(
            subtitle="Загальне надходження (Поля + Ввезення)",
            date_range=date_range
        )

        # =========================================================
        # Зведена інформація
        # =========================================================
        generator.add_subtitle("Зведена інформація (Загалом)", level=1)

        aggregation = data.get('aggregation', {})
        total_weight = aggregation.get('total_weight', 0.0)
        culture_agg = aggregation.get('by_culture', {})

        generator.add_table(
            headers=['Параметр', 'Значення'],
            data=[['Загальна вага приходу', f"{total_weight:,.3f} т"]],
            col_widths=[6.5 * cm, 6.5 * cm],
            style=[('FONTSIZE', (0, 0), (-1, -1), 10)]
        )

        generator.add_spacer(8)

        if culture_agg:
            generator.add_table(
                headers=['Культура', 'Вага (т)'],
                data=[[c, f"{w:,.3f}"] for c, w in culture_agg.items()],
                col_widths=[6.5 * cm, 6.5 * cm],
                style=[('FONTSIZE', (0, 0), (-1, -1), 10)]
            )

        # =========================================================
        # 1. Надходження з полів
        # =========================================================
        generator.add_page_break()
        generator.add_subtitle("1. Надходження з полів", level=1)

        rows = data.get('data', [])

        field_data = [r for r in rows if r.get('source') == 'Поле']
        field_agg = aggregation.get('field_aggregation', {})

        if field_data:
            generator.add_table(
                headers=['Параметр', 'Значення'],
                data=[['Загальна вага з полів', f"{field_agg.get('total_weight', 0.0):,.3f} т"]],
                col_widths=[6.5 * cm, 6.5 * cm]
            )

            generator.add_spacer(8)

            generator.add_table(
                headers=['Дата', 'Час', 'Документ', 'Поле', 'Культура', 'На місце', 'Вага (т)'],
                data=[
                    [
                        r.get('date'), r.get('time'), r.get('document'),
                        r.get('field'), r.get('culture'),
                        r.get('place_to'),
                        f"{r.get('weight_net', 0.0):,.3f}"
                    ]
                    for r in field_data
                ]
            )
        else:
            generator.add_paragraph("Немає надходжень з полів за вказаний період.")

        # =========================================================
        # 2. Зовнішнє ввезення
        # =========================================================
        generator.add_page_break()
        generator.add_subtitle("2. Зовнішнє ввезення", level=1)

        external_data = [r for r in rows if r.get('source') == 'Ввезення']
        external_agg = aggregation.get('external_aggregation', {})

        if external_data:
            generator.add_table(
                headers=['Параметр', 'Значення'],
                data=[['Загальна вага ввезення', f"{external_agg.get('total_weight', 0.0):,.3f} т"]],
                col_widths=[6.5 * cm, 6.5 * cm]
            )

            generator.add_spacer(8)

            generator.add_table(
                headers=['Дата', 'Час', 'Документ', 'Звідки', 'Культура', 'На місце', 'Вага (т)'],
                data=[
                    [
                        r.get('date'), r.get('time'), r.get('document'),
                        r.get('place_from'), r.get('culture'),
                        r.get('place_to'),
                        f"{r.get('weight_net', 0.0):,.3f}"
                    ]
                    for r in external_data
                ]
            )
        else:
            generator.add_paragraph("Немає зовнішніх ввезень за вказаний період.")

        return generator.build()
    @staticmethod
    def build_balance_period_history_report(data, date_from, date_to, filters):
        """
        PDF: Залишки за період (Історія)
        """
        from io import BytesIO
        buffer = BytesIO()

        # якщо у тебе вже є helper
        c = ReportPDFBuilder._create_canvas(
            buffer,
            orientation=filters.get('orientation', 'portrait')
        )

        ReportPDFBuilder._draw_title(
            c,
            f"Залишки за період (історія)\n{date_from:%d.%m.%Y} — {date_to:%d.%m.%Y}"
        )

        headers = ['Склад', 'Культура', 'Тип', 'Зміна, т']
        rows = [
            [
                r['place__name'],
                r['culture__name'],
                r['balance_type'],
                round(r['total_delta'], 3)
            ]
            for r in data['rows']
        ]

        ReportPDFBuilder._draw_table(c, headers, rows)

        ReportPDFBuilder._draw_footer(
            c,
            f"Загальна зміна: {round(data['aggregation']['total_weight'], 3)} т"
        )

        c.save()
        buffer.seek(0)
        return buffer
