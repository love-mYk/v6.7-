#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WellCorrelator v6.8 — 顶部工具栏 + UI美化 + 多道间距优化 + 地层速度计算
- 增加速度阶梯曲线上的 Zone 标注（厚度、平均速度、双程时间）
- 增加瞬时速度曲线自动生成和副道悬浮显示
- 保留原有所有功能
"""

import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path

try:
    import lasio
    HAS_LASIO = True
except ImportError:
    HAS_LASIO = False

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QFileDialog, QComboBox, QInputDialog,
    QSplitter, QMessageBox, QMenu, QColorDialog,
    QGraphicsPathItem, QTextEdit, QLineEdit, QCheckBox,
    QScrollArea, QGridLayout, QFrame,
    QTreeWidget, QTreeWidgetItem, QAbstractItemView, QHeaderView,
    QDialog, QDialogButtonBox, QSpinBox, QTableWidget, QTableWidgetItem,
    QProgressDialog, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QMimeData, QThread
from PyQt6.QtGui import QColor, QPainter, QPen, QCursor, QDragEnterEvent, QDropEvent, QFont, QDrag

import pyqtgraph as pg

# ---------- 全局配置 ----------
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
pg.setConfigOptions(antialias=True)

# ---------- 全局样式表 (同 v6.6，略微调整) ----------
GLOBAL_QSS = """
/* ════════════════════════════════
   BASE
════════════════════════════════ */
QMainWindow {
    background: #0F172A;
}

/* ════════════════════════════════
   SIDEBAR SHELL
════════════════════════════════ */
QWidget#sidebar {
    background: #1A2235;
    border-right: 1px solid #2D3F5C;
}

QWidget#sidebarHeader {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #1E3A5F, stop:1 #0F172A);
    border-bottom: 1px solid #2D3F5C;
}

QLabel#appTitle {
    color: #60A5FA;
    font-size: 15px;
    font-weight: 800;
    font-family: 'Segoe UI', 'SF Pro Display', Arial, sans-serif;
    letter-spacing: 0.5px;
    background: transparent;
}

QLabel#appSubtitle {
    color: #475569;
    font-size: 9px;
    font-family: 'Segoe UI', Arial, sans-serif;
    letter-spacing: 2px;
    font-weight: 600;
    background: transparent;
}

/* ════════════════════════════════
   SCROLL AREA
════════════════════════════════ */
QScrollBar:vertical {
    background: #1A2235;
    width: 5px;
    margin: 0;
    border: none;
}
QScrollBar::handle:vertical {
    background: #334155;
    border-radius: 2px;
    min-height: 20px;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical { height: 0; background: none; }
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical { background: none; }

/* ════════════════════════════════
   SECTION HEADERS (区分 A / B)
════════════════════════════════ */
QWidget#secHeader_A {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #1E3A8A, stop:1 #0F172A);
    border-left: 3px solid #3B82F6;
    border-radius: 6px;
}
QWidget#secHeader_B {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #5B21B6, stop:1 #0F172A);
    border-left: 3px solid #A855F7;
    border-radius: 6px;
}
QWidget#secHeader_Batch {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #065F46, stop:1 #0F172A);
    border-left: 3px solid #10B981;
    border-radius: 6px;
}

QLabel#secTitle_A {
    color: #93C5FD;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1.5px;
    font-family: 'Segoe UI', Arial, sans-serif;
    background: transparent;
}
QLabel#secTitle_B {
    color: #D8B4FE;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1.5px;
    font-family: 'Segoe UI', Arial, sans-serif;
    background: transparent;
}
QLabel#secTitle_Batch {
    color: #6EE7B7;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1.5px;
    font-family: 'Segoe UI', Arial, sans-serif;
    background: transparent;
}

/* ════════════════════════════════
   井分组容器
════════════════════════════════ */
QWidget#wellGroup_A {
    background: #151F2E;
    border-left: 3px solid #3B82F6;
    border-radius: 8px;
    margin: 4px 0px 8px 0px;
}
QWidget#wellGroup_B {
    background: #151F2E;
    border-left: 3px solid #A855F7;
    border-radius: 8px;
    margin: 4px 0px 8px 0px;
}

/* 井名标签 */
QLabel#wellNameLabel_A {
    color: #BFDBFE;
    font-size: 12px;
    font-weight: 700;
    background: #1E3A8A;
    border-radius: 5px;
    padding: 4px 10px;
    font-family: 'Segoe UI', Arial, sans-serif;
}
QLabel#wellNameLabel_B {
    color: #E9D5FF;
    font-size: 12px;
    font-weight: 700;
    background: #4C1D95;
    border-radius: 5px;
    padding: 4px 10px;
    font-family: 'Segoe UI', Arial, sans-serif;
}

/* 通用侧边栏标签 */
QWidget#sidebar QLabel {
    color: #94A3B8;
    font-size: 11px;
    font-family: 'Segoe UI', Arial, sans-serif;
    background: transparent;
}

QLabel#subLabel {
    color: #475569;
    font-size: 9px;
    letter-spacing: 1px;
    font-weight: 700;
    padding-top: 6px;
    background: transparent;
    text-transform: uppercase;
}

/* ════════════════════════════════
   按钮样式
════════════════════════════════ */
QWidget#sidebar QPushButton {
    background: #1E293B;
    color: #CBD5E1;
    border: 1px solid #2D3F5C;
    border-radius: 5px;
    padding: 5px 8px;
    font-size: 11px;
    font-weight: 600;
    font-family: 'Segoe UI', Arial, sans-serif;
}
QWidget#sidebar QPushButton:hover {
    background: #2D3F5C;
    border-color: #3B82F6;
    color: #F1F5F9;
}
QWidget#sidebar QPushButton:pressed {
    background: #0F172A;
}

QPushButton#loadBtn_A {
    background: #1E3A8A;
    color: #BFDBFE;
    font-weight: 700;
    border: 1px solid #3B82F6;
    border-radius: 5px;
    padding: 6px 10px;
}
QPushButton#loadBtn_A:hover {
    background: #2563EB;
    color: #FFFFFF;
}

QPushButton#loadBtn_B {
    background: #4C1D95;
    color: #E9D5FF;
    font-weight: 700;
    border: 1px solid #A855F7;
    border-radius: 5px;
    padding: 6px 10px;
}
QPushButton#loadBtn_B:hover {
    background: #7E22CE;
    color: #FFFFFF;
}

QPushButton#loadBtn_Batch {
    background: #064E3B;
    color: #A7F3D0;
    font-weight: 700;
    border: 1px solid #10B981;
    border-radius: 5px;
    padding: 6px 10px;
}
QPushButton#loadBtn_Batch:hover {
    background: #047857;
    color: #FFFFFF;
}

QPushButton#ghostBtn {
    background: #334155;
    color: #FDE047;
    border: 1px solid #CA8A04;
    font-weight: 600;
}
QPushButton#ghostBtn:hover:!checked {
    background: #475569;
    border-color: #EAB308;
}
QPushButton#ghostBtn:checked {
    background: #854D0E;
    border-color: #FACC15;
    color: #FEF08A;
}

/* 充填颜色按钮 */
QPushButton#fillBtnLeft, QPushButton#fillBtnRight {
    border-radius: 5px;
    padding: 5px 8px;
    font-size: 11px;
    font-weight: 600;
    border: 1px solid #475569;
}

/* ════════════════════════════════
   输入控件
════════════════════════════════ */
QWidget#sidebar QLineEdit {
    background: #0F172A;
    color: #E2E8F0;
    border: 1px solid #334155;
    border-radius: 5px;
    padding: 5px 6px;
    font-size: 11px;
    font-family: 'Consolas', monospace;
    selection-background-color: #3B82F6;
}
QWidget#sidebar QLineEdit:focus {
    border-color: #3B82F6;
    background: #1E293B;
}

QWidget#sidebar QComboBox {
    background: #0F172A;
    color: #E2E8F0;
    border: 1px solid #334155;
    border-radius: 5px;
    padding: 5px 8px;
    font-size: 11px;
    font-family: 'Segoe UI', Arial, sans-serif;
}
QWidget#sidebar QComboBox:hover {
    border-color: #64748B;
}
QWidget#sidebar QComboBox::drop-down {
    border: none;
    width: 18px;
}
QWidget#sidebar QComboBox QAbstractItemView {
    background: #1E293B;
    color: #E2E8F0;
    border: 1px solid #475569;
    selection-background-color: #3B82F6;
}

QWidget#sidebar QCheckBox {
    color: #94A3B8;
    font-size: 11px;
    spacing: 6px;
    background: transparent;
}
QWidget#sidebar QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #475569;
    border-radius: 3px;
    background: #0F172A;
}
QWidget#sidebar QCheckBox::indicator:checked {
    background: #3B82F6;
    border-color: #60A5FA;
}

QWidget#sidebar QTextEdit {
    background: #0F172A;
    color: #E2E8F0;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px;
    font-size: 11px;
    font-family: 'Consolas', monospace;
}
QWidget#sidebar QTextEdit:focus {
    border-color: #3B82F6;
}

/* 分割线与签名 */
QFrame#divider {
    background: #2D3F5C;
    max-height: 1px;
    min-height: 1px;
    border: none;
    margin: 6px 0;
}

QLabel#signature {
    color: #334155;
    font-size: 9px;
    font-family: 'Segoe UI', Arial, sans-serif;
    letter-spacing: 1px;
    padding: 6px;
    background: #0F172A;
    border-top: 1px solid #1A2235;
}
QPushButton#toggleBtn {
    background: #1A2235;
    border: none;
    border-right: 1px solid #2D3F5C;
    font-size: 11px;
    color: #475569;
    padding: 0px;
}
QPushButton#toggleBtn:hover {
    background: #2D3F5C;
    color: #94A3B8;
}

/* ════════════════════════════════
   顶部工具栏
════════════════════════════════ */
QWidget#topBar {
    background: #0F172A;
    border-bottom: 1px solid #1A2235;
}
QWidget#topBarInner {
    background: transparent;
}
QPushButton#topBarToggle {
    background: #1A2235;
    color: #475569;
    border: none;
    border-bottom: 1px solid #2D3F5C;
    font-size: 10px;
    padding: 2px 0;
    min-height: 14px;
}
QPushButton#topBarToggle:hover {
    background: #2D3F5C;
    color: #94A3B8;
}
QWidget#topBar QLabel {
    color: #64748B;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    background: transparent;
    font-family: 'Segoe UI', Arial, sans-serif;
}
QWidget#topBar QLabel#wellTag_A {
    color: #60A5FA;
    font-size: 11px;
    font-weight: 800;
    background: #1E3A8A;
    border-radius: 4px;
    padding: 2px 8px;
}
QWidget#topBar QLabel#wellTag_B {
    color: #C084FC;
    font-size: 11px;
    font-weight: 800;
    background: #4C1D95;
    border-radius: 4px;
    padding: 2px 8px;
}
QWidget#topBar QPushButton {
    background: #1A2235;
    color: #94A3B8;
    border: 1px solid #2D3F5C;
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 11px;
    font-weight: 600;
    font-family: 'Segoe UI', Arial, sans-serif;
}
QWidget#topBar QPushButton:hover {
    background: #2D3F5C;
    border-color: #3B82F6;
    color: #F1F5F9;
}
QWidget#topBar QPushButton:pressed {
    background: #0F172A;
}
QWidget#topBar QComboBox {
    background: #1A2235;
    color: #CBD5E1;
    border: 1px solid #2D3F5C;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 11px;
    font-family: 'Segoe UI', Arial, sans-serif;
    min-width: 80px;
}
QWidget#topBar QComboBox:hover {
    border-color: #3B82F6;
}
QWidget#topBar QComboBox::drop-down {
    border: none;
    width: 16px;
}
QWidget#topBar QComboBox QAbstractItemView {
    background: #1E293B;
    color: #E2E8F0;
    border: 1px solid #334155;
    selection-background-color: #3B82F6;
}
QWidget#topBar QLineEdit {
    background: #1A2235;
    color: #CBD5E1;
    border: 1px solid #2D3F5C;
    border-radius: 4px;
    padding: 4px 6px;
    font-size: 11px;
    font-family: 'Consolas', monospace;
    min-width: 55px;
    max-width: 70px;
}
QWidget#topBar QLineEdit:focus {
    border-color: #3B82F6;
}
QFrame#topDivider {
    background: #2D3F5C;
    max-width: 1px;
    min-width: 1px;
    border: none;
    margin: 4px 4px;
}

