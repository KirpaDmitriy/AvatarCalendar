<h1>Работа с событиями</h1>

<h2>Определение приоритета</h2>

Модуль определения приоритета вычисляет эмоциональность текстового описания события, его близость к корпусу слов-маркеров важности и на основании этих данных выдаёт приоритетность события. Функциональность реализована в статическом методе <i>get_text_priority</i> класса <i>PriorityEstimator</i>. На вход он принимает текст (str) из описания события и его заголовка, на выходе отдаёт вещественное число от 0 до 1. Помимо этого, существует метод <i>get_event_priority</i>, который работает аналогично предыдущему, но на вход принимает сущность события, из которого извлекает нужный для работы <i>get_text_priority</i> текст.


<h2>Переносы событий</h2>

Модуль состоит из нескольких слоёв и лежит в следующих файлах:
<ul>
    <li><b>/libs/transfer_variants.py</b> - логика переноса событий</li>
    <li><b>/libs/bd.py</b> - вспомогательные функции для получения нужных данных из БД (изначально написано для Монго)</li>
    <li><b>/libs/geography.py</b> - модуль для взаимодействия с API геокодера (преобразует текст местоположения в координаты для вычисления расстояния между двумя локациями)</li>
    <li><b>/models/event.py</b> - схема события, на которую опирается модуль</li>
</ul>

<h4>/libs/bd.py</h4>
Включает 2 метода:
<ul>
    <li><b>get_time_segment_user_events</b> - получает на вход айди пользователя, флажок <i>event_beginning</i>, опционально метку <i>before_ts</i>, опционально метку <i>after_ts</i>. Отдаёт курсор, который можно преобразовать в список сущностей события. Имеет следующую логику. По флагу <i>event_beginning</i> определяет, по какому полю таблиы БД проводить поиск: если флаг проставлен в True, то в дальнейшем поиск будет идти по полю date_time_begin, иначе - по полю date_time_end. Далее, в зависимости от того, какие из двух опциональных меток времени были переданы в аргументы, стоится запрос к базе. Если был передан только параметр <i>after_ts</i>, то будет произведён поиск тех событий, у которых целевое поле (то есть метка конца или начала искомых событий) заданное ранее будет позже значения <i>after_ts</i>. Если был передан только параметр <i>before_ts</i>, то будет произведён поиск тех событий, у которых целевое поле раньше значения <i>before_ts</i>. Если заданы оба поля, то будет произведён поиск событий, удовлетворяющих обоим предыдущим условиям. Ко всему добавляется фильтр по пользовательскому айди, чтобы были получены только записи, связанные с текущим пользователем.</li>
    <li><b>get_enveloping_user_events</b> - получает на вход две временные метки <i>begin_ts</i> и <i>end_ts</i> и айди пользователя. Отдаёт курсор, который можно преобразовать в список сущностей события. Назначение - достать те события, которые полностью включают в себя временной отрезок между <i>begin_ts</i> и <i>end_ts</i>. Пример: для события обед с 13 до 14 метод выдаст событие работа с 9 до 18. Ко всему добавляется фильтр по пользовательскому айди, чтобы были получены только записи, связанные с текущим пользователем.</li>
</ul>


<h4>/libs/transfer_variants.py</h4>
<ul>
    <li><b>check_intersections</b> - получает на вход сущность события и айди пользователя. Выдёт список сущностей события. Использует методы <b>/libs/bd.py</b> <i>get_time_segment_user_events</i> и <i>get_enveloping_user_events</i></li>. Получает список событий, которые начинаются во время события пришедшего на вход, которые кончаются во время события пришедшего на вход и которые полностью включают в себя событие пришедшее на вход. Таким образом, метод находит все события, которые как-то накладываются на переданное в аргументе. Все списки формируются для пользователя, айди которого было передано в аргументах.</li>
    <li><b>generate_event_variants</b> - получает на вход айди пользователя, длительность переносимой группы событий (группа может состоять и из одного события), место начала группы событий (то есть место начала самого раннего из них) и место конца группы событий (то есть самый поздний конец входящих в группу событий). Для данного пользователя формируются варианты переноса события на другое время. Выдаётся список из пяти временных меток - варинтов переноса.</li>
    <li><b>get_cancellations</b> - получает на вход айди пользователя и сущность события. Отдаёт словарь с двумя ключами: <i>most_important</i> и <i>less_important</i>. По каждому ключу лежит список из 5 кортежей. В каждом кортеже по 2 элемента: список сущностей события (переносимая группа событий) и список временных меток (вариантов переноса). По ключу <i>most_important</i> лежат варианты для переноса группы событий, приоритет которой систма определила, как минимальный среди добавляемого события и пересекающихся с ним. По ключу <i>less_important</i> лежат варианты для переноса группы событий, приоритет которой систма определила, как максимальный среди добавляемого события и пересекающихся с ним.</li>
</ul>


<h4>/models/event.py</h4>
Описание требуемой формы сущности события.
