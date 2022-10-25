<h1>API модуля</h1>

<h2>main.py -> get_prority</h2>
По тексту события определяет его приоритет.

<h4>Вход</h4>
Строка-описание события

<h4>Выход</h4>
Число - приоритетность события из строки

<hr>

<h2>main.py -> get_transfer_variants</h2>
Определяет, куда в календаре можно поставить новое собтие с учётом уже занесённых пользователем в календарь.

<h4>Вход</h4>
event - сущность <a href="https://github.com/KirpaDmitriy/AvatarCalendar/blob/7dd6ae9e47763ff114756b842087eebbecccef27/app/models/event.py">EventCalendar</a>, user_id - строка-айди пользователя
<h4>Выход</h4>
Словарь с двумя ключами: most_important и less_important. По каждому ключу лежит список из 5 кортежей. В каждом кортеже по 2 элемента: список сущностей <a href="https://github.com/KirpaDmitriy/AvatarCalendar/blob/7dd6ae9e47763ff114756b842087eebbecccef27/app/models/event.py">EventCalendar</a> (переносимая группа событий) и список временных меток (вариантов переноса).
