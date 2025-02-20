# SPDX-FileCopyrightText: 2025 Ryo Funai
# SPDX-License-Identifier: Apache-2.0

"""
ModelとViewの仲介および各種ロジック処理
"""
import sys
import numpy as np
from PyQt5 import QtWidgets, QtCore
from model import IPointCloudModel
from view import IPointCloudView

class PointCloudController:
    def __init__(
        self,
        model: IPointCloudModel,
        view: IPointCloudView,
        loader,
        output_dir: str,
    ) -> None:
        self.model = model
        self.view = view
        self.loader = loader
        self.output_dir = output_dir

        self.timer_interval = 10  # [ms]
        self.update_timer = QtCore.QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.update_filter)

        self._connect_signals()

        # LoaderスレッドのシグナルをControllerのコールバックに接続して起動
        self.loader.loaded.connect(self.on_point_cloud_loaded)
        self.loader.error.connect(self.on_point_cloud_error)
        self.loader.start()

    def _connect_signals(self) -> None:
        self.view.zmin_spin.valueChanged.connect(self.on_zmin_changed)
        self.view.zmin_slider.valueChanged.connect(self.on_zmin_slider_changed)
        self.view.zmax_spin.valueChanged.connect(self.on_zmax_changed)
        self.view.zmax_slider.valueChanged.connect(self.on_zmax_slider_changed)
        self.view.reset_button.clicked.connect(self.on_reset)
        self.view.convert_button.clicked.connect(self.on_convert)
        self.view.set_output_filename_button.clicked.connect(self.on_set_output_filename)
        self.view.set_resolution_button.clicked.connect(self.on_set_resolution)

    def on_point_cloud_loaded(self, pcd) -> None:
        try:
            self.model.set_point_cloud_data(pcd)
        except ValueError as e:
            QtWidgets.QMessageBox.critical(self.view, "Error", str(e))
            sys.exit(1)

        overall_min = self.model.overall_z_min
        overall_max = self.model.overall_z_max
        current_min = self.model.current_min_z
        current_max = self.model.current_max_z

        self.view.zmin_spin.setRange(overall_min, overall_max)
        self.view.zmin_spin.setValue(current_min)
        self.view.zmin_slider.setMinimum(int(overall_min * self.view.slider_multiplier))
        self.view.zmin_slider.setMaximum(int(overall_max * self.view.slider_multiplier))
        self.view.zmin_slider.setValue(int(current_min * self.view.slider_multiplier))

        self.view.zmax_spin.setRange(overall_min, overall_max)
        self.view.zmax_spin.setValue(current_max)
        self.view.zmax_slider.setMinimum(int(overall_min * self.view.slider_multiplier))
        self.view.zmax_slider.setMaximum(int(overall_max * self.view.slider_multiplier))
        self.view.zmax_slider.setValue(int(current_max * self.view.slider_multiplier))

        # 初期表示：モデルの全点群データを描画
        full_poly = self.model.display_cloud
        self.view.plotter.clear()
        self.view.actor = self.view.plotter.add_mesh(
            full_poly,
            scalars="z",
            cmap="nipy_spectral",
            point_size=2,
            render_points_as_spheres=False,
            show_scalar_bar=True,
            scalar_bar_args={
                "title": "Z Value",
                "vertical": True,
                "position_x": 0.9,
                "position_y": 0.1,
                "width": 0.02,
                "height": 0.8,
                "title_font_size": 14,
                "label_font_size": 12,
            },
            reset_camera=True
        )
        self.view.cloud_mesh = full_poly
        self.view.plotter.reset_camera()
        self.view.plotter.show_axes()
        self.view.plotter.render()

        if hasattr(self.view, "splash") and self.view.splash:
            self.view.splash.finish(self.view)
        self.view.show()

    def on_point_cloud_error(self, error_msg: str) -> None:
        QtWidgets.QMessageBox.critical(self.view, "Error", f"点群データの読み込みに失敗しました:\n{error_msg}")
        sys.exit(1)

    def on_zmin_changed(self, value: float) -> None:
        self.model.current_min_z = value
        self.view.update_slider_value(self.view.zmin_slider, value)
        if self.model.current_min_z > self.model.current_max_z:
            self.model.current_max_z = self.model.current_min_z
            self.view.update_spin_value(self.view.zmax_spin, self.model.current_max_z)
            self.view.update_slider_value(self.view.zmax_slider, self.model.current_max_z)
        self.update_timer.start(self.timer_interval)

    def on_zmax_changed(self, value: float) -> None:
        self.model.current_max_z = value
        self.view.update_slider_value(self.view.zmax_slider, value)
        if self.model.current_max_z < self.model.current_min_z:
            self.model.current_min_z = self.model.current_max_z
            self.view.update_spin_value(self.view.zmin_spin, self.model.current_min_z)
            self.view.update_slider_value(self.view.zmin_slider, self.model.current_min_z)
        self.update_timer.start(self.timer_interval)

    def on_zmin_slider_changed(self, slider_value: int) -> None:
        new_value = slider_value / self.view.slider_multiplier
        self.view.update_spin_value(self.view.zmin_spin, new_value)
        self.model.current_min_z = new_value
        self.update_timer.start(self.timer_interval)

    def on_zmax_slider_changed(self, slider_value: int) -> None:
        new_value = slider_value / self.view.slider_multiplier
        self.view.update_spin_value(self.view.zmax_spin, new_value)
        self.model.current_max_z = new_value
        self.update_timer.start(self.timer_interval)

    def on_reset(self) -> None:
        self.model.current_min_z = self.model.overall_z_min
        self.model.current_max_z = self.model.overall_z_max
        self.view.update_spin_value(self.view.zmin_spin, self.model.current_min_z)
        self.view.update_spin_value(self.view.zmax_spin, self.model.current_max_z)
        self.view.update_slider_value(self.view.zmin_slider, self.model.current_min_z)
        self.view.update_slider_value(self.view.zmax_slider, self.model.current_max_z)
        self.update_timer.start(self.timer_interval)

    def update_filter(self) -> None:
        polydata = self.model.get_polydata(self.model.current_min_z, self.model.current_max_z)
        if polydata is None:
            if self.view.actor is not None:
                self.view.plotter.remove_actor(self.view.actor)
                self.view.actor = None
                self.view.cloud_mesh = None
            self.view.plotter.render()
            return

        if self.view.actor is not None and self.view.cloud_mesh is not None:
            if self.view.cloud_mesh.n_points == polydata.n_points:
                np.copyto(self.view.cloud_mesh.points, polydata.points)
                self.view.cloud_mesh["z"] = polydata["z"]
                self.view.cloud_mesh.Modified()
            else:
                new_mesh = polydata
                mapper = self.view.actor.GetMapper()
                mapper.SetInputData(new_mesh)
                self.view.cloud_mesh = new_mesh
        else:
            self.view.actor = self.view.plotter.add_mesh(
                polydata,
                scalars="z",
                cmap="nipy_spectral",
                point_size=2,
                render_points_as_spheres=False,
                show_scalar_bar=True,
                scalar_bar_args={
                    "title": "Z Value",
                    "vertical": True,
                    "position_x": 0.9,
                    "position_y": 0.1,
                    "width": 0.02,
                    "height": 0.8,
                    "title_font_size": 14,
                    "label_font_size": 12,
                },
                reset_camera=False
            )
            self.view.cloud_mesh = polydata
        self.view.plotter.render()

    def on_set_output_filename(self) -> None:
        text, ok = QtWidgets.QInputDialog.getText(
            self.view,
            "Output File Name",
            "出力PGMファイル名:",
            text=self.view.user_output_filename
        )
        if ok and text.strip():
            self.view.user_output_filename = text.strip()
            self.view.output_file_label.setText("Output File Name: " + self.view.user_output_filename)
            self.view.plotter.render()

    def on_set_resolution(self) -> None:
        dialog = QtWidgets.QInputDialog(self.view)
        dialog.setInputMode(QtWidgets.QInputDialog.DoubleInput)
        dialog.setWindowTitle("Set Resolution")
        dialog.setLabelText("解像度[m/px] を入力してください:")
        dialog.setDoubleValue(self.view.user_resolution)
        dialog.setDoubleDecimals(3)

        spin_box = dialog.findChild(QtWidgets.QDoubleSpinBox)
        if spin_box is not None:
            spin_box.setSingleStep(0.05)

        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.view.user_resolution = dialog.doubleValue()
            self.view.resolution_label.setText("Resolution: {:.3f} [m/px]".format(self.view.user_resolution))
            self.view.plotter.render()

    def on_convert(self) -> None:
        try:
            pgm_path, yaml_path = self.model.convert_to_pgm(
                self.model.current_min_z,
                self.model.current_max_z,
                self.view.user_resolution,
                self.output_dir,
                self.view.user_output_filename
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(self.view, "Error", f"PGM/YAML出力時にエラーが発生しました: {e}")
            return

        message = f"PGMファイルを出力しました: {pgm_path}\nYAMLファイルを出力しました: {yaml_path}"
        QtWidgets.QMessageBox.information(self.view, "Success", message)
        self.view.show_pgm_image(pgm_path)
