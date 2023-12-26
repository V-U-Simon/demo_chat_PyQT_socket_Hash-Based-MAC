import dis


# Метакласс для проверки соответствия сервера:
class ServerMaker(type):
    def __init__(cls, clsname, bases, clsdict):
        # Список методов, которые используются в функциях класса:
        methods = []
        # Атрибуты, вызываемые функциями классов
        attrs = []
        for func in clsdict:
            # Пробуем
            try:
                ret = dis.get_instructions(clsdict[func])
                # Если не функция то ловим исключение
            except TypeError:
                pass
            else:
                # Раз функция разбираем код, получая используемые методы и атрибуты.
                for i in ret:
                    if i.opname == "LOAD_GLOBAL":
                        if i.argval not in methods:
                            methods.append(i.argval)
                    elif i.opname == "LOAD_ATTR":
                        if i.argval not in attrs:
                            attrs.append(i.argval)
        # Если обнаружено использование недопустимого метода connect, бросаем исключение:
        if "connect" in methods:
            raise TypeError("Использование метода connect недопустимо в серверном классе")
        # Если сокет не инициализировался константами SOCK_STREAM(TCP) AF_INET(IPv4), тоже исключение.
        if not ("SOCK_STREAM" in attrs and "AF_INET" in attrs):
            raise TypeError("Некорректная инициализация сокета.")
        super().__init__(clsname, bases, clsdict)
