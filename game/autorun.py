import sys
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QStatusBar, QPushButton, QVBoxLayout, QWidget, QLineEdit, QLabel
from tetris_main import main

class StatusBarGame(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(300, 50, 200, 150)  # 调整窗口大小
        self.setWindowTitle('Game Setup')

        self.centralWidget = QWidget(self)
        self.setCentralWidget(self.centralWidget)
        layout = QVBoxLayout()

        # 添加 exp_no 输入框和标签
        self.expNoLabel = QLabel("Experiment Number (exp_no):", self)
        layout.addWidget(self.expNoLabel)
        
        self.expNoInput = QLineEdit(self)
        layout.addWidget(self.expNoInput)

        # 添加确认按钮
        self.confirmButton = QPushButton("Confirm and Start Game", self)
        self.confirmButton.clicked.connect(self.confirm)
        layout.addWidget(self.confirmButton)

        self.centralWidget.setLayout(layout)

    def confirm(self):
        try:
            exp_no = int(self.expNoInput.text())
            self.hide()  # 隐藏设置窗口
            run_game(exp_no)  # 使用用户输入的 exp_no 启动游戏
        except ValueError:
            # 如果输入无效，可以在这里处理（比如通过弹窗通知用户）
            self.expNoLabel.setText("Please enter a valid number for exp_no:")

def run_game(exp_no):
    patience = 2
    increase_thresh = 0.1
    max_score = 0
    round_remain = patience
    start_mode = "normal"
    round_no = 1

    app = QApplication(sys.argv)
    game_status = QMainWindow()
    game_status.setGeometry(300, 50, 500, 100)
    game_status.setWindowTitle('Game Status')
    statusBar = QStatusBar()
    game_status.setStatusBar(statusBar)
    game_status.show()
    while round_remain >= 0:
        current_status = "Running" if round_remain > 0 else "Game Over"
        statusBar.showMessage(f'Max Score: {max_score} | Rounds Left: {round_remain} | Status: {current_status}')
        new_score = main(start_mode, exp_no, round_no)
        if new_score > max_score * (1 + increase_thresh):
            max_score = new_score
            round_remain = patience
        else:
            round_remain -= 1

        statusBar.showMessage(f'Max Score: {max_score} | Rounds Left: {round_remain} | Status: Waiting')
        time.sleep(5) 

        round_no += 1

        QApplication.processEvents()  # 处理用户界面事件，例如点击操作

        if round_remain < 0:
            statusBar.showMessage(f'Max Score: {max_score} | Rounds Left: {round_remain} | Status: "Game Over"')
            time.sleep(5)
            break

    sys.exit(app.exec_())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = StatusBarGame()
    ex.show()
    sys.exit(app.exec_())
