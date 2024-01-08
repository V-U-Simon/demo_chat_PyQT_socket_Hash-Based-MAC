import messeghost8740

# from messeghost8740.server import main
# from messenger8740.client import main
import threading
import signal

from messeghost8740.server import main

print(dir(messeghost8740))
print(dir(messeghost8740.server))
# print(dir(server))
main()
messeghost8740.server
# # Создание списка для отслеживания всех потоков
# threads = []

# # Создание события для управления остановкой
# stop_event = threading.Event()


# def stop_processes():
#     # Устанавливаем событие остановки
#     stop_event.set()
#     # Ожидаем завершения каждого потока
#     for thread in threads:
#         thread.join()


# if __name__ == "__main__":
#     while True:
#         text_for_input = "Выберите действие: q - выход, s - запустить сервер и клиенты, x - закрыть все окна: "
#         action = input(text_for_input)

#         if action == "q":
#             stop_processes()
#             break
#         elif action == "s":
#             # Сброс события остановки для нового запуска
#             stop_event.clear()

#             # Запуск сервера
#             server_thread = threading.Thread(target=main, args=(stop_event,))
#             server_thread.start()
#             threads.append(server_thread)

#             # Запуск двух клиентов
#             for i in range(2):
#                 client_thread = threading.Thread(target=main, args=(f"test{i+1}", stop_event))
#                 client_thread.start()
#                 threads.append(client_thread)

#         elif action == "x":
#             stop_processes()
#             print("Процессы остановлены.")
