# SPDX-FileCopyrightText: 2025 Ryo Funai
# SPDX-License-Identifier: Apache-2.0

"""
バックグラウンドで点群を読み込む
"""
from PyQt5 import QtCore
import open3d as o3d

class PointCloudLoaderThread(QtCore.QThread):
    loaded = QtCore.pyqtSignal(object)
    error = QtCore.pyqtSignal(str)

    def __init__(self, input_file: str, parent=None) -> None:
        super().__init__(parent)
        self.input_file = input_file

    def run(self) -> None:
        try:
            pcd = o3d.io.read_point_cloud(self.input_file)
            if not pcd.has_points():
                self.error.emit(f"点群が存在しません: {self.input_file}")
                return
            # 生の点群をそのままemit（描画用のダウンサンプリングはModel側で実施）
            self.loaded.emit(pcd)
        except Exception as e:
            self.error.emit(str(e))
