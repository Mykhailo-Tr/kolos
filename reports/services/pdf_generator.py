import os
from io import BytesIO
from datetime import datetime
from decimal import Decimal

from django.conf import settings
from django.contrib.staticfiles import finders

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, 
    Spacer, PageBreak, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

class PDFReportGenerator:
    """Генератор PDF звітів з підтримкою української мови та виправленою орієнтацією"""
    
    PRIMARY_COLOR = HexColor('#2563eb')
    SECONDARY_COLOR = HexColor('#64748b')
    HEADER_BG = HexColor('#f1f5f9')
    BORDER_COLOR = HexColor('#e2e8f0')
    
    def __init__(self, title, orientation='portrait'):
        self.title = title
        self.orientation = orientation
        
        # Визначаємо розмір сторінки
        if orientation == 'landscape':
            self.pagesize = landscape(A4)
        else:
            self.pagesize = portrait(A4)
            
        # Розрахунок доступної ширини контенту
        self.page_width, self.page_height = self.pagesize
        self.margin_x = 1.5 * cm
        self.margin_y = 2.0 * cm
        self.content_width = self.page_width - (2 * self.margin_x)
        
        self.buffer = BytesIO()
        self.elements = []
        
        self._register_fonts()
        self.styles = self._create_styles()
        
    def _register_fonts(self):
        try:
            # Шлях до шрифту (переконайтеся, що файл є в static/fonts/)
            font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'DejaVuSans.ttf')
            
            if not os.path.exists(font_path):
                found_path = finders.find('fonts/DejaVuSans.ttf')
                if found_path:
                    font_path = found_path
            
            if font_path and os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('Regular', font_path))
                self.font_name = 'Regular'
                self.font_bold = 'Regular' 
            else:
                raise FileNotFoundError("Шрифт не знайдено")
                
        except Exception:
            # Fallback на стандартні шрифти (не підтримують кирилицю, але не ламають код)
            self.font_name = 'Helvetica'
            self.font_bold = 'Helvetica-Bold'

    def _create_styles(self):
        styles = getSampleStyleSheet()
        
        # Оновлення базових стилів
        styles['Normal'].fontName = self.font_name
        styles['Normal'].fontSize = 10
        styles['Heading1'].fontName = self.font_bold
        styles['Heading2'].fontName = self.font_bold
        
        styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=self.PRIMARY_COLOR,
            spaceAfter=10,
            alignment=TA_CENTER,
            fontName=self.font_bold
        ))
        
        styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=HexColor('#1e293b'),
            spaceBefore=15,
            spaceAfter=10,
            fontName=self.font_bold
        ))
        
        styles.add(ParagraphStyle(
            name='TableHeader',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.white,
            alignment=TA_CENTER,
            fontName=self.font_bold
        ))
        
        styles.add(ParagraphStyle(
            name='TableCell',
            parent=styles['Normal'],
            fontSize=9,
            alignment=TA_LEFT,
            fontName=self.font_name
        ))
        
        styles.add(ParagraphStyle(
            name='TableCellRight',
            parent=styles['Normal'],
            fontSize=9,
            alignment=TA_RIGHT,
            fontName=self.font_name
        ))
        
        return styles

    def _header_footer(self, canvas, doc):
        canvas.saveState()
        
        # Header
        canvas.setStrokeColor(self.PRIMARY_COLOR)
        canvas.setLineWidth(2)
        canvas.line(self.margin_x, self.page_height - 1.5*cm, self.page_width - self.margin_x, self.page_height - 1.5*cm)
        
        canvas.setFont(self.font_bold, 10)
        canvas.setFillColor(self.SECONDARY_COLOR)
        canvas.drawString(self.margin_x, self.page_height - 1.2*cm, "Система обліку зерна")
        
        canvas.setFont(self.font_name, 9)
        date_str = datetime.now().strftime('%d.%m.%Y %H:%M')
        canvas.drawRightString(self.page_width - self.margin_x, self.page_height - 1.2*cm, f"Згенеровано: {date_str}")

        # Footer
        canvas.setStrokeColor(self.BORDER_COLOR)
        canvas.setLineWidth(1)
        canvas.line(self.margin_x, 1.5*cm, self.page_width - self.margin_x, 1.5*cm)
        
        page_num = canvas.getPageNumber()
        canvas.setFont(self.font_name, 9)
        canvas.setFillColor(self.SECONDARY_COLOR)
        canvas.drawCentredString(self.page_width / 2, 1.0*cm, f"Сторінка {page_num}")
        
        canvas.restoreState()

    def add_header(self, subtitle=None, date_range=None):
        self.elements.append(Paragraph(self.title, self.styles['ReportTitle']))
        
        meta_parts = []
        if subtitle: meta_parts.append(subtitle)
        if date_range:
            if isinstance(date_range, tuple):
                meta_parts.append(f"Період: {date_range[0]} - {date_range[1]}")
            else:
                meta_parts.append(f"Дата: {date_range}")
        
        if meta_parts:
            self.elements.append(Paragraph(" | ".join(meta_parts), ParagraphStyle(
                name='Meta', parent=self.styles['Normal'], alignment=TA_CENTER, textColor=self.SECONDARY_COLOR, spaceAfter=20
            )))
    
    def add_summary_box(self, summary_data):
        data = []
        for label, value in summary_data.items():
            style = self.styles['Normal']
            if not label.startswith(' '):
                style = ParagraphStyle('BoldLbl', parent=style, fontName=self.font_bold)
            data.append([Paragraph(label, style), Paragraph(str(value), self.styles['TableCellRight'])])
        
        # Адаптивна ширина підсумкової таблиці
        summary_width = min(12*cm, self.content_width)
        table = Table(data, colWidths=[summary_width*0.6, summary_width*0.4], hAlign='LEFT')
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.HEADER_BG),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.white),
            ('BOX', (0, 0), (-1, -1), 0.5, self.BORDER_COLOR),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        
        self.elements.append(Paragraph("Підсумки", self.styles['SectionTitle']))
        self.elements.append(table)
        self.elements.append(Spacer(1, 0.5*cm))
    
    def add_table(self, headers, data, col_widths=None, title=None):
        if title:
            self.elements.append(Paragraph(title, self.styles['SectionTitle']))
        
        header_row = [Paragraph(str(h), self.styles['TableHeader']) for h in headers]
        table_data = [header_row]
        
        for row in data:
            row_data = []
            for cell in row:
                if isinstance(cell, (int, float, Decimal)):
                    row_data.append(Paragraph(self._format_number(cell), self.styles['TableCellRight']))
                else:
                    row_data.append(Paragraph(str(cell) if cell is not None else '—', self.styles['TableCell']))
            table_data.append(row_data)
        
        # Автоматичний розрахунок ширини колонок під сторінку
        if not col_widths:
            widths = [self.content_width / len(headers)] * len(headers)
        else:
            # Масштабування заданих пропорцій під реальну ширину
            total_req = sum(col_widths)
            ratio = self.content_width / total_req
            widths = [w * ratio for w in col_widths]
            
        table = Table(table_data, colWidths=widths, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, self.BORDER_COLOR),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#f8fafc')]),
        ]))
        
        self.elements.append(table)
        self.elements.append(Spacer(1, 0.5*cm))

    def _format_number(self, value):
        if isinstance(value, Decimal): value = float(value)
        if isinstance(value, float):
            return f"{int(value)}" if value.is_integer() else f"{value:,.3f}".replace(',', ' ').replace('.', ',')
        return str(value)
    
    def build(self):
        self.doc = SimpleDocTemplate(
            self.buffer,
            pagesize=self.pagesize,
            rightMargin=self.margin_x,
            leftMargin=self.margin_x,
            topMargin=self.margin_y,
            bottomMargin=self.margin_y,
            title=self.title
        )
        self.doc.build(self.elements, onFirstPage=self._header_footer, onLaterPages=self._header_footer)
        self.buffer.seek(0)
        return self.buffer


