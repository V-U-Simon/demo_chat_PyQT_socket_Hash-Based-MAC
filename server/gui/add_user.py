from PyQt5.QtWidgets import (
    QDialog,
    QPushButton,
    QLineEdit,
    QApplication,
    QLabel,
    QMessageBox,
)
from PyQt5.QtCore import Qt

from db_server import Storage
from core.core import MessageProcessor


class RegisterUser(QDialog):
    """Класс диалог регистрации пользователя на сервере."""

    def __init__(self, db: Storage, server: MessageProcessor):
        super().__init__()

        self.db = db
        self.server = server

        self.setWindowTitle("Регистрация")
        self.setFixedSize(175, 183)
        self.setModal(True)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.label_username = QLabel("Введите имя пользователя:", self)
        self.label_username.move(10, 10)
        self.label_username.setFixedSize(150, 15)

        self.client_name = QLineEdit(self)
        self.client_name.setFixedSize(154, 20)
        self.client_name.move(10, 30)

        self.label_passwd = QLabel("Введите пароль:", self)
        self.label_passwd.move(10, 55)
        self.label_passwd.setFixedSize(150, 15)

        self.client_passwd = QLineEdit(self)
        self.client_passwd.setFixedSize(154, 20)
        self.client_passwd.move(10, 75)
        self.client_passwd.setEchoMode(QLineEdit.Password)
        self.label_conf = QLabel("Введите подтверждение:", self)
        self.label_conf.move(10, 100)
        self.label_conf.setFixedSize(150, 15)

        self.client_conf = QLineEdit(self)
        self.client_conf.setFixedSize(154, 20)
        self.client_conf.move(10, 120)
        self.client_conf.setEchoMode(QLineEdit.Password)

        self.btn_ok = QPushButton("Сохранить", self)
        self.btn_ok.move(10, 150)
        self.btn_ok.clicked.connect(self.save_data)

        self.btn_cancel = QPushButton("Выход", self)
        self.btn_cancel.move(90, 150)
        self.btn_cancel.clicked.connect(self.close)

        self.messages = QMessageBox()

        self.show()

    def save_data(self):
        """
        Метод проверки правильности ввода и сохранения в базу нового пользователя.
        """
        username = self.client_name.text()
        password = self.client_passwd.text()
        confirm_password = self.client_conf.text()

        if not username:
            self.messages.critical(self, "Ошибка", "Не указано имя пользователя.")
            return
        elif password != confirm_password:
            self.messages.critical(self, "Ошибка", "Введённые пароли не совпадают.")
            return
        elif self.db.check_user_existing(username):
            self.messages.critical(self, "Ошибка", "Пользователь уже существует.")
            return
        else:
            new_user = self.db.add_user(username, password)
            if not new_user:
                self.messages.critical(self, "Ошибка", "Ошибка при создании пользователя.")
                return

            # Рассылаем клиентам сообщение о необходимости обновить справочники
            self.messages.information(self, "Успех", "Пользователь успешно зарегистрирован.")
            self.server.service_update_lists()
            self.close()


if __name__ == "__main__":
    app = QApplication([])
    database = Storage()
    server = MessageProcessor("127.0.0.1", 7777, database)

    dial = RegisterUser(database, server)
    app.exec_()
