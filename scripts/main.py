import sys
import argparse
from PyQt5 import QtWidgets, QtCore, QtGui
from model import PointCloudModel
from view import PointCloudView
from controller import PointCloudController
from loader import PointCloudLoaderThread

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="入力点群ファイル (.pcd または .ply)")
    parser.add_argument("output_dir", help="出力先ディレクトリ")
    args = parser.parse_args()

    app = QtWidgets.QApplication(sys.argv)

    # スプラッシュスクリーンの設定
    pixmap = QtGui.QPixmap(400, 300)
    pixmap.fill(QtCore.Qt.gray)
    splash = QtWidgets.QSplashScreen(pixmap, QtCore.Qt.WindowStaysOnTopHint)
    splash.showMessage("Loading point cloud...", QtCore.Qt.AlignCenter | QtCore.Qt.AlignBottom, QtCore.Qt.white)
    splash.show()

    # DI（依存性注入）
    model = PointCloudModel()
    view = PointCloudView()
    view.splash = splash  # スプラッシュスクリーンをViewに注入
    loader = PointCloudLoaderThread(args.input_file)
    output_dir = args.output_dir

    # Controllerに各コンポーネントを注入
    _ = PointCloudController(model, view, loader, output_dir)

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
