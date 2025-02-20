# SPDX-FileCopyrightText: 2025 Ryo Funai
# SPDX-License-Identifier: Apache-2.0

"""
GUIの構築と更新を行う
"""
from abc import ABC, ABCMeta, abstractmethod
from PyQt5 import QtWidgets, QtCore
from pyvistaqt import QtInteractor
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

class IPointCloudView(ABC):
    @abstractmethod
    def update_spin_value(self, spin: QtWidgets.QDoubleSpinBox, value: float) -> None:
        pass

    @abstractmethod
    def update_slider_value(self, slider: QtWidgets.QSlider, value: float) -> None:
        pass

    @abstractmethod
    def show_pgm_image(self, pgm_file: str) -> None:
        pass


class MetaQWidgetABC(type(QtWidgets.QMainWindow), ABCMeta):
    pass

class PointCloudView(QtWidgets.QMainWindow, IPointCloudView, metaclass=MetaQWidgetABC):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Map Editor")
        self.slider_multiplier = 1000

        # ユーザ設定の初期値
        self.user_output_filename = "output_map.pgm"
        self.user_resolution = 0.2

        # 描画関連の属性
        self.actor = None
        self.cloud_mesh = None

        # コントロールパネル用ウィジェット
        self.zmin_spin = None
        self.zmin_slider = None
        self.zmax_spin = None
        self.zmax_slider = None
        self.output_file_label = None
        self.resolution_label = None

        # PyVista描画エリアのセットアップ
        self.plotter = QtInteractor(self)
        self.plotter.add_text("Loading point cloud...", position='upper_left', font_size=24)
        self.plotter.show_axes()
        self.setCentralWidget(self.plotter)

        self._setup_control_panel()

    def _setup_control_panel(self) -> None:
        dock = QtWidgets.QDockWidget("", self)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
        control_widget = QtWidgets.QWidget()
        dock.setWidget(control_widget)

        layout = QtWidgets.QVBoxLayout(control_widget)
        sliders_container = QtWidgets.QWidget()
        sliders_layout = QtWidgets.QHBoxLayout(sliders_container)
        sliders_layout.setContentsMargins(0, 0, 0, 0)

        # 仮の初期値（後で更新）
        dummy_min, dummy_max, dummy_val = 0.0, 1.0, 0.0

        # min zグループ
        min_group = QtWidgets.QWidget()
        min_layout = QtWidgets.QVBoxLayout(min_group)
        min_layout.setContentsMargins(0, 0, 0, 0)
        min_label = QtWidgets.QLabel("min z:")
        min_label.setAlignment(QtCore.Qt.AlignCenter)
        min_layout.addWidget(min_label)
        min_control, self.zmin_spin, self.zmin_slider = self._create_slider_control(dummy_min, dummy_max, dummy_val)
        min_layout.addWidget(min_control)
        sliders_layout.addWidget(min_group)

        # max zグループ
        max_group = QtWidgets.QWidget()
        max_layout = QtWidgets.QVBoxLayout(max_group)
        max_layout.setContentsMargins(0, 0, 0, 0)
        max_label = QtWidgets.QLabel("max z:")
        max_label.setAlignment(QtCore.Qt.AlignCenter)
        max_layout.addWidget(max_label)
        max_control, self.zmax_spin, self.zmax_slider = self._create_slider_control(dummy_min, dummy_max, dummy_val)
        max_layout.addWidget(max_control)
        sliders_layout.addWidget(max_group)

        layout.addWidget(sliders_container)

        # ボタン群の作成
        self.reset_button = self._create_button("Reset")
        self.convert_button = self._create_button("Convert to PGM")
        self.set_output_filename_button = self._create_button("Set Output File Name")
        self.set_resolution_button = self._create_button("Set Resolution[m/px]")

        layout.addWidget(self.reset_button)
        layout.addWidget(self.convert_button)
        layout.addWidget(self.set_output_filename_button)
        layout.addWidget(self.set_resolution_button)

        self.output_file_label = QtWidgets.QLabel("Output File Name: " + self.user_output_filename)
        self.resolution_label = QtWidgets.QLabel("Resolution: {:.3f} [m/px]".format(self.user_resolution))
        layout.addWidget(self.output_file_label)
        layout.addWidget(self.resolution_label)
        layout.addStretch()

    def _create_slider_control(self, min_val: float, max_val: float, initial_val: float):
        container = QtWidgets.QWidget()
        v_layout = QtWidgets.QVBoxLayout(container)
        spin = QtWidgets.QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(initial_val)
        spin.setDecimals(3)
        v_layout.addWidget(spin)
        slider = QtWidgets.QSlider(QtCore.Qt.Vertical)
        slider.setMinimum(int(min_val * self.slider_multiplier))
        slider.setMaximum(int(max_val * self.slider_multiplier))
        slider.setValue(int(initial_val * self.slider_multiplier))
        slider.setTickPosition(QtWidgets.QSlider.NoTicks)
        v_layout.addWidget(slider, alignment=QtCore.Qt.AlignHCenter)
        return container, spin, slider

    def _create_button(self, text: str) -> QtWidgets.QPushButton:
        return QtWidgets.QPushButton(text)

    def update_spin_value(self, spin: QtWidgets.QDoubleSpinBox, value: float) -> None:
        spin.blockSignals(True)
        spin.setValue(value)
        spin.blockSignals(False)

    def update_slider_value(self, slider: QtWidgets.QSlider, value: float) -> None:
        slider.blockSignals(True)
        slider.setValue(int(value * self.slider_multiplier))
        slider.blockSignals(False)

    def show_pgm_image(self, pgm_file: str) -> None:
        try:
            with open(pgm_file, "r") as f:
                header = f.readline().strip()
                if header != "P2":
                    QtWidgets.QMessageBox.warning(self, "Error", "不明なPGM形式です。")
                    return
                dims = f.readline().strip().split()
                if len(dims) != 2:
                    QtWidgets.QMessageBox.warning(self, "Error", "PGM画像のサイズ情報が不正です。")
                    return
                width, height = int(dims[0]), int(dims[1])
                _ = int(f.readline().strip())
                data = np.array(f.read().split(), dtype=np.uint8)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"PGM画像読み込み時にエラーが発生しました: {e}")
            return

        try:
            image = data.reshape((height, width))
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"画像変換時にエラーが発生しました: {e}")
            return

        matplotlib.use("Qt5Agg")
        plt.figure("PGM Image")
        plt.imshow(image, cmap="gray", interpolation="nearest")
        plt.axis("off")
        plt.show(block=False)