QStatusBar {
    background: #0F172A;
    color: #475569;
    font-size: 11px;
    font-family: 'Segoe UI', Arial, sans-serif;
}
"""

# ---------- 树形面板 QSS ----------
TREE_QSS = """
QTreeWidget {
    background: #1A2235;
    border: none;
    color: #CBD5E1;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 12px;
    outline: 0;
}
QTreeWidget::item {
    height: 26px;
    padding-left: 2px;
    border: none;
    border-radius: 4px;
}
QTreeWidget::item:hover {
    background: #2D3F5C;
    color: #F1F5F9;
}
QTreeWidget::item:selected {
    background: #1D4ED8;
    color: #FFFFFF;
    border-radius: 4px;
}
QTreeWidget::branch {
    background: #1A2235;
}
QTreeWidget::branch:has-children:!has-siblings:closed,
QTreeWidget::branch:closed:has-children:has-siblings {
    border-image: none;
    image: none;
    background: #1A2235;
    color: #64748B;
}
QTreeWidget::branch:open:has-children:!has-siblings,
QTreeWidget::branch:open:has-children:has-siblings {
    border-image: none;
    image: none;
    background: #1A2235;
    color: #94A3B8;
}
QTreeWidget::branch:closed:has-children {
    border-image: none;
    image: none;
    background-color: #1A2235;
}
QTreeWidget::branch:open:has-children {
    border-image: none;
    image: none;
    background-color: #1A2235;
}
QHeaderView::section {
    background: #0F172A;
    color: #64748B;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    border: none;
    padding: 4px 8px;
    border-bottom: 1px solid #1E293B;
}
/* Drop zone highlight */
QTreeWidget[dropHighlight="true"] {
    border: 2px dashed #3B82F6;
}
"""

# ---------- 颜色常量 (Zone / Top) ----------
ZONE_COLORS = [
    (255, 200, 180, 40), (180, 220, 255, 40), (200, 255, 200, 40),
    (255, 255, 180, 40), (220, 200, 255, 40), (255, 220, 180, 40),
    (180, 255, 220, 40), (240, 200, 255, 40),
]

TOP_COLORS = [
    "#FF4444", "#44FF44", "#4444FF", "#FFFF44", "#FF44FF", "#44FFFF",
    "#FF8844", "#88FF44", "#4488FF", "#FF44AA", "#AAFF44", "#44AAFF"
]

_GHOST_PALETTE = [
    (233, 30, 99), (255, 152, 0), (156, 39, 176),
    (0, 188, 212), (76, 175, 80), (255, 87, 34),
    (96, 125, 139),
]
_ghost_color_idx = 0

def _next_ghost_color():
    global _ghost_color_idx
    c = _GHOST_PALETTE[_ghost_color_idx % len(_GHOST_PALETTE)]
    _ghost_color_idx += 1
    return c

# ---------- DTW 距离计算 ----------
def dtw_distance(seq1, seq2):
    n, m = len(seq1), len(seq2)
    dtw = np.full((n+1, m+1), np.inf)
    dtw[0, 0] = 0
    for i in range(1, n+1):
        for j in range(1, m+1):
            cost = abs(seq1[i-1] - seq2[j-1])
            dtw[i, j] = cost + min(dtw[i-1, j], dtw[i, j-1], dtw[i-1, j-1])
    distance = dtw[n, m]
    max_diff = max(np.ptp(seq1), np.ptp(seq2))
    max_len = max(n, m)
    max_possible = max_diff * max_len
    if max_possible > 0:
        similarity = max(0.0, 100.0 * (1.0 - distance / max_possible))
    else:
        similarity = 100.0
    return distance, similarity

# ---------- 地层速度计算模块 ----------
def compute_zone_velocities(well, dt_curve_name, dt_unit='us/ft', output_vel_unit='m/s'):
    df = well.df
    depth = well.depth
    if dt_curve_name not in df.columns:
        raise ValueError(f"曲线 {dt_curve_name} 不存在")
    dt = df[dt_curve_name].values.astype(float)
    zones = well.topset.Zones
    results = []
    for zone in zones:
        mask = (depth >= zone.md_from) & (depth <= zone.md_to)
        d_zone = depth[mask]
        dt_zone = dt[mask]
        valid = (dt_zone > 0) & ~np.isnan(dt_zone)
        if valid.sum() < 2:
            continue
        d_zone = d_zone[valid]
        dt_zone = dt_zone[valid]
        thickness = d_zone[-1] - d_zone[0]
        if dt_unit == 'us/ft':
            d_ft = d_zone / 0.3048
            delta_d_ft = np.diff(d_ft)
            dt_avg = (dt_zone[:-1] + dt_zone[1:]) / 2.0
            time_sec = np.sum(dt_avg * 1e-6 * delta_d_ft)
        else:
            delta_d_m = np.diff(d_zone)
            dt_avg = (dt_zone[:-1] + dt_zone[1:]) / 2.0
            time_sec = np.sum(dt_avg * 1e-6 * delta_d_m)
        if time_sec <= 0:
            continue
        vel_mps = thickness / time_sec
        if output_vel_unit == 'km/s':
            vel = vel_mps / 1000.0
        else:
            vel = vel_mps
        results.append({
            'zone': zone.name,
            'thickness_m': thickness,
            'velocity': vel,
            'oneway_time_s': time_sec,
            'twt_s': 2 * time_sec,
            'vel_unit': output_vel_unit
        })
    return results

# ---------- 速度参数对话框 (新增两个复选框) ----------
class VelocityDialog(QDialog):
    def __init__(self, curves, default_curve=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("地层速度计算参数")
        self.setMinimumWidth(400)
        self.setStyleSheet("""
            QDialog { background: #1E293B; }
            QLabel { color: #CBD5E1; font-size: 11px; }
            QComboBox, QComboBox QAbstractItemView {
                background: #0F172A;
                color: #E2E8F0;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 4px 6px;
            }
            QPushButton {
                background: #2563EB;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover { background: #3B82F6; }
            QRadioButton, QCheckBox { color: #CBD5E1; }
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 曲线选择
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("DT 曲线:"))
        self.cmb_curve = QComboBox()
        self.cmb_curve.addItems(curves)
        if default_curve and default_curve in curves:
            self.cmb_curve.setCurrentText(default_curve)
        row1.addWidget(self.cmb_curve, 1)
        layout.addLayout(row1)

        # DT 单位
        group_unit = QWidget()
        group_unit.setStyleSheet("background:#0F172A; border-radius:6px; padding:6px;")
        gl_unit = QGridLayout(group_unit)
        gl_unit.setContentsMargins(8, 8, 8, 8)
        gl_unit.addWidget(QLabel("DT 单位:"), 0, 0)
        self.radio_usft = QRadioButton("us/ft")
        self.radio_usm = QRadioButton("us/m")
        self.radio_usft.setChecked(True)
        gl_unit.addWidget(self.radio_usft, 0, 1)
        gl_unit.addWidget(self.radio_usm, 0, 2)
        layout.addWidget(group_unit)

        # 输出速度单位
        group_out = QWidget()
        group_out.setStyleSheet("background:#0F172A; border-radius:6px; padding:6px;")
        gl_out = QGridLayout(group_out)
        gl_out.setContentsMargins(8, 8, 8, 8)
        gl_out.addWidget(QLabel("输出速度单位:"), 0, 0)
        self.radio_ms = QRadioButton("m/s")
        self.radio_kms = QRadioButton("km/s")
        self.radio_ms.setChecked(True)
        gl_out.addWidget(self.radio_ms, 0, 1)
        gl_out.addWidget(self.radio_kms, 0, 2)
        layout.addWidget(group_out)

        # 是否添加平均速度曲线
        self.chk_add_curve = QCheckBox("将平均速度作为阶梯曲线添加到数据框（新道）")
        self.chk_add_curve.setChecked(True)
        layout.addWidget(self.chk_add_curve)

        # 新增：是否显示 Zone 标注
        self.chk_show_labels = QCheckBox("在速度道上显示 Zone 标注（厚度/速度/双程时间）")
        self.chk_show_labels.setChecked(True)
        layout.addWidget(self.chk_show_labels)

        # 新增：是否生成瞬时速度曲线
        self.chk_gen_inst = QCheckBox("生成瞬时速度曲线并自动添加为副道")
        self.chk_gen_inst.setChecked(True)
        layout.addWidget(self.chk_gen_inst)

        # 按钮
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_parameters(self):
        dt_unit = 'us/ft' if self.radio_usft.isChecked() else 'us/m'
        vel_unit = 'm/s' if self.radio_ms.isChecked() else 'km/s'
        return {
            'curve': self.cmb_curve.currentText(),
            'dt_unit': dt_unit,
            'output_vel_unit': vel_unit,
            'add_curve': self.chk_add_curve.isChecked(),
            'show_labels': self.chk_show_labels.isChecked(),
            'gen_inst': self.chk_gen_inst.isChecked()
        }

# ---------- 速度结果表格对话框 ----------
class VelocityResultDialog(QDialog):
    def __init__(self, results, well_name, curve_name, parent=None):
        super().__init__(parent)
        self.results = results
        self.well_name = well_name
        self.curve_name = curve_name
        self.setWindowTitle(f"地层速度计算结果 - {well_name}")
        self.setMinimumSize(720, 400)
        self.setStyleSheet("QDialog { background: #1E293B; }")
        layout = QVBoxLayout(self)

        info = QLabel(f"井: {well_name}  |  DT: {curve_name}")
        info.setStyleSheet("color:#94A3B8; font-size:11px; padding:4px;")
        layout.addWidget(info)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Zone 名称", "厚度 (m)", "平均速度", "单程时间 (s)", "双程时间 (s)", "速度单位"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background: #0F172A;
                color: #E2E8F0;
                gridline-color: #334155;
                font-size: 11px;
            }
            QTableWidget::item:selected {
                background: #1D4ED8;
            }
            QHeaderView::section {
                background: #1A2235;
                color: #94A3B8;
                padding: 4px;
                font-weight: bold;
            }
        """)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._populate_table()
        layout.addWidget(self.table, stretch=1)

        btn_layout = QHBoxLayout()
        btn_export = QPushButton("导出 CSV")
        btn_export.clicked.connect(self._export_csv)
        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_export)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

    def _populate_table(self):
        self.table.setRowCount(len(self.results))
        vel_unit = self.results[0]['vel_unit'] if self.results else ''
        for i, r in enumerate(self.results):
            self.table.setItem(i, 0, QTableWidgetItem(r['zone']))
            self.table.setItem(i, 1, QTableWidgetItem(f"{r['thickness_m']:.2f}"))
            self.table.setItem(i, 2, QTableWidgetItem(f"{r['velocity']:.2f}"))
            self.table.setItem(i, 3, QTableWidgetItem(f"{r['oneway_time_s']:.6f}"))
            self.table.setItem(i, 4, QTableWidgetItem(f"{r['twt_s']:.6f}"))
            self.table.setItem(i, 5, QTableWidgetItem(vel_unit))
        self.table.resizeColumnsToContents()

    def _export_csv(self):
        if not self.results:
            return
        path, _ = QFileDialog.getSaveFileName(self, "保存 CSV", f"{self.well_name}_velocity.csv", "CSV (*.csv)")
        if not path:
            return
        import csv
        with open(path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Zone", "Thickness_m", "AvgVelocity", "OneWayTime_s", "TwoWayTime_s", "VelocityUnit"])
            for r in self.results:
                writer.writerow([r['zone'], r['thickness_m'], r['velocity'], r['oneway_time_s'], r['twt_s'], r['vel_unit']])
        QMessageBox.information(self, "导出成功", f"已保存到: {path}")

# ---------- 双击层线触发拉平 ----------
class TopLine(pg.InfiniteLine):
    sigDoubleClicked = pyqtSignal(object)

    def mouseDoubleClickEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.sigDoubleClicked.emit(self)
            ev.accept()
        else:
            super().mouseDoubleClickEvent(ev)

# ---------- 全局颜色管理器 ----------
class ZoneColorManager:
    def __init__(self):
        self._zone_color_map = {}
        self._next_color_idx = 0

    def get_color(self, zone_name: str):
        if zone_name not in self._zone_color_map:
            color = ZONE_COLORS[self._next_color_idx % len(ZONE_COLORS)]
            self._zone_color_map[zone_name] = color
            self._next_color_idx += 1
        return self._zone_color_map[zone_name]

    def clear(self):
        self._zone_color_map.clear()
        self._next_color_idx = 0

class TopColorManager:
    def __init__(self):
        self._top_color_map = {}
        self._next_color_idx = 0

    def get_color(self, top_name: str) -> str:
        if top_name not in self._top_color_map:
            color = TOP_COLORS[self._next_color_idx % len(TOP_COLORS)]
            self._top_color_map[top_name] = color
            self._next_color_idx += 1
        return self._top_color_map[top_name]

    def register_color(self, top_name: str, color: str):
        if top_name not in self._top_color_map:
            self._top_color_map[top_name] = color

    def remove(self, top_name: str):
        self._top_color_map.pop(top_name, None)

    def clear(self):
        self._top_color_map.clear()
        self._next_color_idx = 0

# ---------- 数据模型 ----------
class Top:
    def __init__(self, name: str, md: float, color: str = "#FF4444"):
        self.name = name
        self.md = float(md)
        self.color = color
    def to_dict(self):
        return {"name": self.name, "md": self.md, "color": self.color}
    @classmethod
    def from_dict(cls, d):
        return cls(d["name"], d["md"], d.get("color", "#FF4444"))

class Zone:
    def __init__(self, top_from: Top, top_to: Top):
        self._top_from = top_from
        self._top_to = top_to
    @property
    def name(self):
        return f"{self._top_from.name} → {self._top_to.name}"
    @property
    def md_from(self):
        return self._top_from.md
    @property
    def md_to(self):
        return self._top_to.md

class TopSet:
    def __init__(self, name: str = "Default", color_manager: TopColorManager = None):
        self.name = name
        self._tops: dict[str, Top] = {}
        self._color_manager = color_manager

    def __contains__(self, name):
        return name in self._tops
    def __getitem__(self, name):
        return self._tops[name]

    @property
    def Tops(self) -> list[Top]:
        return sorted(self._tops.values(), key=lambda t: t.md)

    @property
    def Zones(self) -> list[Zone]:
        s = self.Tops
        return [Zone(s[i], s[i+1]) for i in range(len(s)-1)]

    def addRow(self, name: str, md: float, color: str = None) -> Top:
        if name in self._tops:
            raise ValueError(f"Top '{name}' 已存在")
        if color is None and self._color_manager:
            color = self._color_manager.get_color(name)
        elif color is None:
            color = "#FF4444"
        t = Top(name, md, color)
        self._tops[name] = t
        return t

    def deleteRow(self, name: str):
        del self._tops[name]

    def to_dict(self):
        return {"name": self.name, "tops": [t.to_dict() for t in self.Tops]}

    @classmethod
    def from_dict(cls, d, color_manager=None):
        ts = cls(d["name"], color_manager=color_manager)
        for td in d.get("tops", []):
            name = td["name"]
            md = td["md"]
            if color_manager:
                if name not in color_manager._top_color_map:
                    file_color = td.get("color", "#FF4444")
                    color_manager._top_color_map[name] = file_color
                color = color_manager.get_color(name)
            else:
                color = td.get("color", "#FF4444")
            t = Top(name, md, color)
            ts._tops[name] = t
        return ts

class WellData:
    def __init__(self, name: str = "", color_manager: TopColorManager = None):
        self.name = name
        self.df = None
        self.topset = TopSet(f"{name}_Tops" if name else "Default", color_manager=color_manager)
    @property
    def depth(self) -> np.ndarray:
        if self.df is not None and len(self.df) > 0:
            return self.df.index.values.astype(float)
        return np.array([])

# ---------- Ghost 模块 (未修改) ----------
class GhostObject:
    _MIN_SEG = 0.5
    def __init__(self, raw_depth, raw_value, anchor_data, color=None, opacity=0.65, label="Ghost"):
        self.raw_depth = np.asarray(raw_depth, dtype=float).copy()
        self.raw_value = np.asarray(raw_value, dtype=float).copy()
        self.color = color or _next_ghost_color()
        self.opacity = float(np.clip(opacity, 0., 1.))
        self.label = label
        self.raw_min = np.nanmin(self.raw_value)
        self.raw_max = np.nanmax(self.raw_value)
        self.left_bound = self.raw_min
        self.right_bound = self.raw_max
        d_min = float(self.raw_depth.min())
        d_max = float(self.raw_depth.max())
        anchors_raw = [(float(d), name) for d, name in anchor_data if d_min + self._MIN_SEG < float(d) < d_max - self._MIN_SEG]
        anchors_raw.sort(key=lambda x: x[0])
        self.anchor_depths = [d for d, _ in anchors_raw]
        self.anchor_names = [name for _, name in anchors_raw]
        self.raw_boundaries = [d_min] + self.anchor_depths + [d_max]
        self.display_boundaries = list(self.raw_boundaries)
        self.x_offset = 0.0
    def get_display_data(self):
        y = np.interp(self.raw_depth, self.raw_boundaries, self.display_boundaries)
        t = (self.raw_value - self.raw_min) / (self.raw_max - self.raw_min)
        x = self.left_bound + t * (self.right_bound - self.left_bound)
        return x, y
    def move_all(self, delta):
        self.display_boundaries = [d + delta for d in self.display_boundaries]
    def move_boundary(self, idx, new_dp):
        dp = self.display_boundaries
        mn = self._MIN_SEG
        if idx > 0:
            new_dp = max(new_dp, dp[idx-1] + mn)
        if idx < len(dp)-1:
            new_dp = min(new_dp, dp[idx+1] - mn)
        dp[idx] = new_dp
    @property
    def n_boundaries(self):
        return len(self.raw_boundaries)
    def contains_depth(self, d):
        return self.display_boundaries[0] <= d <= self.display_boundaries[-1]

class GhostView:
    def __init__(self, ghost, plot_item):
        self.ghost = ghost
        self.plot_item = plot_item
        self._curve = None
        self._lines = []
        self._blocking = False
        self._build(plot_item)
    def _build(self, plot_item):
        g, n = self.ghost, self.ghost.n_boundaries
        r, gr, b = g.color
        alpha = int(g.opacity * 255)
        pen = pg.mkPen(QColor(r, gr, b, alpha), width=2.5, style=Qt.PenStyle.DashLine)
        self._curve = pg.PlotDataItem(pen=pen)
        plot_item.addItem(self._curve)
        for i in range(n):
            is_top = (i == 0)
            is_bot = (i == n-1)
            if is_top or is_bot:
                lc, lw, sty = QColor(r, gr, b, 220), 2.0, Qt.PenStyle.SolidLine
                lbl = f"↕ {g.label}" if is_top else "⇕ 拉伸底"
            else:
                lc, lw, sty = QColor(0, 0, 0, 200), 1.2, Qt.PenStyle.DashDotLine
                anchor_idx = i - 1
                if anchor_idx < len(g.anchor_names):
                    lbl = f"⚓ {g.anchor_names[anchor_idx]}"
                else:
                    lbl = "⚓ 锚点"
            line = pg.InfiniteLine(pos=g.display_boundaries[i], angle=0,
                                   pen=pg.mkPen(lc, width=lw, style=sty),
                                   movable=True, label=lbl,
                                   labelOpts={"color": lc, "position": 0.94, "fill": pg.mkBrush(255,255,255,100)})
            line.sigPositionChanged.connect(lambda obj, idx=i: self._on_drag(idx, obj))
            plot_item.addItem(line)
            self._lines.append(line)
        self._left_handle = pg.InfiniteLine(
            pos=self.ghost.left_bound, angle=90,
            pen=pg.mkPen(QColor(0,0,0,0), width=5), movable=True
        )
        self._left_handle.sigPositionChanged.connect(self._on_left_stretch)
        plot_item.addItem(self._left_handle)
        self._right_handle = pg.InfiniteLine(
            pos=self.ghost.right_bound, angle=90,
            pen=pg.mkPen(QColor(0,0,0,0), width=5), movable=True
        )
        self._right_handle.sigPositionChanged.connect(self._on_right_stretch)
        plot_item.addItem(self._right_handle)
        self._refresh()
    def _on_drag(self, idx, line_obj):
        if self._blocking:
            return
        self._blocking = True
        try:
            new_pos = float(line_obj.value())
            g = self.ghost
            if idx == 0:
                delta = new_pos - g.display_boundaries[0]
                g.move_all(delta)
                for i, ln in enumerate(self._lines):
                    ln.setValue(g.display_boundaries[i])
            else:
                g.move_boundary(idx, new_pos)
                line_obj.setValue(g.display_boundaries[idx])
            self._refresh()
        finally:
            self._blocking = False
    def _on_left_stretch(self, line):
        new_left = line.value()
        if new_left >= self.ghost.right_bound:
            new_left = self.ghost.right_bound - 0.1
            line.setValue(new_left)
        self.ghost.left_bound = new_left
        self._refresh()
    def _on_right_stretch(self, line):
        new_right = line.value()
        if new_right <= self.ghost.left_bound:
            new_right = self.ghost.left_bound + 0.1
            line.setValue(new_right)
        self.ghost.right_bound = new_right
        self._refresh()
    def _refresh(self):
        x, y = self.ghost.get_display_data()
        mask = ~(np.isnan(x) | np.isnan(y))
        if mask.sum() >= 2:
            self._curve.setData(x[mask], y[mask])
        if hasattr(self, '_left_handle'):
            self._left_handle.setValue(self.ghost.left_bound)
        if hasattr(self, '_right_handle'):
            self._right_handle.setValue(self.ghost.right_bound)
    def reattach(self, plot_item):
        self.plot_item = plot_item
        plot_item.addItem(self._curve)
        for ln in self._lines:
            plot_item.addItem(ln)
        self._refresh()
    def remove(self):
        for item in [self._curve] + self._lines + [self._left_handle, self._right_handle]:
            if item is not None:
                try:
                    self.plot_item.removeItem(item)
                except:
                    pass
        self._lines.clear()
        self._curve = None
        self._left_handle = None
        self._right_handle = None

class GhostManager:
    def __init__(self, plot_item):
        self.plot_item = plot_item
        self._entries = []
    def add_ghost(self, ghost_obj):
        view = GhostView(ghost_obj, self.plot_item)
        self._entries.append((ghost_obj, view))
    def remove_ghost(self, ghost_obj):
        for i, (g, v) in enumerate(self._entries):
            if g is ghost_obj:
                v.remove()
                self._entries.pop(i)
                return
    def clear(self):
        for _, v in self._entries:
            v.remove()
        self._entries.clear()
    def reattach(self, plot_item):
        self.plot_item = plot_item
        for _, v in self._entries:
            v.reattach(plot_item)
    def hit_test(self, depth, tol=5.0):
        for g, _ in self._entries:
            if any(abs(dp - depth) < tol for dp in g.display_boundaries):
                return g
            if g.contains_depth(depth):
                return g
        return None

class GhostSelector(QObject):
    selected = pyqtSignal(float, float)
    def __init__(self, plot_widget, plot_item, parent=None):
        super().__init__(parent)
        self._pw, self._pi, self._vb = plot_widget, plot_item, plot_item.getViewBox()
        self.active, self._step, self._d1 = False, 0, None
        self._guide, self._band = None, None
        scene = plot_widget.scene()
        scene.sigMouseClicked.connect(self._on_click)
        self._proxy = pg.SignalProxy(scene.sigMouseMoved, rateLimit=30, slot=self._on_move)
    def activate(self):
        self.active, self._step, self._d1 = True, 0, None
        self._pw.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        self._clear_temp()
    def deactivate(self):
        self.active, self._step, self._d1 = False, 0, None
        self._pw.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self._clear_temp()
    def _clear_temp(self):
        for item in [self._guide, self._band]:
            if item is not None:
                try:
                    self._pi.removeItem(item)
                except:
                    pass
        self._guide, self._band = None, None
    def _on_click(self, event):
        if not self.active or event.button() != Qt.MouseButton.LeftButton:
            return
        if not self._vb.sceneBoundingRect().contains(event.scenePos()):
            return
        depth = float(self._vb.mapSceneToView(event.scenePos()).y())
        if self._step == 0:
            self._d1, self._step = depth, 1
            self._guide = pg.InfiniteLine(pos=depth, angle=0, pen=pg.mkPen('#1565c0', width=1.5, style=Qt.PenStyle.DashLine),
                                          movable=False, label=f" 起点 {depth:.1f}m")
            self._pi.addItem(self._guide)
            event.accept()
        elif self._step == 1:
            d_min, d_max = sorted([self._d1, depth])
            self.deactivate()
            if d_max - d_min >= 1.0:
                self.selected.emit(d_min, d_max)
            event.accept()
    def _on_move(self, args):
        if not self.active or self._step != 1 or self._d1 is None:
            return
        sp = args[0]
        if not self._vb.sceneBoundingRect().contains(sp):
            return
        d2 = float(self._vb.mapSceneToView(sp).y())
        d_min, d_max = sorted([self._d1, d2])
        if self._band is None:
            self._band = pg.LinearRegionItem(values=[d_min, d_max], orientation='horizontal',
                                             brush=pg.mkBrush(21, 101, 192, 35), movable=False)
            self._pi.addItem(self._band)
        else:
            self._band.setRegion([d_min, d_max])

def build_ghost(well_data, curve_name, d_min, d_max):
    if well_data is None or well_data.df is None or curve_name not in well_data.df.columns:
        return None
    depth = well_data.depth
    mask = (depth >= d_min) & (depth <= d_max)
    seg_d = depth[mask]
    if len(seg_d) < 2:
        return None
    seg_v = well_data.df[curve_name].values[mask].astype(float)
    valid = ~np.isnan(seg_v)
    if valid.sum() < 2:
        return None
    anchors = [(t.md, t.name) for t in well_data.topset.Tops if d_min < t.md < d_max]
    return GhostObject(raw_depth=seg_d[valid], raw_value=seg_v[valid], anchor_data=anchors,
                       label=f"{well_data.name}/{curve_name}")

# ---------- 文件 I/O ----------
def read_log_file(filepath: str):
    encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin-1']
    fp = filepath.lower()
    if fp.endswith('.las') and HAS_LASIO:
        for enc in encodings:
            try:
                las = lasio.read(filepath, ignore_header_errors=True, encoding=enc)
                df = las.df()
                df.index.name = 'DEPTH'
                well_name = str(las.well['WELL'].value).strip() if las.well['WELL'].value else Path(filepath).stem
                break
            except:
                continue
    else:
        for enc in encodings:
            try:
                if fp.endswith(('.csv', '.txt')):
                    df = pd.read_csv(filepath, encoding=enc, sep=None, engine='python')
                else:
                    df = pd.read_excel(filepath)
                df, well_name = _normalize_df(df, Path(filepath).stem)
                break
            except:
                continue
    if 'df' not in locals() or df is None or df.empty:
        raise RuntimeError("数据无效或无法解析")
    df.columns = [c.strip().replace('\x00', '').replace('\ufeff', '') for c in df.columns]
    df = df.dropna(axis=1, how='all')
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df, well_name, list(df.columns)

def _normalize_df(df: pd.DataFrame, well_name: str):
    depth_col = next((c for c in df.columns if any(k in c.lower() for k in ['depth', 'dept', 'dep', '深度', 'md', 'tvd'])), None)
    if depth_col:
        df[depth_col] = pd.to_numeric(df[depth_col], errors='coerce')
        df = df.dropna(subset=[depth_col]).sort_values(depth_col).reset_index(drop=True)
        df.index = df[depth_col].values
        df.drop(columns=[depth_col], inplace=True, errors='ignore')
    else:
        df = df.reset_index(drop=True)
    df.index.name = 'DEPTH'
    return df, well_name

# ---------- 多道数据类 ----------
class TrackInfo:
    _PALETTE = ['#1565c0', '#e65100', '#2e7d32', '#6a1b9a',
                '#c62828', '#00838f', '#f9a825', '#4e342e']
    _idx = 1

    def __init__(self, curve_name: str | None, plot_item, is_primary: bool = False):
        self.curve_name = curve_name
        self.plot_item = plot_item
        self.is_primary = is_primary
        if is_primary:
            self.color = '#1565c0'
        else:
            self.color = TrackInfo._PALETTE[TrackInfo._idx % len(TrackInfo._PALETTE)]
            TrackInfo._idx += 1

# ---------- 绘图组件 WellPanel ----------
class WellPanel(QWidget):
    topset_changed = pyqtSignal()
    send_ghost_signal = pyqtSignal(object)
    flatten_requested = pyqtSignal(str)
    dtw_compare_requested = pyqtSignal(object, object)

    def __init__(self, label: str = "井", parent=None):
        super().__init__(parent)
        self.label = label
        self.well: WellData | None = None
        self._current_curve = None
        self._curve_list = []

        self._fill_mode = 'both'
        self._fill_ref_val = None
        self._fill_color_l = QColor(255, 0, 0, 100)
        self._fill_color_r = QColor(255, 200, 60, 90)
        self._fill_ref_line = None
        self._fill_l_item = None
        self._fill_r_item = None

        self._depth_lock_enabled = False
        self._depth_locked_min = None
        self._depth_locked_max = None
        self._value_lock_enabled = False
        self._value_locked_min = None
        self._value_locked_max = None

        self.zone_color_mgr = None
        self.top_color_mgr = None

        # 速度标注相关
        self._velocity_labels: list[pg.TextItem] = []
        self._velocity_track: TrackInfo | None = None
        self._velocity_results: list | None = None
        self._velocity_unit: str | None = None

        self._build_ui()
        self.topset_changed.connect(self._on_topset_changed_internal)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.gw = pg.GraphicsLayoutWidget()
        self.gw.ci.layout.setSpacing(0)
        self.gw.ci.layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.gw, stretch=1)

        self._tracks: list[TrackInfo] = []
        main_pi = self.gw.addPlot(0, 0)
        main_pi.setMinimumWidth(250)
        main_pi.setLabel('left', '深度 (m)')
        main_pi.invertY(True)
        main_pi.showGrid(x=False, y=False, alpha=0.3)
        main_track = TrackInfo(curve_name=None, plot_item=main_pi, is_primary=True)
        self._tracks.append(main_track)

        self.plot_item = main_pi
        self.plot_widget = self.gw

        self.gw.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.gw.customContextMenuRequested.connect(self._on_context_menu)

        self.setAcceptDrops(True)

        # 悬浮标签放在场景级别
        self.hover_label = pg.TextItem("", anchor=(0, 1), color='white',
                                       fill=pg.mkBrush(0, 0, 0, 180), border=pg.mkPen('#D1D5DB'))
        self.hover_label.setZValue(1000)
        self.hover_label.setVisible(False)
        self.gw.scene().addItem(self.hover_label)

        self.gw.scene().sigMouseMoved.connect(self._on_mouse_hover)

        self.ghost_manager = GhostManager(main_pi)
        self.ghost_selector = GhostSelector(self.gw, main_pi, self)
        self.ghost_selector.selected.connect(self._on_ghost_selected)

    @property
    def primary_track(self) -> 'TrackInfo':
        return self._tracks[0]

    @property
    def _main_vb(self):
        return self.primary_track.plot_item.getViewBox()

    def add_track(self, curve_name: str, force_secondary: bool = False) -> bool:
        """添加曲线道，返回是否成功"""
        if not self.well or self.well.df is None:
            return False
        if curve_name not in self.well.df.columns:
            return False
        for t in self._tracks:
            if t.curve_name == curve_name:
                return False

        # 如果主道为空
        if self.primary_track.curve_name is None:
            if force_secondary:
                # 不作为主道，提示用户
                return False
            # 否则自动设为主曲线
            self.primary_track.curve_name = curve_name
            self._redraw_all()
            return True

        # 添加副道
        col = len(self._tracks)
        pi = self.gw.addPlot(0, col)
        pi.setMinimumWidth(60)
        pi.setMaximumWidth(16777215)
        pi.setYLink(self.primary_track.plot_item)
        pi.hideAxis('left')
        pi.showGrid(x=False, y=False, alpha=0.3)
        pi.invertY(True)
        self.gw.ci.layout.setColumnStretchFactor(col, 1)

        track = TrackInfo(curve_name=curve_name, plot_item=pi, is_primary=False)
        self._tracks.append(track)
        self._draw_track(track)
        return True

    def remove_track(self, curve_name: str):
        for i, t in enumerate(self._tracks):
            if t.curve_name == curve_name and not t.is_primary:
                t.plot_item.clear()
                self.gw.removeItem(t.plot_item)
                # 清理关联的速度标注
                if t is self._velocity_track:
                    self._clear_velocity_labels()
                    self._velocity_track = None
                    self._velocity_results = None
                self._tracks.pop(i)
                self.gw.update()
                return

    def _draw_track(self, track: 'TrackInfo'):
        pi = track.plot_item
        pi.clear()
        if not self.well or self.well.df is None:
            return
        if track.curve_name not in self.well.df.columns:
            return

        y = self.well.depth
        x = self.well.df[track.curve_name].values.astype(float)
        mask = ~np.isnan(x)
        xc, yc = x[mask], y[mask]

        self._draw_zones_on(pi)
        if track.is_primary and self._fill_mode != 'none' and len(xc) >= 2:
            self._init_fill(xc, yc)
        pi.addItem(pg.PlotDataItem(xc, yc, pen=pg.mkPen(track.color, width=1.5)))
        pi.setLabel('bottom', f"{self.well.name} - {track.curve_name}")
        self._draw_tops_on(pi)
        if track.is_primary:
            self.ghost_manager.reattach(pi)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasFormat('application/x-curve-name'):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat('application/x-curve-name'):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        mime = event.mimeData()
        if mime.hasFormat('application/x-curve-name'):
            curve_name = bytes(mime.data('application/x-curve-name')).decode('utf-8')
            if not self.well or self.well.df is None:
                self.status_message(f"⚠ 请先加载井数据再添加道")
            elif curve_name not in self.well.df.columns:
                self.status_message(f"⚠ 井 {self.well.name} 中无曲线 {curve_name}")
            elif self.add_track(curve_name):
                self.status_message(f"✅ 已添加道: {curve_name}")
            else:
                self.status_message(f"⚠ 该道已存在: {curve_name}")
            event.acceptProposedAction()
        else:
            event.ignore()

    def status_message(self, text: str):
        win = self.window()
        if hasattr(win, 'statusBar'):
            win.statusBar().showMessage(text, 3000)

    def _on_mouse_hover(self, pos):
        if not self.well or self.well.df is None:
            self.hover_label.setVisible(False)
            return

        # 找到鼠标所在的 track
        active_track = None
        for track in self._tracks:
            vb = track.plot_item.getViewBox()
            if vb and vb.sceneBoundingRect().contains(pos):
                active_track = track
                break

        if active_track is None:
            self.hover_label.setVisible(False)
            return

        # 计算深度
        depth_vb = active_track.plot_item.getViewBox()
        point = depth_vb.mapSceneToView(pos)
        depth = point.y()
        depths = self.well.depth
        if len(depths) == 0:
            self.hover_label.setVisible(False)
            return
        idx = np.argmin(np.abs(depths - depth))
        actual_depth = depths[idx]

        # 获取当前曲线值
        curve_name = active_track.curve_name
        val_str = ""
        if curve_name and curve_name in self.well.df.columns:
            vals = self.well.df[curve_name].values
            # 插值获得鼠标所在深度的值
            try:
                val = np.interp(actual_depth, depths, vals)
                if not np.isnan(val):
                    val_str = f"{curve_name}: {val:.2f}"
                else:
                    val_str = f"{curve_name}: ---"
            except:
                val_str = f"{curve_name}: ---"

        # Zone 厚度信息
        zone_thickness = None
        for zone in self.well.topset.Zones:
            if zone.md_from <= actual_depth <= zone.md_to:
                zone_thickness = zone.md_to - zone.md_from
                break

        text = f"{actual_depth:.1f} m"
        if val_str:
            text += f"\n{val_str}"
        if zone_thickness is not None:
            text += f"\n厚度: {zone_thickness:.2f} m"

        self.hover_label.setText(text)
        # 设置标签在场景坐标的位置，偏移一点避免遮挡
        self.hover_label.setPos(pos.x() + 15, pos.y() - 15)
        self.hover_label.setVisible(True)

    def set_curve_list(self, curves):
        self._curve_list = curves
        if curves and self._current_curve is None:
            self._current_curve = curves[0]
        self._redraw_all()

    def set_current_curve(self, curve_name):
        if curve_name in self._curve_list:
            for t in list(self._tracks):
                if not t.is_primary and t.curve_name == curve_name:
                    self.remove_track(curve_name)
                    break
            self._current_curve = curve_name
            self._fill_ref_val = None
            self._redraw_all()

    def get_current_curve(self):
        return self._current_curve

    def get_curve_list(self):
        return self._curve_list

    def set_fill_mode(self, mode):
        self._fill_mode = mode
        self._redraw_all()

    def set_fill_color(self, side, color):
        if side == 'left':
            self._fill_color_l = color
        else:
            self._fill_color_r = color
        self._redraw_all()

    def get_fill_color(self, side):
        return self._fill_color_l if side == 'left' else self._fill_color_r

    def apply_depth_range(self, min_d, max_d, lock=False):
        self._main_vb.setYRange(min_d, max_d)
        if lock:
            self._main_vb.setLimits(yMin=min_d, yMax=max_d)
            self._depth_lock_enabled = True
            self._depth_locked_min = min_d
            self._depth_locked_max = max_d
        else:
            self._main_vb.setLimits(yMin=None, yMax=None)
            self._depth_lock_enabled = False

    def apply_value_range(self, min_v, max_v, lock=False):
        self._main_vb.setXRange(min_v, max_v)
        if lock:
            self._main_vb.setLimits(xMin=min_v, xMax=max_v)
            self._value_lock_enabled = True
            self._value_locked_min = min_v
            self._value_locked_max = max_v
        else:
            self._main_vb.setLimits(xMin=None, xMax=None)
            self._value_lock_enabled = False

    def reset_depth_range(self):
        if self.well is None or self.well.df is None:
            return
        dmin, dmax = self.well.depth.min(), self.well.depth.max()
        self._main_vb.setYRange(dmin, dmax)
        if self._depth_lock_enabled:
            self._main_vb.setLimits(yMin=dmin, yMax=dmax)
            self._depth_locked_min = dmin
            self._depth_locked_max = dmax

    def reset_value_range(self):
        if self.well is None or self.well.df is None or not self._current_curve:
            return
        vals = self.well.df[self._current_curve].values
        valid = vals[~np.isnan(vals)]
        if len(valid) == 0:
            return
        vmin, vmax = valid.min(), valid.max()
        self._main_vb.setXRange(vmin, vmax)
        if self._value_lock_enabled:
            self._main_vb.setLimits(xMin=vmin, xMax=vmax)
            self._value_locked_min = vmin
            self._value_locked_max = vmax

    def load_well_data(self, well_data):
        self.well = well_data
        self._fill_ref_val = None
        self._clear_velocity_labels()
        self._velocity_track = None
        self._velocity_results = None
        self._redraw_all()
        self.topset_changed.emit()

    def save_topset(self):
        if not self.well:
            QMessageBox.warning(self, "提示", "请先加载井数据")
            return
        path, _ = QFileDialog.getSaveFileName(self, "保存分层", f"{self.well.name}_tops.json", "JSON (*.json)")
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.well.topset.to_dict(), f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "成功", "分层已保存")

    def load_topset(self):
        if not self.well:
            QMessageBox.warning(self, "提示", "请先加载井数据")
            return
        path, _ = QFileDialog.getOpenFileName(self, "加载分层", "", "JSON (*.json)")
        if path:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.well.topset = TopSet.from_dict(data, color_manager=self.top_color_mgr)
            self._redraw_all()
            self.topset_changed.emit()
            QMessageBox.information(self, "成功", "分层已加载")

    def activate_ghost_selector(self, active):
        if active:
            self.ghost_selector.activate()
        else:
            self.ghost_selector.deactivate()

    def receive_ghost(self, ghost):
        self.ghost_manager.add_ghost(ghost)

    def _redraw_all(self):
        if not self.well or self.well.df is None:
            return
        if self._current_curve is None:
            return
        self.primary_track.curve_name = self._current_curve
        self._fill_ref_val = None
        self._fill_ref_line = None
        self._fill_l_item = None
        self._fill_r_item = None

        for track in self._tracks:
            if track.curve_name and track.curve_name in self.well.df.columns:
                self._draw_track(track)

        # 重新绘制速度标注（如果存在）
        self._redraw_velocity_labels()

        if self._depth_lock_enabled and self._depth_locked_min is not None:
            self.primary_track.plot_item.getViewBox().setLimits(yMin=self._depth_locked_min, yMax=self._depth_locked_max)
        if self._value_lock_enabled and self._value_locked_min is not None:
            self.primary_track.plot_item.getViewBox().setLimits(xMin=self._value_locked_min, xMax=self._value_locked_max)

    def _draw_zones_on(self, pi):
        for z in self.well.topset.Zones:
            if self.zone_color_mgr is not None:
                color = self.zone_color_mgr.get_color(z.name)
            else:
                idx = self.well.topset.Zones.index(z)
                color = ZONE_COLORS[idx % len(ZONE_COLORS)]
            pi.addItem(pg.LinearRegionItem(
                values=[z.md_from, z.md_to], orientation='horizontal',
                brush=pg.mkBrush(*color), movable=False
            ))

    def _draw_tops_on(self, pi):
        for t in self.well.topset.Tops:
            line = TopLine(
                pos=t.md, angle=0,
                pen=pg.mkPen(t.color, width=2.5, style=Qt.PenStyle.DashLine),
                label=f"{t.name} ({t.md:.1f}m)",
                labelOpts={'color': '#000000', 'fill': pg.mkBrush(255,255,255,200),
                           'position': 0.85, 'movable': True},
                movable=True
            )
            line.sigPositionChanged.connect(lambda obj, top=t: setattr(top, 'md', float(obj.value())))
            line.sigPositionChangeFinished.connect(lambda: self._redraw_all())
            line.sigDoubleClicked.connect(lambda obj, name=t.name: self.flatten_requested.emit(name))
            pi.addItem(line)

    def _init_fill(self, xc, yc):
        if self._fill_ref_val is None:
            self._fill_ref_val = float(np.nanpercentile(xc, 25))
        ref = self._fill_ref_val
        pi = self.primary_track.plot_item

        if self._fill_mode in ('left', 'both'):
            self._fill_l_item = QGraphicsPathItem()
            self._fill_l_item.setBrush(pg.mkBrush(self._fill_color_l))
            self._fill_l_item.setPen(pg.mkPen(None))
            pi.addItem(self._fill_l_item)

        if self._fill_mode in ('right', 'both'):
            self._fill_r_item = QGraphicsPathItem()
            self._fill_r_item.setBrush(pg.mkBrush(self._fill_color_r))
            self._fill_r_item.setPen(pg.mkPen(None))
            pi.addItem(self._fill_r_item)

        self._fill_ref_line = pg.InfiniteLine(
            pos=ref, angle=90, pen=pg.mkPen(QColor(84,110,122,180), width=1.2, style=Qt.PenStyle.DashLine),
            movable=True, label=f"阈值={ref:.1f}"
        )
        self._fill_ref_line.sigPositionChanged.connect(lambda obj: self._on_fill_ref_drag(obj))
        pi.addItem(self._fill_ref_line)

        self._update_fill_paths(xc, yc, ref)

    def _create_fill_path(self, x_arr, y_arr, ref_val):
        px = np.concatenate([x_arr, [ref_val, ref_val]])
        py = np.concatenate([y_arr, [y_arr[-1], y_arr[0]]])
        return pg.arrayToQPath(px, py, connect='all')

    def _update_fill_paths(self, xc, yc, ref):
        if self._fill_l_item:
            xl = np.minimum(xc, ref)
            self._fill_l_item.setPath(self._create_fill_path(xl, yc, ref))
        if self._fill_r_item:
            xr = np.maximum(xc, ref)
            self._fill_r_item.setPath(self._create_fill_path(xr, yc, ref))

    def _on_fill_ref_drag(self, line_obj):
        if not self.well or self.well.df is None:
            return
        ref = float(line_obj.value())
        self._fill_ref_val = ref
        if not self._current_curve or self._current_curve not in self.well.df.columns:
            return
        x = self.well.df[self._current_curve].values.astype(float)
        y = self.well.depth
        mask = ~np.isnan(x)
        xc, yc = x[mask], y[mask]
        self._update_fill_paths(xc, yc, ref)
        try:
            line_obj.label.setFormat(f"阈值={ref:.1f}")
        except:
            pass

    def _on_ghost_selected(self, d_min, d_max):
        if not self.well:
            return
        ghost = build_ghost(self.well, self._current_curve, d_min, d_max)
        if ghost:
            self.send_ghost_signal.emit(ghost)
        else:
            QMessageBox.information(self, "提示", "有效数据不足")

    def _get_zone_at_depth(self, depth):
        if not self.well:
            return None
        for zone in self.well.topset.Zones:
            if zone.md_from <= depth <= zone.md_to:
                return zone
        return None

    # ---------- 速度标注 ----------
    def _clear_velocity_labels(self):
        for label in self._velocity_labels:
            if label is not None:
                try:
                    # 从所在的 plot_item 移除
                    if self._velocity_track:
                        self._velocity_track.plot_item.removeItem(label)
                except:
                    pass
        self._velocity_labels.clear()

    def _redraw_velocity_labels(self):
        if self._velocity_track and self._velocity_results and self._velocity_unit:
            self._annotate_velocity_zones(self._velocity_results, self._velocity_unit)

    def _annotate_velocity_zones(self, results, vel_unit):
        """在速度道上绘制 Zone 标注"""
        # 查找速度曲线所在的 track
        track = None
        # 尝试从现有 tracks 中找到匹配的 track
        for t in self._tracks:
            if t.curve_name and t.curve_name in self.well.df.columns:
                # 检查是否是速度阶梯曲线列名（例如 Vavg_...）
                if t.curve_name.startswith("Vavg_"):
                    track = t
                    break
        if not track:
            # 没有找到速度道，不标注
            return

        self._clear_velocity_labels()
        self._velocity_track = track
        self._velocity_results = results
        self._velocity_unit = vel_unit

        pi = track.plot_item
        vb = pi.getViewBox()
        # 获取当前视图的 X 范围，用于确定偏移量
        if vb is None:
            return
        x_range = vb.viewRange()[0]
        x_span = x_range[1] - x_range[0] if x_range[1] > x_range[0] else 1.0
        offset = max(x_span * 0.02, 50)  # 偏移量

        for r in results:
            # 找到对应的 Zone 对象
            zone_name = r['zone']
            zone_obj = None
            for z in self.well.topset.Zones:
                if z.name == zone_name:
                    zone_obj = z
                    break
            if not zone_obj:
                continue
            y_mid = (zone_obj.md_from + zone_obj.md_to) / 2.0
            v = r['velocity']
            # 文本内容
            thick = r['thickness_m']
            twt_ms = r['twt_s'] * 1000.0
            txt = f"{thick:.1f}m | {v:.0f} {vel_unit} | {twt_ms:.1f}ms"
            label = pg.TextItem(txt, anchor=(0, 0.5), color='white',
                                fill=pg.mkBrush(0, 0, 0, 150), border=pg.mkPen('#FFFFFF'))
            label.setPos(v + offset, y_mid)
            pi.addItem(label)
            self._velocity_labels.append(label)

    def _on_topset_changed_internal(self):
        """当分层变化时重绘速度标注"""
        if self._velocity_track and self._velocity_results and self._velocity_unit:
            self._annotate_velocity_zones(self._velocity_results, self._velocity_unit)

    def _on_context_menu(self, pos):
        if not self.well:
            return
        vb = self._main_vb
        scene_pos = self.gw.mapToScene(pos)
        if not vb.sceneBoundingRect().contains(scene_pos):
            return
        click_depth = vb.mapSceneToView(scene_pos).y()

        menu = QMenu()
        hit_ghost = self.ghost_manager.hit_test(click_depth)
        if hit_ghost:
            act_del = menu.addAction(f"❌ 删除 Ghost: {hit_ghost.label}")
            act_del.triggered.connect(lambda: self.ghost_manager.remove_ghost(hit_ghost))
            menu.addSeparator()

        act_ghost = menu.addAction("👻 Ghost 选段")
        act_ghost.setCheckable(True)
        act_ghost.setChecked(self.ghost_selector.active)
        act_ghost.toggled.connect(lambda checked: self.activate_ghost_selector(checked))
        menu.addSeparator()

        hit_zone = self._get_zone_at_depth(click_depth)
        if hit_zone:
            act_dtw = menu.addAction(f"📊 DTW 对比该 Zone: {hit_zone.name}")
            act_dtw.triggered.connect(lambda: self.dtw_compare_requested.emit(hit_zone, self))
            menu.addSeparator()

        hit_top = None
        for t in self.well.topset.Tops:
            if abs(t.md - click_depth) < 5.0:
                hit_top = t
                break

        if len(self._tracks) > 1:
            track_menu = menu.addMenu("📊 道管理")
            for i, track in enumerate(self._tracks):
                if track.is_primary:
                    track_menu.addAction(f"主道: {track.curve_name or '未设置'}")
                else:
                    tm = track_menu.addMenu(f"{track.curve_name}")
                    act_up = tm.addAction("⬆ 上移")
                    act_up.setEnabled(i > 1)
                    act_up.triggered.connect(lambda checked, idx=i: self._move_track(idx, -1))
                    act_dn = tm.addAction("⬇ 下移")
                    act_dn.setEnabled(i < len(self._tracks) - 1)
                    act_dn.triggered.connect(lambda checked, idx=i: self._move_track(idx, 1))
                    tm.addSeparator()
                    act_rm = tm.addAction("🗑 移除")
                    act_rm.triggered.connect(lambda checked, cn=track.curve_name: self._remove_track_menu(cn))
            menu.addSeparator()

        if hit_top:
            act_rename = menu.addAction(f"✏️ 重命名层位: {hit_top.name}")
            act_del_t = menu.addAction(f"🗑️ 删除层位: {hit_top.name}")
            act_rename.triggered.connect(lambda: self._rename_top(hit_top))
            act_del_t.triggered.connect(lambda: self._delete_top(hit_top))
            menu.addSeparator()
            act_flatten = menu.addAction(f"📐 层拉平（居中到该层）: {hit_top.name}")
            act_flatten.triggered.connect(lambda: self.flatten_requested.emit(hit_top.name))
        else:
            act_add = menu.addAction(f"➕ 在 {click_depth:.1f}m 处添加新 Top")
            act_add.triggered.connect(lambda: self._add_top(click_depth))

        menu.exec(self.gw.mapToGlobal(pos))

    def _add_top(self, depth):
        name, ok = QInputDialog.getText(self, "添加层位", "请输入层位名称:")
        if ok and name:
            try:
                self.well.topset.addRow(name, depth)
                self._redraw_all()
                self.topset_changed.emit()
            except Exception as e:
                QMessageBox.warning(self, "错误", f"层位名冲突或无效: {e}")

    def _remove_track_menu(self, curve_name: str):
        self.remove_track(curve_name)
        self.status_message(f"已移除道: {curve_name}")

    def _move_track(self, idx: int, direction: int):
        new_idx = idx + direction
        if new_idx < 1 or new_idx >= len(self._tracks):
            return
        self._tracks[idx], self._tracks[new_idx] = self._tracks[new_idx], self._tracks[idx]
        self._rebuild_layout()
        self.status_message(f"道顺序已调整")

    def _rebuild_layout(self):
        self.gw.clear()
        self.gw.ci.layout.setSpacing(0)
        self.gw.ci.layout.setContentsMargins(0, 0, 0, 0)
        for col, track in enumerate(self._tracks):
            pi = self.gw.addPlot(0, col)
            pi.setMinimumWidth(60)

            if col == 0:
                pi.setLabel('left', '深度 (m)')
            else:
                pi.setYLink(self._tracks[0].plot_item)
                pi.hideAxis('left')
            pi.invertY(True)
            pi.showGrid(x=False, y=False, alpha=0.3)
            self.gw.ci.layout.setColumnStretchFactor(col, 1)
            track.plot_item = pi
            if track.curve_name and self.well and track.curve_name in self.well.df.columns:
                self._draw_track(track)
        self.ghost_manager.reattach(self._tracks[0].plot_item)

        # 重新绘制速度标注
        self._redraw_velocity_labels()

    def _delete_top(self, top):
        self.well.topset.deleteRow(top.name)
        self._redraw_all()
        self.topset_changed.emit()

    def _rename_top(self, top):
        new_name, ok = QInputDialog.getText(self, "重命名", "输入新名称:", text=top.name)
        if ok and new_name and new_name != top.name:
            md = top.md
            old_color = top.color
            self.well.topset.deleteRow(top.name)
            if self.top_color_mgr:
                self.top_color_mgr.remove(top.name)
                if new_name not in self.top_color_mgr._top_color_map:
                    self.top_color_mgr._top_color_map[new_name] = old_color
            self.well.topset.addRow(new_name, md)
            self._redraw_all()
            self.topset_changed.emit()

# ---------- 可拖拽曲线的树控件 ----------
class CurveDragTreeWidget(QTreeWidget):
    def startDrag(self, supportedActions):
        item = self.currentItem()
        if not item:
            return
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or data.get('type') != 'curve':
            return
        curve_name = data.get('curve', '')
        slot = data.get('slot', '')
        mime_data = QMimeData()
        mime_data.setData('application/x-curve-name', curve_name.encode('utf-8'))
        mime_data.setData('application/x-curve-slot', slot.encode('utf-8'))
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        lbl = QLabel(f"  {curve_name}  ")
        lbl.setStyleSheet(
            "background:#3B82F6; color:white; border-radius:4px; "
            "padding:4px 8px; font-size:12px; font-weight:bold;")
        lbl.adjustSize()
        pm = lbl.grab()
        drag.setPixmap(pm)
        drag.exec(Qt.DropAction.CopyAction)

# ---------- StarSteer 风格树形侧边栏 ----------
class WellTreePanel(QWidget):
    file_dropped        = pyqtSignal(str, str)
    curve_selected      = pyqtSignal(str, str)
    load_requested      = pyqtSignal(str)
    topset_action       = pyqtSignal(str, str)
    batch_tops_requested = pyqtSignal(str, str)

    SLOT_COLORS = {
        'A': '#3B82F6',
        'B': '#A855F7',
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setStyleSheet("background: #1A2235;")
        self.setAcceptDrops(True)
        self.setFixedWidth(260)

        self._slot_well_items = {}
        self._slot_log_items  = {}
        self._slot_top_items  = {}
        self._well_names      = {}

        self._build_ui()

    def _build_ui(self):
        root_lay = QVBoxLayout(self)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        hdr = QWidget()
        hdr.setObjectName("sidebarHeader")
        hdr.setFixedHeight(60)
        hdr_lay = QVBoxLayout(hdr)
        hdr_lay.setContentsMargins(14, 10, 14, 10)
        hdr_lay.setSpacing(2)
        t1 = QLabel("WellCorrelator")
        t1.setObjectName("appTitle")
        t2 = QLabel("v6.8  ·  StarSteer Style")
        t2.setObjectName("appSubtitle")
        hdr_lay.addWidget(t1)
        hdr_lay.addWidget(t2)
        root_lay.addWidget(hdr)

        self._drop_hint = QLabel("  ⬇  拖入 LAS / CSV / XLSX 文件导入")
        self._drop_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._drop_hint.setStyleSheet(
            "background:#0F172A; color:#475569; font-size:10px; "
            "font-family:'Segoe UI',Arial; padding:5px 0; "
            "border-bottom:1px solid #1E293B;")
        root_lay.addWidget(self._drop_hint)

        self.tree = CurveDragTreeWidget()
        self.tree.setStyleSheet(TREE_QSS)
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(16)
        self.tree.setAnimated(True)
        self.tree.setExpandsOnDoubleClick(False)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree.setDragEnabled(True)
        self.tree.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)
        self.tree.itemDoubleClicked.connect(self._on_double_click)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)
        root_lay.addWidget(self.tree, stretch=1)

        bar = QWidget()
        bar.setStyleSheet("background:#0F172A; border-top:1px solid #1E293B;")
        bar_lay = QHBoxLayout(bar)
        bar_lay.setContentsMargins(6, 5, 6, 5)
        bar_lay.setSpacing(4)
        for slot, label, color in [('A', '＋ 加载 A', '#1D4ED8'), ('B', '＋ 加载 B', '#7E22CE')]:
            btn = QPushButton(label)
            btn.setStyleSheet(
                f"background:{color}; color:white; border:none; border-radius:4px; "
                f"padding:5px 4px; font-size:11px; font-weight:700;")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, s=slot: self.load_requested.emit(s))
            bar_lay.addWidget(btn)
        root_lay.addWidget(bar)

        sig = QLabel("by  m Y k")
        sig.setObjectName("signature")
        sig.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root_lay.addWidget(sig)

        self._build_tree_skeleton()

    def _build_tree_skeleton(self):
        self.tree.clear()
        self._slot_well_items.clear()
        self._slot_log_items.clear()
        self._slot_top_items.clear()

        root = QTreeWidgetItem(self.tree, ["▾  Wells"])
        root.setExpanded(True)
        root.setForeground(0, QColor("#475569"))
        fnt = QFont("Segoe UI", 9, QFont.Weight.Bold)
        root.setFont(0, fnt)
        root.setFlags(root.flags() & ~Qt.ItemFlag.ItemIsSelectable)
        self._root_item = root

        for slot in ('A', 'B'):
            self._add_well_placeholder(slot)

    def _add_well_placeholder(self, slot):
        color = self.SLOT_COLORS[slot]
        well_item = QTreeWidgetItem(self._root_item)
        well_item.setText(0, f"  📋  未加载  [{slot}]")
        well_item.setForeground(0, QColor("#475569"))
        well_item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'well_placeholder', 'slot': slot})
        fnt = QFont("Segoe UI", 10, QFont.Weight.Bold)
        well_item.setFont(0, fnt)
        well_item.setExpanded(False)
        self._slot_well_items[slot] = well_item
        return well_item

    def update_well(self, slot: str, well_data, curves: list):
        well_item = self._slot_well_items.get(slot)
        if not well_item:
            return

        color = self.SLOT_COLORS[slot]
        icon = "🔵" if slot == 'A' else "🟣"
        well_item.setText(0, f"  {icon}  {well_data.name}")
        well_item.setForeground(0, QColor(color))
        well_item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'well', 'slot': slot})
        self._well_names[slot] = well_data.name

        while well_item.childCount():
            well_item.removeChild(well_item.child(0))

        logs_item = QTreeWidgetItem(well_item, ["  ▾  📊  Logs"])
        logs_item.setForeground(0, QColor("#64748B"))
        logs_item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'logs_folder', 'slot': slot})
        logs_item.setExpanded(True)
        self._slot_log_items[slot] = logs_item

        for curve in curves:
            ci = QTreeWidgetItem(logs_item)
            ci.setText(0, f"       {curve}")
            ci.setForeground(0, QColor("#94A3B8"))
            ci.setData(0, Qt.ItemDataRole.UserRole, {'type': 'curve', 'slot': slot, 'curve': curve})

        tops_item = QTreeWidgetItem(well_item, [f"  ▾  📌  {well_data.topset.name}"])
        tops_item.setForeground(0, QColor("#64748B"))
        tops_item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'topset_folder', 'slot': slot})
        tops_item.setExpanded(True)
        self._slot_top_items[slot] = tops_item

        self._refresh_tops(slot, well_data)
        well_item.setExpanded(True)

    def refresh_tops(self, slot: str, well_data):
        self._refresh_tops(slot, well_data)

    def _refresh_tops(self, slot: str, well_data):
        tops_item = self._slot_top_items.get(slot)
        if not tops_item:
            return
        while tops_item.childCount():
            tops_item.removeChild(tops_item.child(0))
        for top in well_data.topset.Tops:
            ti = QTreeWidgetItem(tops_item)
            ti.setText(0, f"       {top.name}  ({top.md:.1f}m)")
            ti.setForeground(0, QColor(top.color))
            ti.setData(0, Qt.ItemDataRole.UserRole, {'type': 'top', 'slot': slot, 'top_name': top.name})

    def _on_double_click(self, item: QTreeWidgetItem, col: int):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
        t = data.get('type')
        if t == 'well_placeholder':
            self.load_requested.emit(data['slot'])
        elif t == 'curve':
            self.curve_selected.emit(data['slot'], data['curve'])
            self._mark_active_curve(data['slot'], data['curve'])

    def _mark_active_curve(self, slot: str, curve: str):
        logs_item = self._slot_log_items.get(slot)
        if not logs_item:
            return
        for i in range(logs_item.childCount()):
            ci = logs_item.child(i)
            d = ci.data(0, Qt.ItemDataRole.UserRole)
            if d and d.get('curve') == curve:
                ci.setForeground(0, QColor("#FACC15"))
                fnt = QFont("Segoe UI", 10, QFont.Weight.Bold)
                ci.setFont(0, fnt)
            else:
                ci.setForeground(0, QColor("#CBD5E1"))
                ci.setFont(0, QFont("Segoe UI", 10))

    def _on_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item:
            return
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
        t = data.get('type')
        slot = data.get('slot')
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu{background:#1E293B;color:#E2E8F0;border:1px solid #334155;font-size:11px;}"
            "QMenu::item:selected{background:#3B82F6;}")

        if t in ('well', 'well_placeholder'):
            a = menu.addAction(f"📂  加载文件到槽 {slot}")
            a.triggered.connect(lambda: self.load_requested.emit(slot))

        if t in ('well', 'logs_folder', 'topset_folder', 'curve', 'top'):
            menu.addSeparator()
            a2 = menu.addAction("💾  保存分层")
            a2.triggered.connect(lambda: self.topset_action.emit(slot, 'save'))
            a3 = menu.addAction("📥  加载分层")
            a3.triggered.connect(lambda: self.topset_action.emit(slot, 'load'))

        if t == 'top':
            menu.addSeparator()
            top_name = data.get('top_name', '')
            a4 = menu.addAction(f"📐  拉平到  {top_name}")
            a4.triggered.connect(lambda: self._emit_flatten(slot, top_name))

        menu.exec(self.tree.viewport().mapToGlobal(pos))

    def _emit_flatten(self, slot, top_name):
        self.curve_selected.emit(slot, f'__flatten__:{top_name}')

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            valid = any(u.toLocalFile().lower().endswith(('.las', '.csv', '.xlsx', '.xls'))
                        for u in urls)
            if valid:
                self._drop_hint.setStyleSheet(
                    "background:#1D4ED8; color:white; font-size:11px; font-weight:700; "
                    "font-family:'Segoe UI',Arial; padding:6px 0; "
                    "border-bottom:1px solid #3B82F6;")
                self._drop_hint.setText("  ⬇  释放到此处导入")
                event.acceptProposedAction()
                return
        event.ignore()

    def dragLeaveEvent(self, event):
        self._reset_drop_hint()

    def dropEvent(self, event: QDropEvent):
        self._reset_drop_hint()
        urls = event.mimeData().urls()
        files = [u.toLocalFile() for u in urls
                 if u.toLocalFile().lower().endswith(('.las', '.csv', '.xlsx', '.xls'))]
        if not files:
            event.ignore()
            return

        occupied = {s for s, wi in self._slot_well_items.items()
                    if wi.data(0, Qt.ItemDataRole.UserRole) and
                    wi.data(0, Qt.ItemDataRole.UserRole).get('type') == 'well'}

        slots_order = ['A', 'B']
        for filepath in files:
            slot = None
            for s in slots_order:
                if s not in occupied:
                    slot = s
                    occupied.add(s)
                    break
            if slot is None:
                dlg = QMenu(self)
                dlg.setStyleSheet(
                    "QMenu{background:#1E293B;color:#E2E8F0;border:1px solid #334155;font-size:12px;}"
                    "QMenu::item:selected{background:#3B82F6;}")
                dlg.addSection(f"导入: {Path(filepath).name}")
                aA = dlg.addAction("→ 覆盖槽 A")
                aB = dlg.addAction("→ 覆盖槽 B")
                chosen = dlg.exec(self.mapToGlobal(self.rect().center()))
                if chosen == aA:
                    slot = 'A'
                elif chosen == aB:
                    slot = 'B'
                else:
                    continue
            self.file_dropped.emit(slot, filepath)

        event.acceptProposedAction()

    def _reset_drop_hint(self):
        self._drop_hint.setStyleSheet(
            "background:#0F172A; color:#475569; font-size:10px; "
            "font-family:'Segoe UI',Arial; padding:5px 0; "
            "border-bottom:1px solid #1E293B;")
        self._drop_hint.setText("  ⬇  拖入 LAS / CSV / XLSX 文件导入")

# ---------- 联井覆盖层 ----------
class CorrelationOverlay(QWidget):
    def __init__(self, panel_left, panel_right, parent=None):
        super().__init__(parent)
        self.panel_left, self.panel_right = panel_left, panel_right
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def paintEvent(self, event):
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            lw, rw = self.panel_left.well, self.panel_right.well
            if not lw or not rw:
                painter.end()
                return
            common = sorted({t.name for t in lw.topset.Tops} & {t.name for t in rw.topset.Tops})
            if not common:
                painter.end()
                return
            lvb = self.panel_left.primary_track.plot_item.getViewBox()
            rvb = self.panel_right.primary_track.plot_item.getViewBox()
            lp_gw, rp_gw = self.panel_left.gw, self.panel_right.gw
            w = self.width()
            pen = QPen(QColor(100,100,100,140), 1.2)
            pen.setStyle(Qt.PenStyle.DashLine)
            for name in common:
                lsc = lvb.mapViewToScene(pg.Point(0, lw.topset[name].md))
                rsc = rvb.mapViewToScene(pg.Point(0, rw.topset[name].md))
                lpos = self.mapFromGlobal(lp_gw.mapToGlobal(lsc.toPoint()))
                rpos = self.mapFromGlobal(rp_gw.mapToGlobal(rsc.toPoint()))
                painter.setPen(pen)
                painter.drawLine(0, int(lpos.y()), w, int(rpos.y()))
            painter.end()
        except:
            pass

# ---------- 主窗口 ----------
class MainWindow(QMainWindow):
    def _make_section_header(self, container_id, label_id, icon_text, title_text):
        w = QWidget()
        w.setObjectName(container_id)
        w.setFixedHeight(34)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(12, 0, 12, 0)
        lay.setSpacing(8)
        icon = QLabel(icon_text)
        icon.setObjectName(label_id)
        icon.setFixedWidth(20)
        icon.setStyleSheet("font-size: 14px; font-weight: bold;")
        lbl = QLabel(title_text)
        lbl.setObjectName(label_id)
        lay.addWidget(icon)
        lay.addWidget(lbl)
        lay.addStretch()
        return w

    def _make_sub_label(self, text):
        lbl = QLabel(text)
        lbl.setObjectName("subLabel")
        return lbl

    def _make_divider(self):
        line = QFrame()
        line.setObjectName("divider")
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFixedHeight(1)
        return line

    def _build_well_controls(self, letter, group_color):
        refs = {}
        container = QWidget()
        container.setObjectName(f"wellGroup_{letter}")
        lay = QVBoxLayout(container)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(6)

        lbl_name = QLabel("  未加载")
        lbl_name.setObjectName(f"wellNameLabel_{letter}")
        lay.addWidget(lbl_name)
        refs['lbl_name'] = lbl_name

        btn_id = f"loadBtn_{letter}"
        btn_load = QPushButton("+ 加载测井文件")
        btn_load.setObjectName(btn_id)
        lay.addWidget(btn_load)
        refs['btn_load'] = btn_load

        row_curve = QHBoxLayout()
        row_curve.setSpacing(6)
        lbl_c = QLabel("曲线")
        lbl_c.setFixedWidth(30)
        cmb_curve = QComboBox()
        row_curve.addWidget(lbl_c)
        row_curve.addWidget(cmb_curve, stretch=1)
        lay.addLayout(row_curve)
        refs['cmb_curve'] = cmb_curve

        row_sl = QHBoxLayout()
        row_sl.setSpacing(6)
        btn_save = QPushButton("保存分层")
        btn_load_ts = QPushButton("加载分层")
        row_sl.addWidget(btn_save)
        row_sl.addWidget(btn_load_ts)
        lay.addLayout(row_sl)
        refs['btn_save'] = btn_save
        refs['btn_load_ts'] = btn_load_ts

        row_fill = QHBoxLayout()
        row_fill.setSpacing(6)
        lbl_f = QLabel("充填")
        lbl_f.setFixedWidth(30)
        cmb_fill = QComboBox()
        cmb_fill.addItems(["无", "左充填", "右充填", "双向"])
        cmb_fill.setCurrentText("双向")
        row_fill.addWidget(lbl_f)
        row_fill.addWidget(cmb_fill, stretch=1)
        lay.addLayout(row_fill)
        refs['cmb_fill'] = cmb_fill

        row_color = QHBoxLayout()
        row_color.setSpacing(6)
        btn_fill_l = QPushButton("左色")
        btn_fill_r = QPushButton("右色")
        btn_fill_l.setObjectName("fillBtnLeft")
        btn_fill_r.setObjectName("fillBtnRight")
        row_color.addWidget(btn_fill_l)
        row_color.addWidget(btn_fill_r)
        lay.addLayout(row_color)
        refs['btn_fill_l'] = btn_fill_l
        refs['btn_fill_r'] = btn_fill_r

        btn_ghost = QPushButton("GHOST 选段")
        btn_ghost.setObjectName("ghostBtn")
        btn_ghost.setCheckable(True)
        lay.addWidget(btn_ghost)
        refs['btn_ghost'] = btn_ghost

        lay.addWidget(self._make_sub_label("深度范围"))
        g_depth = QGridLayout()
        g_depth.setSpacing(4)
        g_depth.setColumnStretch(0, 1)
        g_depth.setColumnStretch(1, 1)
        le_dmin = QLineEdit(); le_dmin.setPlaceholderText("Min")
        le_dmax = QLineEdit(); le_dmax.setPlaceholderText("Max")
        btn_apply_d = QPushButton("应用")
        btn_reset_d = QPushButton("重置")
        cb_lock_d = QCheckBox("锁定")
        g_depth.addWidget(le_dmin,      0, 0)
        g_depth.addWidget(le_dmax,      0, 1)
        g_depth.addWidget(btn_apply_d,  1, 0)
        g_depth.addWidget(btn_reset_d,  1, 1)
        g_depth.addWidget(cb_lock_d,    1, 2)
        lay.addLayout(g_depth)
        refs['le_dmin'] = le_dmin
        refs['le_dmax'] = le_dmax
        refs['btn_apply_d'] = btn_apply_d
        refs['btn_reset_d'] = btn_reset_d
        refs['cb_lock_d'] = cb_lock_d

        lay.addWidget(self._make_sub_label("曲线范围"))
        g_val = QGridLayout()
        g_val.setSpacing(4)
        g_val.setColumnStretch(0, 1)
        g_val.setColumnStretch(1, 1)
        le_vmin = QLineEdit(); le_vmin.setPlaceholderText("Min")
        le_vmax = QLineEdit(); le_vmax.setPlaceholderText("Max")
        btn_apply_v = QPushButton("应用")
        btn_reset_v = QPushButton("重置")
        cb_lock_v = QCheckBox("锁定")
        g_val.addWidget(le_vmin,     0, 0)
        g_val.addWidget(le_vmax,     0, 1)
        g_val.addWidget(btn_apply_v, 1, 0)
        g_val.addWidget(btn_reset_v, 1, 1)
        g_val.addWidget(cb_lock_v,   1, 2)
        lay.addLayout(g_val)
        refs['le_vmin'] = le_vmin
        refs['le_vmax'] = le_vmax
        refs['btn_apply_v'] = btn_apply_v
        refs['btn_reset_v'] = btn_reset_v
        refs['cb_lock_v'] = cb_lock_v

        return container, refs

    def __init__(self):
        super().__init__()
        self.setWindowTitle("WellCorrelator v6.8 · 地层速度计算与标注")
        self.resize(1540, 920)

        self.zone_color_mgr = ZoneColorManager()
        self.top_color_mgr = TopColorManager()

        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.panel_a = WellPanel("参考井 A")
        self.panel_b = WellPanel("目标井 B")
        self.panel_a.zone_color_mgr = self.zone_color_mgr
        self.panel_b.zone_color_mgr = self.zone_color_mgr
        self.panel_a.top_color_mgr = self.top_color_mgr
        self.panel_b.top_color_mgr = self.top_color_mgr

        self.panel_a.send_ghost_signal.connect(self.panel_b.receive_ghost)
        self.panel_b.send_ghost_signal.connect(self.panel_a.receive_ghost)
        self.panel_a.flatten_requested.connect(lambda name: self._flatten(name, self.panel_a, self.panel_b))
        self.panel_b.flatten_requested.connect(lambda name: self._flatten(name, self.panel_a, self.panel_b))
        self.panel_a.dtw_compare_requested.connect(self._dtw_compare_zone)
        self.panel_b.dtw_compare_requested.connect(self._dtw_compare_zone)

        self.corr_overlay = CorrelationOverlay(self.panel_a, self.panel_b)
        right_splitter = QSplitter(Qt.Orientation.Horizontal)
        right_splitter.addWidget(self.panel_a)
        right_splitter.addWidget(self.corr_overlay)
        right_splitter.addWidget(self.panel_b)
        right_splitter.setSizes([650, 50, 650])

        self.tree_panel = WellTreePanel()
        self.tree_panel.file_dropped.connect(self._on_file_dropped)
        self.tree_panel.load_requested.connect(self._on_load_requested)
        self.tree_panel.curve_selected.connect(self._on_curve_selected)
        self.tree_panel.topset_action.connect(self._on_topset_action)

        self.panel_a.topset_changed.connect(lambda: self._refresh_tree_tops('A'))
        self.panel_b.topset_changed.connect(lambda: self._refresh_tree_tops('B'))

        self.toggle_btn = QPushButton("◀")
        self.toggle_btn.setObjectName("toggleBtn")
        self.toggle_btn.setFixedWidth(18)
        self.toggle_btn.clicked.connect(self._toggle_left_panel)

        self._top_bar = self._build_top_bar()
        main_layout.addWidget(self._top_bar)

        main_h = QHBoxLayout()
        main_h.setContentsMargins(0, 0, 0, 0)
        main_h.setSpacing(0)
        main_h.addWidget(self.tree_panel)
        main_h.addWidget(self.toggle_btn)
        main_h.addWidget(right_splitter, stretch=1)
        main_layout.addLayout(main_h, stretch=1)

        self._syncing_scale = False
        self._flatten_active = False
        self._flatten_offset = 0.0
        self._flatten_top_name = None

        def sync_scale(source, target, offset_to_target=0.0):
            if self._syncing_scale:
                return
            y_min, y_max = source._main_vb.viewRange()[1]
            height = y_max - y_min
            center_src = (y_min + y_max) / 2
            if self._flatten_active:
                center_tgt = center_src - offset_to_target
            else:
                y_min_t, y_max_t = target._main_vb.viewRange()[1]
                center_tgt = (y_min_t + y_max_t) / 2
            new_min = center_tgt - height / 2
            new_max = center_tgt + height / 2
            if new_max > new_min:
                self._syncing_scale = True
                target._main_vb.setYRange(new_min, new_max, padding=0.0)
                self._syncing_scale = False

        self.panel_a._main_vb.sigRangeChanged.connect(
            lambda: sync_scale(self.panel_a, self.panel_b, self._flatten_offset))
        self.panel_b._main_vb.sigRangeChanged.connect(
            lambda: sync_scale(self.panel_b, self.panel_a, -self._flatten_offset))

        self.panel_a.topset_changed.connect(self.corr_overlay.update)
        self.panel_b.topset_changed.connect(self.corr_overlay.update)
        self.panel_a._main_vb.sigRangeChanged.connect(self.corr_overlay.update)
        self.panel_b._main_vb.sigRangeChanged.connect(self.corr_overlay.update)

    # ── 顶部工具栏构建 ────────────────────────────────────────────────────
    def _make_top_divider(self):
        f = QFrame()
        f.setObjectName("topDivider")
        f.setFrameShape(QFrame.Shape.VLine)
        f.setFixedWidth(1)
        return f

    def _build_top_bar(self):
        outer = QWidget()
        outer.setObjectName("topBar")
        outer_lay = QVBoxLayout(outer)
        outer_lay.setContentsMargins(0, 0, 0, 0)
        outer_lay.setSpacing(0)

        self._top_bar_toggle = QPushButton("▲  工具栏")
        self._top_bar_toggle.setObjectName("topBarToggle")
        self._top_bar_toggle.setFixedHeight(16)
        self._top_bar_toggle.clicked.connect(self._toggle_top_bar)
        outer_lay.addWidget(self._top_bar_toggle)

        self._top_bar_content = QWidget()
        self._top_bar_content.setObjectName("topBarInner")

        def lbl(text, obj_name=None):
            l = QLabel(text)
            if obj_name:
                l.setObjectName(obj_name)
            return l

        v_layout = QVBoxLayout(self._top_bar_content)
        v_layout.setContentsMargins(8, 6, 8, 6)
        v_layout.setSpacing(4)

        row1 = QHBoxLayout()
        row1.setSpacing(6)

        row2 = QHBoxLayout()
        row2.setSpacing(12)

        # ----- 第一行控件 -----
        row1.addWidget(lbl("A", "wellTag_A"))
        row1.addWidget(self._make_top_divider())

        row1.addWidget(lbl("深度:"))
        self._tb_le_dmin_a = QLineEdit(); self._tb_le_dmin_a.setPlaceholderText("Min")
        self._tb_le_dmax_a = QLineEdit(); self._tb_le_dmax_a.setPlaceholderText("Max")
        row1.addWidget(self._tb_le_dmin_a)
        row1.addWidget(QLabel("–"))
        row1.addWidget(self._tb_le_dmax_a)
        btn_apply_d_a = QPushButton("应用")
        btn_apply_d_a.setFixedWidth(44)
        btn_apply_d_a.clicked.connect(lambda: self._apply_depth(
            self.panel_a, self._tb_le_dmin_a.text(), self._tb_le_dmax_a.text(), False))
        row1.addWidget(btn_apply_d_a)
        row1.addWidget(self._make_top_divider())

        row1.addWidget(lbl("曲线范围:"))
        self._tb_le_vmin_a = QLineEdit(); self._tb_le_vmin_a.setPlaceholderText("Min")
        self._tb_le_vmax_a = QLineEdit(); self._tb_le_vmax_a.setPlaceholderText("Max")
        row1.addWidget(self._tb_le_vmin_a)
        row1.addWidget(QLabel("–"))
        row1.addWidget(self._tb_le_vmax_a)
        btn_apply_v_a = QPushButton("应用")
        btn_apply_v_a.setFixedWidth(44)
        btn_apply_v_a.clicked.connect(lambda: self._apply_value(
            self.panel_a, self._tb_le_vmin_a.text(), self._tb_le_vmax_a.text(), False))
        row1.addWidget(btn_apply_v_a)
        row1.addWidget(self._make_top_divider())

        row1.addWidget(lbl("充填:"))
        self._tb_cmb_fill_a = QComboBox()
        self._tb_cmb_fill_a.addItems(["无", "左充填", "右充填", "双向"])
        self._tb_cmb_fill_a.setCurrentText("双向")
        self._tb_cmb_fill_a.setFixedWidth(72)
        self._tb_cmb_fill_a.currentTextChanged.connect(
            lambda t: self.panel_a.set_fill_mode(
                {'无': 'none', '左充填': 'left', '右充填': 'right', '双向': 'both'}.get(t, 'both')))
        row1.addWidget(self._tb_cmb_fill_a)
        row1.addWidget(self._make_top_divider())

        self._tb_btn_ghost_a = QPushButton("Ghost A")
        self._tb_btn_ghost_a.setObjectName("ghostBtn")
        self._tb_btn_ghost_a.setCheckable(True)
        self._tb_btn_ghost_a.toggled.connect(self.panel_a.activate_ghost_selector)
        row1.addWidget(self._tb_btn_ghost_a)

        row1.addWidget(self._make_top_divider())

        row1.addWidget(lbl("B", "wellTag_B"))
        row1.addWidget(self._make_top_divider())

        row1.addWidget(lbl("曲线范围:"))
        self._tb_le_vmin_b = QLineEdit(); self._tb_le_vmin_b.setPlaceholderText("Min")
        self._tb_le_vmax_b = QLineEdit(); self._tb_le_vmax_b.setPlaceholderText("Max")
        row1.addWidget(self._tb_le_vmin_b)
        row1.addWidget(QLabel("–"))
        row1.addWidget(self._tb_le_vmax_b)
        btn_apply_v_b = QPushButton("应用")
        btn_apply_v_b.setFixedWidth(44)
        btn_apply_v_b.clicked.connect(lambda: self._apply_value(
            self.panel_b, self._tb_le_vmin_b.text(), self._tb_le_vmax_b.text(), False))
        row1.addWidget(btn_apply_v_b)
        row1.addWidget(self._make_top_divider())

        row1.addWidget(lbl("充填:"))
        self._tb_cmb_fill_b = QComboBox()
        self._tb_cmb_fill_b.addItems(["无", "左充填", "右充填", "双向"])
        self._tb_cmb_fill_b.setCurrentText("双向")
        self._tb_cmb_fill_b.setFixedWidth(72)
        self._tb_cmb_fill_b.currentTextChanged.connect(
            lambda t: self.panel_b.set_fill_mode(
                {'无': 'none', '左充填': 'left', '右充填': 'right', '双向': 'both'}.get(t, 'both')))
        row1.addWidget(self._tb_cmb_fill_b)
        row1.addWidget(self._make_top_divider())

        self._tb_btn_ghost_b = QPushButton("Ghost B")
        self._tb_btn_ghost_b.setObjectName("ghostBtn")
        self._tb_btn_ghost_b.setCheckable(True)
        self._tb_btn_ghost_b.toggled.connect(self.panel_b.activate_ghost_selector)
        row1.addWidget(self._tb_btn_ghost_b)

        # ----- 第二行控件 -----
        btn_batch_a = QPushButton("批量分层 A")
        btn_batch_a.clicked.connect(lambda: self._batch_add_tops(slot='A'))
        row2.addWidget(btn_batch_a)

        btn_batch_b = QPushButton("批量分层 B")
        btn_batch_b.clicked.connect(lambda: self._batch_add_tops(slot='B'))
        row2.addWidget(btn_batch_b)

        row2.addWidget(self._make_top_divider())

        self._tb_btn_velocity = QPushButton("📊 地层速度")
        self._tb_btn_velocity.setFixedWidth(100)
        self._tb_btn_velocity.clicked.connect(self._compute_formation_velocity)
        row2.addWidget(self._tb_btn_velocity)

        row2.addWidget(self._make_top_divider())

        btn_save_a = QPushButton("💾  A ")
        btn_save_a.setStyleSheet("padding: 4px 8px;")
        btn_save_a.clicked.connect(lambda: self.panel_a.save_topset())
        btn_load_a = QPushButton("📥  A ")
        btn_load_a.setStyleSheet("padding: 4px 8px;")
        btn_load_a.clicked.connect(lambda: self.panel_a.load_topset())
        
        btn_save_b = QPushButton("💾  B ")
        btn_save_b.setStyleSheet("padding: 4px 8px;")
        btn_save_b.clicked.connect(lambda: self.panel_b.save_topset())
        btn_load_b = QPushButton("📥  B ")
        btn_load_b.setStyleSheet("padding: 4px 8px;")
        btn_load_b.clicked.connect(lambda: self.panel_b.load_topset())
        for b in (btn_save_a, btn_load_a, btn_save_b, btn_load_b):
            b.setFixedWidth(42)
            row2.addWidget(b)

        row2.addStretch()

        v_layout.addLayout(row1)
        v_layout.addLayout(row2)

        outer_lay.addWidget(self._top_bar_content)
        self._top_bar_visible = True
        return outer

    def _toggle_top_bar(self):
        self._top_bar_visible = not self._top_bar_visible
        self._top_bar_content.setVisible(self._top_bar_visible)
        self._top_bar_toggle.setText("▲  工具栏" if self._top_bar_visible else "▼  工具栏")

    # ── 树形面板信号处理 ─────────────────────────────────────────────────
    def _panel_for(self, slot):
        return self.panel_a if slot == 'A' else self.panel_b

    def _on_file_dropped(self, slot: str, filepath: str):
        self._load_well_from_path(slot, filepath)

    def _on_load_requested(self, slot: str):
        path, _ = QFileDialog.getOpenFileName(
            self, f"选择文件 — 槽 {slot}", "",
            "Log Files (*.las *.csv *.xlsx *.xls);;All (*)")
        if path:
            self._load_well_from_path(slot, path)

    def _load_well_from_path(self, slot: str, path: str):
        panel = self._panel_for(slot)
        try:
            df, well_name, cols = read_log_file(path)
            well_data = WellData(well_name, color_manager=self.top_color_mgr)
            well_data.df = df
            panel.load_well_data(well_data)
            if cols:
                panel.set_curve_list(cols)
                default_curve = "GR" if "GR" in cols else cols[0]
                panel.set_current_curve(default_curve)
            dmin, dmax = well_data.depth.min(), well_data.depth.max()
            panel.reset_value_range()
            if slot == 'A':
                self._tb_le_dmin_a.setText(f"{dmin:.2f}")
                self._tb_le_dmax_a.setText(f"{dmax:.2f}")
            self.tree_panel.update_well(slot, well_data, cols)
            self.tree_panel._mark_active_curve(slot, panel.get_current_curve() or '')
            self.statusBar().showMessage(
                f"✅  槽 {slot} 已加载: {well_name}  |  曲线: {', '.join(cols[:6])}{'…' if len(cols)>6 else ''}  "
                f"|  深度: {dmin:.1f}–{dmax:.1f} m", 6000)
        except Exception as e:
            QMessageBox.critical(self, "加载失败", str(e))

    def _on_curve_selected(self, slot: str, value: str):
        if value.startswith('__flatten__:'):
            top_name = value[len('__flatten__:'):]
            self._flatten(top_name, self.panel_a, self.panel_b)
            return
        panel = self._panel_for(slot)
        panel.set_current_curve(value)
        self.tree_panel._mark_active_curve(slot, value)
        self.statusBar().showMessage(f"槽 {slot} 当前曲线: {value}", 3000)

    def _on_topset_action(self, slot: str, action: str):
        panel = self._panel_for(slot)
        if action == 'save':
            panel.save_topset()
        elif action == 'load':
            panel.load_topset()
            if panel.well:
                self._refresh_tree_tops(slot)

    def _refresh_tree_tops(self, slot: str):
        panel = self._panel_for(slot)
        if panel.well:
            self.tree_panel.refresh_tops(slot, panel.well)

    def _toggle_left_panel(self):
        visible = self.tree_panel.isVisible()
        self.tree_panel.setVisible(not visible)
        self.toggle_btn.setText("▶" if visible else "◀")

    def _apply_depth(self, panel, min_str, max_str, lock):
        try:
            panel.apply_depth_range(float(min_str), float(max_str), lock)
        except ValueError:
            QMessageBox.warning(self, "错误", "请输入有效的深度数字")

    def _apply_value(self, panel, min_str, max_str, lock):
        try:
            panel.apply_value_range(float(min_str), float(max_str), lock)
        except ValueError:
            QMessageBox.warning(self, "错误", "请输入有效的曲线值数字")

    def _batch_add_tops(self, slot=None, text=None):
        if slot is None:
            items = []
            if self.panel_a.well: items.append("槽 A")
            if self.panel_b.well: items.append("槽 B")
            if not items:
                QMessageBox.warning(self, "提示", "请先加载井数据")
                return
            chosen, ok = QInputDialog.getItem(self, "选择目标井", "目标:", items, 0, False)
            if not ok:
                return
            slot = 'A' if 'A' in chosen else 'B'

        panel = self._panel_for(slot)
        if panel.well is None:
            QMessageBox.warning(self, "提示", f"槽 {slot} 尚未加载井数据，请先加载。")
            return

        if text is None:
            dlg = QDialog(self)
            dlg.setWindowTitle(f"批量添加分层 — 槽 {slot}")
            dlg.setMinimumWidth(320)
            lay = QVBoxLayout(dlg)
            lbl = QLabel("每行: 层名 深度  (逗号或空格分隔)\n示例:\n  T1  1200.5\n  T2, 1350.0")
            lbl.setStyleSheet("color:#CBD5E1; font-size:11px;")
            te = QTextEdit()
            te.setPlaceholderText("T1 1200.5\nT2, 1350.0")
            te.setFixedHeight(120)
            btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            btns.accepted.connect(dlg.accept)
            btns.rejected.connect(dlg.reject)
            lay.addWidget(lbl)
            lay.addWidget(te)
            lay.addWidget(btns)
            dlg.setStyleSheet("QDialog{background:#1E293B;} QTextEdit{background:#0F172A;color:#E2E8F0;border:1px solid #334155;border-radius:4px;} QLabel{background:transparent;}")
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
            text = te.toPlainText().strip()

        if not text:
            QMessageBox.warning(self, "提示", "请输入层名和深度数据")
            return
        lines = text.splitlines()
        success, errors = 0, []
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            parts = line.split(',', 1) if ',' in line else line.split(None, 1)
            if len(parts) != 2:
                errors.append(f"第{line_num}行格式错误: {line}")
                continue
            name, md_str = parts[0].strip(), parts[1].strip()
            try:
                md = float(md_str)
            except ValueError:
                errors.append(f"第{line_num}行深度无效: {md_str}")
                continue
            try:
                panel.well.topset.addRow(name, md)
                success += 1
            except ValueError as e:
                errors.append(f"第{line_num}行添加失败: {e}")
        if success > 0:
            panel._redraw_all()
            panel.topset_changed.emit()
            QMessageBox.information(self, "完成", f"成功添加 {success} 个分层。")
        if errors:
            QMessageBox.warning(self, "部分失败", "\n".join(errors[:10]))

    def _flatten(self, top_name, panel_a, panel_b):
        if self._flatten_active and self._flatten_top_name == top_name:
            self._flatten_active = False
            self._flatten_offset = 0.0
            self._flatten_top_name = None
            self.statusBar().showMessage(f"✔ 已取消拉平层位 '{top_name}'，恢复独立浏览", 4000)
            return

        if not panel_a.well or not panel_b.well:
            QMessageBox.warning(self, "提示", "请先加载两口井的数据")
            return
        if top_name not in panel_a.well.topset or top_name not in panel_b.well.topset:
            QMessageBox.warning(self, "提示", f"两口井中未同时找到层位 '{top_name}'")
            return

        depth_a = panel_a.well.topset[top_name].md
        depth_b = panel_b.well.topset[top_name].md

        self._flatten_offset = depth_a - depth_b
        self._flatten_active = True
        self._flatten_top_name = top_name

        view_a = panel_a._main_vb
        view_b = panel_b._main_vb
        y_min_a, y_max_a = view_a.viewRange()[1]
        height = y_max_a - y_min_a
        self._syncing_scale = True
        view_a.setYRange(depth_a - height / 4, depth_a + 3*height / 4)
        view_b.setYRange(depth_b - height / 4, depth_b + 3*height / 4)
        self._syncing_scale = False

        self.statusBar().showMessage(
            f"📐 已拉平层位 '{top_name}'  ·  A: {depth_a:.1f}m  B: {depth_b:.1f}m  "
            f"偏移: {self._flatten_offset:+.1f}m  ·  再次双击该层取消拉平", 0)

    # ---------- DTW 对比处理 ----------
    def _dtw_compare_zone(self, source_zone, source_panel):
        if source_panel is self.panel_a:
            source_well = self.panel_a.well
            target_well = self.panel_b.well
            target_panel = self.panel_b
            source_label = "A"
            target_label = "B"
        else:
            source_well = self.panel_b.well
            target_well = self.panel_a.well
            target_panel = self.panel_a
            source_label = "B"
            target_label = "A"

        if not target_well:
            QMessageBox.warning(self, "错误", f"目标井 {target_label} 未加载数据")
            return

        source_curve = source_panel.get_current_curve()
        target_curve = target_panel.get_current_curve()
        if not source_curve or not target_curve:
            QMessageBox.warning(self, "错误", "请先在两口井中选择要对比的曲线")
            return

        depth_src = source_well.depth
        mask_src = (depth_src >= source_zone.md_from) & (depth_src <= source_zone.md_to)
        src_vals = source_well.df[source_curve].values[mask_src]
        src_vals = src_vals[~np.isnan(src_vals)]

        target_zone = None
        for z in target_well.topset.Zones:
            if z.name == source_zone.name:
                target_zone = z
                break

        if not target_zone:
            QMessageBox.warning(self, "提示",
                f"目标井 {target_label} 中不存在同名 Zone '{source_zone.name}'")
            return

        depth_tgt = target_well.depth
        mask_tgt = (depth_tgt >= target_zone.md_from) & (depth_tgt <= target_zone.md_to)
        tgt_vals = target_well.df[target_curve].values[mask_tgt]
        tgt_vals = tgt_vals[~np.isnan(tgt_vals)]

        if len(src_vals) < 3 or len(tgt_vals) < 3:
            QMessageBox.warning(self, "错误", "Zone 内有效数据点不足（至少需要3个点）")
            return

        dist, sim = dtw_distance(src_vals, tgt_vals)

        msg = QMessageBox(self)
        msg.setWindowTitle("DTW Zone 对比结果")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(
            f"<h3>Zone: {source_zone.name}</h3>"
            f"<b>井 A</b> (深度: {source_zone.md_from:.1f}–{source_zone.md_to:.1f} m)<br>"
            f"<b>井 B</b> (深度: {target_zone.md_from:.1f}–{target_zone.md_to:.1f} m)<br><br>"
            f"<b>曲线:</b> {source_curve} (A) / {target_curve} (B)<br>"
            f"<b>有效点数:</b> {len(src_vals)} (A) , {len(tgt_vals)} (B)<br><br>"
            f"<font size='+1'><b>DTW 距离:</b> {dist:.4f}<br>"
            f"<b>相似度:</b> {sim:.2f}%</font>"
        )
        msg.exec()

    # ---------- 地层速度计算入口 ----------
    def _compute_formation_velocity(self):
        items = []
        if self.panel_a.well is not None:
            items.append("A - " + self.panel_a.well.name)
        if self.panel_b.well is not None:
            items.append("B - " + self.panel_b.well.name)
        if not items:
            QMessageBox.warning(self, "提示", "请先加载至少一口井的数据")
            return
        if len(items) == 1:
            slot = 'A' if items[0].startswith('A') else 'B'
        else:
            chosen, ok = QInputDialog.getItem(self, "选择井", "请选择要计算的井:", items, 0, False)
            if not ok:
                return
            slot = 'A' if chosen.startswith('A') else 'B'

        panel = self._panel_for(slot)
        if not panel.well or panel.well.df is None:
            QMessageBox.warning(self, "错误", "井数据无效")
            return

        curves = panel.get_curve_list()
        if not curves:
            QMessageBox.warning(self, "错误", "当前井没有可用的数值曲线")
            return

        default_curve = panel.get_current_curve()
        for c in curves:
            if c.upper() in ('DT', 'AC'):
                default_curve = c
                break

        dlg = VelocityDialog(curves, default_curve, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        params = dlg.get_parameters()
        curve_name = params['curve']
        dt_unit = params['dt_unit']
        output_vel_unit = params['output_vel_unit']
        add_curve = params['add_curve']
        show_labels = params['show_labels']
        gen_inst = params['gen_inst']

        try:
            results = compute_zone_velocities(panel.well, curve_name, dt_unit, output_vel_unit)
        except Exception as e:
            QMessageBox.critical(self, "计算错误", str(e))
            return

        if not results:
            QMessageBox.warning(self, "提示", "没有有效的 Zone 数据（分段内 DT 有效点不足2个）")
            return

        # 显示结果对话框
        result_dlg = VelocityResultDialog(results, panel.well.name, curve_name, self)
        result_dlg.exec()

        # 添加平均速度曲线及标注
        if add_curve:
            self._add_velocity_curve(panel, results, output_vel_unit, show_labels)

        # 生成瞬时速度曲线
        if gen_inst:
            self._add_instant_velocity_curve(panel, curve_name, dt_unit, output_vel_unit)

    def _add_velocity_curve(self, panel, results, vel_unit, show_labels):
        """添加平均速度阶梯曲线，并可选显示 Zone 标注"""
        well = panel.well
        depth = well.depth
        vel_col = np.full_like(depth, np.nan, dtype=float)
        for r in results:
            zone_name = r['zone']
            for zone in well.topset.Zones:
                if zone.name == zone_name:
                    mask = (depth >= zone.md_from) & (depth <= zone.md_to)
                    vel_col[mask] = r['velocity']
                    break
        col_name = f"Vavg_{vel_unit.replace('/','_')}"
        base = col_name
        i = 1
        while col_name in well.df.columns:
            col_name = f"{base}_{i}"
            i += 1
        well.df[col_name] = vel_col
        # 更新曲线列表
        panel.set_curve_list(list(well.df.columns))
        # 刷新树
        self.tree_panel.update_well(
            'A' if panel is self.panel_a else 'B',
            well,
            panel.get_curve_list()
        )
        # 尝试添加为副道 (force_secondary=True)
        if panel.add_track(col_name, force_secondary=False):  # 允许作为主道，若主道为空
            self.statusBar().showMessage(f"✅ 已添加速度曲线: {col_name}", 5000)
        else:
            self.statusBar().showMessage(f"速度曲线 {col_name} 已生成，可手动拖入", 3000)

        # 绘制 Zone 标注
        if show_labels:
            # 查找刚刚添加的或现有的速度 track
            track = None
            for t in panel._tracks:
                if t.curve_name == col_name:
                    track = t
                    break
            if not track:
                # 如果主道被占用，可能是 primary track
                if panel.primary_track.curve_name == col_name:
                    track = panel.primary_track
            if track:
                panel._velocity_track = track
                panel._velocity_results = results
                panel._velocity_unit = vel_unit
                panel._annotate_velocity_zones(results, vel_unit)
            else:
                self.statusBar().showMessage("无法添加标注：未找到速度道", 3000)

    def _add_instant_velocity_curve(self, panel, dt_curve, dt_unit, out_unit):
        """生成瞬时速度曲线并添加为新道"""
        well = panel.well
        dt = well.df[dt_curve].values.astype(float)
        if dt_unit == 'us/ft':
            # us/ft → m/s: V = 1e6 / dt * 0.3048
            vel_inst = 1e6 / dt * 0.3048
        else:
            # us/m → m/s
            vel_inst = 1e6 / dt
        if out_unit == 'km/s':
            vel_inst /= 1000.0
        col_name = f"Vinst_{out_unit.replace('/','_')}"
        base = col_name
        i = 1
        while col_name in well.df.columns:
            col_name = f"{base}_{i}"
            i += 1
        well.df[col_name] = vel_inst
        # 更新面板曲线列表
        panel.set_curve_list(list(well.df.columns))
        # 刷新树
        self.tree_panel.update_well(
            'A' if panel is self.panel_a else 'B',
            well,
            panel.get_curve_list()
        )
        # 添加副道，force_secondary=True 防止在没有主曲线时占据主道
        if panel.add_track(col_name, force_secondary=True):
            self.statusBar().showMessage(f"✅ 已添加瞬时速度曲线: {col_name}", 5000)
        else:
            if panel.primary_track.curve_name is None:
                self.statusBar().showMessage(f"瞬时速度曲线 {col_name} 已生成，但无主曲线，请先选择一条主曲线再手动拖入副道", 6000)
            else:
                self.statusBar().showMessage(f"瞬时速度曲线 {col_name} 已生成，可手动拖入", 4000)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(GLOBAL_QSS)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()