class ReportPDFBuilder:
    """Клас-будівельник, що коректно обробляє орієнтацію з фільтрів"""
    
    @staticmethod
    def _get_orientation(filters):
        """Отримуємо орієнтацію, за замовчуванням Portrait"""
        if not filters:
            return 'portrait'
        return filters.get('orientation', 'portrait')

    @staticmethod
    def build_balance_report(data, date=None, filters=None):
        filters = filters or {}
        # Тепер беремо орієнтацію динамічно з фільтрів
        orientation = filters.get('orientation', 'landscape') # Тут можна залишити landscape як дефолт для широких таблиць
        
        generator = PDFReportGenerator("Звіт по залишках", orientation=orientation)
        
        date_str = date.strftime('%d.%m.%Y') if date else datetime.now().strftime('%d.%m.%Y')
        generator.add_header(subtitle=f"Стан залишків на {date_str}")
        
        if data.get('aggregation'):
            summary = {
                'Загальна кількість': f"{data['aggregation'].get('total_quantity', 0):.3f} т",
                'Кількість позицій': data.get('total_rows', 0),
            }
            generator.add_summary_box(summary)
        
        headers = ['№', 'Місце', 'Культура', 'Тип', 'Кількість (т)']
        table_data = []
        for idx, row in enumerate(data.get('data', []), 1):
            table_data.append([
                idx, row.get('place', '—'), row.get('culture', '—'),
                row.get('type', '—'), row.get('quantity', 0)
            ])
            
        generator.add_table(headers, table_data, col_widths=[1.5*cm, 7*cm, 6*cm, 4*cm, 4*cm])
        return generator.build()
    
    @staticmethod
    def build_income_report(data, date_from, date_to, filters=None):
        filters = filters or {}
        orientation = filters.get('orientation', 'landscape')
        
        generator = PDFReportGenerator("Звіт по приходу зерна", orientation=orientation)
        date_range = (date_from.strftime('%d.%m.%Y'), date_to.strftime('%d.%m.%Y'))
        generator.add_header(subtitle="Надходження з полів", date_range=date_range)
        
        if data.get('aggregation'):
            summary = {'Всього': f"{data['aggregation'].get('total_weight', 0):.3f} т"}
            for k, v in data['aggregation'].get('by_culture', {}).items():
                summary[f"  {k}"] = f"{v:.3f} т"
            generator.add_summary_box(summary)
            
        headers = ['№', 'Дата', 'Поле', 'Культура', 'Місце', 'Вага (т)']
        table_data = [[
            idx, r.get('date'), r.get('field'), r.get('culture'), 
            r.get('place_to'), r.get('weight_net', 0)
        ] for idx, r in enumerate(data.get('data', []), 1)]
        
        generator.add_table(headers, table_data, col_widths=[1.5*cm, 2.5*cm, 5*cm, 4*cm, 5*cm, 3*cm])
        return generator.build()

    @staticmethod
    def build_balance_period_report(data, date_from, date_to, filters=None):
        filters = filters or {}
        orientation = filters.get('orientation', 'landscape')
        
        generator = PDFReportGenerator("Динаміка залишків", orientation=orientation)
        date_range = (date_from.strftime('%d.%m.%Y'), date_to.strftime('%d.%m.%Y'))
        generator.add_header(subtitle="Порівняння залишків", date_range=date_range)
        
        headers = ['Місце', 'Культура', 'Початок', 'Кінець', 'Зміна', '%']
        table_data = [[
            r.get('place'), r.get('culture'), r.get('start_quantity'), 
            r.get('end_quantity'), r.get('change'), 
            f"{r.get('change_percent', 0):+.1f}%"
        ] for r in data]
        
        generator.add_table(headers, table_data, col_widths=[6*cm, 6*cm, 3*cm, 3*cm, 3*cm, 2.5*cm])
        return generator.build()

    @staticmethod
    def build_shipment_summary(data, date_from, date_to, filters=None):
        filters = filters or {}
        orientation = filters.get('orientation', 'landscape')
        
        generator = PDFReportGenerator("Звіт по ввезенню/вивезенню", orientation=orientation)
        date_range = (date_from.strftime('%d.%m.%Y'), date_to.strftime('%d.%m.%Y'))
        generator.add_header(subtitle="Зовнішні операції", date_range=date_range)
        
        headers = ['Дата', 'Тип', 'Культура', 'Звідки', 'Куди', 'Вага']
        table_data = [[
            r.get('date'), r.get('action_type'), r.get('culture'),
            r.get('place_from'), r.get('place_to'), r.get('weight_net')
        ] for r in data.get('data', [])]
        
        generator.add_table(headers, table_data, col_widths=[2.5*cm, 3*cm, 4*cm, 4.5*cm, 4.5*cm, 3*cm])
        return generator.build()