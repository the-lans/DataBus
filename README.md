# DataBus
Instructions in English [below](#english-version).

Шина обеспечивает взаимодействие клиента (отправителя) и сервера (приёмника) HTTP-запросов. Предназначена в качестве буфера обмена HTTP-запросами (сообщениями). Также имеет интерфейс для взаимодействия с [Redis](https://redis.io/) извне.

<img src=".\images\001.png" alt="001" style="zoom: 50%;" />

Внутри шина устроена примерно так. На схеме показано только движение HTTP-запросов (не весь функционал).

<img src=".\images\002.png" alt="002" style="zoom: 80%;" />

Клиент посылает [специально подготовленный запрос](#%D0%BF%D0%BE%D0%B4%D0%B3%D0%BE%D1%82%D0%BE%D0%B2%D0%BA%D0%B0-%D0%B7%D0%B0%D0%BF%D1%80%D0%BE%D1%81%D0%B0) (input request) в шину. Соответствующий эндпойнт FastAPI обрабатывает поступивший запрос, конвертирует его в сообщение (message request) и сохраняет его в очереди Redis. 

Независимый процесс последовательно достаёт сообщения из очереди, строит из них запросы (output request) и рассылает получателям в соответствии с мепингом. От получателей приходит ответ (response). Ответ преобразуется в сообщение (message response) и сохраняется в отдельной очереди Redis, если это указано в мепинге. Если запрос по каким-либо причинам не был доставлен хотя бы одному получателю, он помещается в самое начало очереди. Каждый из получателей, указанный в мепинге, гарантировано получает данный запрос только один раз независимо от других.

Далее независимый процесс последовательно достаёт сообщения (message response) из очереди, строит из них запросы (async response) и доставляет их исходному клиенту (отправителю исходного запроса = input request) или прочему получателю, который указывается в мепинге. Также, если запрос не был доставлен, он помещается в начало очереди.

Так происходит весь процесс обмена сообщениями (запрос-ответ).

   

## Преимущества

Универсальная шина передачи данных решает такие проблемы как:

1. Изменение IP-адреса сервера. Новый адрес сервера прописывается при этом в мепинге. Достаточно сделать запрос к соответствующему эндпойнту (*PUT /api/map/{item_id}*).
2. Периодическое отключение или нестабильная работа сервера. В этом случае запросы будут накапливаться в очереди шины и будут гарантированно доставлены позже. Клиенту не нужно ждать и повторять отправку запроса.
3. Сложная маршрутизация запросов. Запрос может быть разделён на несколько приёмников. Разные запросы могут быть перенаправлены на разные сервера. Маршруты задаются через мепинг (*POST /api/map/new*).
4. Сложная аутентификация сервера. Некоторые клиенты (например, 1С:Предприятие) не поддерживают JWT-аутентификацию, поэтому шина выступает как шлюз для аутентификации. Требуется доработка функционала.
5. Асинхронное взаимодействие: ответ сервера (приёмника) обрабатывается отдельно и пересылается клиенту (отправителю).

   

## Пример использования

У нас есть небольшая фирма. Она занимается обработкой заявок на партнёрские продукты и доставкой этих товаров потребителю. Для нас важна быстрота реакции на запросы клиентов. Поэтому у нас чётко выстроенные бизнес-процессы.

Мы хотим напрямую отслеживать заказы, созданные через мобильный клиент (мобильное приложение) так, чтобы они мгновенно появлялись в нашей CRM-системе. При этом сама CRM-система находится на ноутбуках наших сотрудников, данные периодически синхронизируются с облаком. Ноутбуки сотрудников подключены к сети только в рабочее время. Заявки на заказы, соответственно, могут быть оставлены пользователями когда угодно, а обрабатываются только в рабочие часы нашими сотрудниками. 

Как работало раньше?

1. В мобильном приложении клиент оформляет новую заявку. Все данные заносятся в [Firestore Database](https://firebase.google.com/).
2. Облачный сервер периодически проверяет данные на изменение в мобильной базе. Т.к. важна реакция, время периодической проверки пришлось сократить до 10 секунд (как на стороне сервера, так и на стороне CRM-клиента). В худшем случае на CRM-клиент заявка может прийти через 20 секунд. 
3. CRM-клиенты проверяют облачный сервер на изменения в данных с периодичностью 10 секунд. Общий поток запросов на чтение составляет: 12 сотрудников x 6 запросов в минуту x 60 минут x 24 часа = 103680 запросов в день. В связи с этим нагрузка на облачную базу начинает увеличиваться и будет только расти. Также за такое количество запросов приходится переплачивать.
4. Действия, которые привязаны к обновлению данных в CRM системе (на клиентах и на облачном сервере), также отрабатывают с указанной выше задержкой.
5. Таким образом заявки гарантировано будут доставлены, но с указанным временным лагом. В большинстве случаев система будет функционировать приемлемо, но за определённую плату. С увеличением штата сотрудников затраты вырастают, возникает проблема масштабирования.

Как работает новая система? 

1. Шина передачи данных устанавливается на облачном сервере и всегда доступна извне.
2. CRM система (клиент) в начале работы сотрудника проверяет актуальность своего IP-адреса и при необходимости посылает запрос в шину на его корректировку, т.к. динамический IP адрес может изменяться.
3. Все заявки, которые накопились в нерабочее время (за ночь), приходят в CRM скопом.
4. В мобильном приложении клиент оформляет новую заявку, нажимает кнопку, отсылается запрос к шине по API.
5. Шина обрабатывает запрос и пересылает его CRM системе. Можно организовать пересылку напрямую CRM-клиентам. Если связь нестабильна, сообщение гарантировано придёт немного позже.
6. CRM система получает запрос, обрабатывает его и оповещает сотрудника о поступившей заявке на заказ. Также CRM может выборочно обновить данные из облака, т.к. получение запроса может являться триггером и на другие действия. 
7. Таким образом сотрудник сможет молниеносно отреагировать на заявку от клиента и обработать её быстро.

   

## СУБД

Шина может использовать для хранения данных любую СУБД, которая поддерживается [ORM Peewee](http://docs.peewee-orm.com/en/latest/). В этом репозитории используется СУБД SQLite. Вы можете легко подключить такие СУБД как: MySQL, PostgreSQL и Cockroach.

Для хранения внешних данных и в качестве очереди шина использует [Redis](https://redis.io/). Redis использует стандартные настройки подключения: redis://localhost:6379/0.

   

## Установка

Последовательность действий для установки:

- Установите и настройте [Redis](https://redis.io/docs/getting-started/installation/)

- Для создания виртуальной среды могут использоваться *conda* или *virtualenv*

- Создайте виртуальное окружение `conda create -n venv`

- Активируйте виртуальное окружение `conda activate venv`

- Установите пакеты `pip install -r requirements.txt`

- Перейдите в папку с проектом

- Создайте новую базу данных \<database\>

- Выполните миграцию `python pw_migrate.py migrate --database=postgresql://postgres@<host_postgres>:5432/<database>`

  *\<host_postgres\>* - рабочий хост базы данных

  *\<database\>* - имя базы данных

- Добавьте пользователя с административной ролью

- Настройте конфигурационный файл *conf.yaml*

- Запустите API `uvicorn main:app --reload`

- Через API заполните необходимые таблицы БД

   

## Отладка

Запустите на отладку файл `main.py`

Запустите `receiver.py` в качестве приёмника запросов и `sender.py` как источник запросов.

`python receiver.py --detail false --server 127.0.0.1`
`python sender.py --detail false --server 127.0.0.1 --user admin --pass password --send all`

Проверьте API на локальной машине: http://127.0.0.1:8000/

Доступ к REST API Swagger: http://127.0.0.1:8000/docs#/

Доступ к REST API Redoc: http://127.0.0.1:8000/redoc

   

## Конфигурация

Настройте конфигурационный файл *conf.yaml*.

Управление авторизацией через JWT токен:

- SECRET_KEY - Секретный ключ.

- ALGORITHM - Алгоритм. Чаще используется HS256.

- ACCESS_TOKEN_EXPIRE_MINUTES - Истечение токена через определённое время (в минутах).

Шина:

- DB.DOMAIN - Текущий домен (адрес), на который приходят запросы.

- DB.PORT - Выделенный порт. Не забудьте настроить разрешения для этого порта в своём брандмауэре.

Управление данными:

- DB.NAME - Расположение БД.

- DB.USER - Пользователь БД.

- DB.ASYNC - Асинхронное взаимодействие с БД (если значение *True*).

- DB.REQUEST_HISTORY - Сохранение истории запросов в БД.

   


## API

|      Group       |                   Type                    |        Endpoint        | Description                                                  |
| :--------------: | :---------------------------------------: | :--------------------: | ------------------------------------------------------------ |
|       user       |                   POST                    |         /login         | Получение текущего токена по кредам.                         |
|       user       |                   POST                    |        /signup         | Создание нового пользователя.                                |
|       user       |                    GET                    |       /api/user        | Сведения о текущем пользователе.                             |
|    HTTPMapApp    |                    GET                    |     /api/map/list      | Маппинг запросов. Список всех элементов.                     |
|    HTTPMapApp    |                    GET                    |    /api/map/update     | Маппинг запросов. Обновление глобальных переменных в самой шине. |
|    HTTPMapApp    |                    GET                    |   /api/map/{item_id}   | Маппинг запросов. Один элемент.                              |
|    HTTPMapApp    |                    PUT                    |   /api/map/{item_id}   | Маппинг запросов. Обновление полей элемента.                 |
|    HTTPMapApp    |                   POST                    |      /api/map/new      | Маппинг запросов. Новый элемент.                             |
|     RedisApp     |      GET<br/>PUT<br/>POST<br/>DELETE      |    /api/redis/{cmd}    | Выполнение запроса в Redis. <br/>*{cmd}* - Команда Redis. Список команд [здесь](https://redis.io/commands/).<br/>*args* - Параметры команды через пробел.<br/>Прочие параметры, определённые через *\<key\>=\<value\>*. |
|     QueueApp     | GET<br/>PUT<br/>POST<br/>PATCH<br/>DELETE |   /api/queue/{name}    | Отправка запроса в очередь шины.<br/>*{name}* - Название очереди. Очередь определяет (через маппинг) куда далее пойдёт запрос. |
| CommonHeadersApp |                    GET                    |   /api/headers/list    | Общие заголовки. Список всех элементов.                      |
| CommonHeadersApp |                    GET                    |  /api/headers/update   | Общие заголовки. Обновление глобальных переменных в самой шине. |
| CommonHeadersApp |                    GET                    | /api/headers/{item_id} | Общие заголовки. Один элемент.                               |
| CommonHeadersApp |                    PUT                    | /api/headers/{item_id} | Общие заголовки. Обновление полей элемента.                  |
| CommonHeadersApp |                   POST                    |    /api/headers/new    | Общие заголовки. Новый элемент.                              |
|  AdditionalApp   |                    GET                    |    /api/common/hash    | Хеш для пароля.                                              |
|  AdditionalApp   |                    GET                    |   /api/common/sha256   | SHA256 для текстовых данных (параметр *data*).               |
|  AdditionalApp   |                   POST                    |   /api/common/sha256   | SHA256 для файла (*file*).                                   |
|  AdditionalApp   |                    GET                    | /api/common/timestamp  | Дата и время в определённом формате.<br/>*sformat* - Заданный формат, *default value*: %Y-%m-%d %H:%M:%S |
|  AdditionalApp   |                    GET                    |    /api/common/now     | Текущие дата и время.                                        |
|  AdditionalApp   |                    GET                    |    /api/common/uuid    | Возвращает случайный UUID.                                   |
|  AdditionalApp   |                    GET                    |   /api/common/srand    | Возвращает случайную строку.<br/>*size* - размер строки<br/>*chars* - типы символов для выборки |
|                  |                                           |                        |                                                              |

   

## Модели

#### User

*username* - Имя пользователя.

*hashed_password* - Хешированный пароль.

*email* - E-mail пользователя.

*full_name* - Полное имя.

*role* - Роль пользователя: *restricted_user*, *user*, *admin*. По умолчанию restricted_user.

*disabled* - Запрет пользователя.

#### HTTPMap

*queue* - Название очереди. По этому полю происходит отбор.

*address* - Конечный адрес сервера: протокол, IP-адрес, порт.

*url* - Путь к конечной точке.

*method* - Используемый метод. По этому полю происходит отбор.

#### CommonHeaders

*queue* - Название очереди. По этому полю происходит отбор.

*key* - Ключ заголовка.

*value* - Значение заголовка.

   

## Подготовка запроса

Чтобы отправить запрос в шину, его необходимо подготовить. Предположим, есть исходный HTTP-запрос для получателя.

1. Изменяем URL на ***/api/queue/{name}*** . *{name}* очереди определяем в соответствии с маппингом.
2. Названия переменных, которые будут использоваться в шаблоне URL запроса, выносим в отдельный параметр-список ***params***.
3. URL-переменные также задаём как отдельные параметры в виде ***\<key\>=\<value\>***.
4. Для авторизации используем заголовок ***Authorization***.
5. Всё остальное оставляем без изменений.

   

## Производительность

Проводились замеры производительности HTTP-запросов напрямую (клиент - сервер) и с шиной. Если использовать хранение истории запросов (параметр *REQUEST_HISTORY*), то скорость шины падает примерно в 4.7 раза. Результаты замеров представлены в таблице ниже в секундах.

| Requests | Directly (First) | Bus + History | Directly (Second) | Bus         |
| -------- | ---------------- | ------------- | ----------------- | ----------- |
| 100      | 7.479515913      | 22.38414639   | 5.861896894       | 4.703070805 |
| 100      | 3.209643742      | 21.44252342   | 4.956573356       | 4.263683129 |
| 100      | 3.249170097      | 22.14673435   | 3.713075762       | 3.458604061 |
| Mean     | 4.646109917      | 21.99113472   | 4.843848671       | 4.141785999 |
|          |                  |               |                   |             |

   

   

# English version

The bus provides interaction between the client (sender) and server (receiver) of HTTP requests. It is intended as an exchange buffer for HTTP requests (messages). It also has an interface for interacting with [Redis](https://redis.io/) from the outside.

<img src=".\images\001.png" alt="001" style="zoom: 50%;" />

Inside the tire is arranged something like this. The diagram shows only the movement of HTTP requests (not all functionality).

<img src=".\images\002.png" alt="002" style="zoom: 80%;" />

The client sends a [prepared-request](#prepare-request) (input request) to the bus. The corresponding FastAPI endpoint processes the incoming request, converts it into a message (message request) and stores it in the Redis queue.

An independent process sequentially retrieves messages from the queue, constructs output requests from them, and sends them to recipients in accordance with the mapping. From the recipients comes the answer (response). The response is converted to a message (message response) and stored in a separate Redis queue if specified in the mapping. If the request for some reason was not delivered to at least one recipient, it is placed at the very beginning of the queue. Each of the recipients specified in the mapping is guaranteed to receive this request only once, regardless of the others.

Next, an independent process sequentially retrieves messages (message response) from the queue, builds requests from them (async response) and delivers them to the original client (original request sender = input request) or other recipient specified in the mapping. Also, if the request was not delivered, it is placed at the front of the queue.

This is how the whole messaging process (request-response) takes place.

   

## Advantages

The universal data bus solves problems such as:

1. Change the IP address of the server. The new server address is written in the mapping. It is enough to make a request to the corresponding endpoint (*PUT /api/map/{item_id}*).

2. Periodic shutdown or unstable operation of the server. In this case, requests will accumulate in the bus queue and will be guaranteed to be delivered later. The client does not need to wait and retry sending the request.

3. Complicated routing of requests. A request can be split into multiple receivers. Different requests can be redirected to different servers. Routes are set via mapping (*POST /api/map/new*).

4. Complex server authentication. Some clients (for example, 1C:Enterprise) do not support JWT authentication, so the bus acts as an authentication gateway. Functionality needs to be improved.

5. Asynchronous interaction: the response of the server (receiver) is processed separately and sent to the client (sender).

   

## Usage example

We have a small firm. It is engaged in the processing of applications for partner products and the delivery of these products to the consumer. Quick response to customer requests is important to us. Therefore, we have well-defined business processes.

We want to directly track orders created through the mobile client (mobile app) so that they appear instantly in our CRM system. At the same time, the CRM system itself is located on the laptops of our employees, the data is periodically synchronized with the cloud. Employee laptops are connected to the network only during working hours. Applications for orders, respectively, can be left by users at any time, and are processed only during business hours by our employees.

How did it work before?

1. In the mobile application, the client makes a new application. All data is entered into [Firestore Database](https://firebase.google.com/).
2. The cloud server periodically checks the data for changes in the mobile database. Because reaction is important, the periodic check time had to be reduced to 10 seconds (both on the server side and on the side of the CRM client). In the worst case, an application can arrive at the CRM client in 20 seconds.
3. CRM clients check the cloud server for changes in data every 10 seconds. The total read request flow is: 12 employees x 6 requests per minute x 60 minutes x 24 hours = 103680 requests per day. In this regard, the load on the cloud base begins to increase and will only grow. Also, for such a number of requests you have to overpay.
4. Actions that are tied to updating data in the CRM system (on clients and on the cloud server) are also processed with the above delay.
5. Thus, applications are guaranteed to be delivered, but with the specified time lag. The system will function acceptable in most cases, but at some cost. With an increase in the number of employees, costs increase, and the problem of scaling arises.

How does the new system work?

1. The data bus is installed on the cloud server and is always accessible from the outside.
2. The CRM system (client) at the beginning of the employee's work checks the relevance of his IP address and, if necessary, sends a request to the bus to correct it, because dynamic IP address can change.
3. All applications that have accumulated during non-working hours (overnight) come to CRM en masse.
4. In the mobile application, the client makes a new request, presses a button, and a request is sent to the bus via the API.
5. The bus processes the request and forwards it to the CRM system. You can organize forwarding directly to CRM clients. If the connection is unstable, the message is guaranteed to arrive a little later.
6. The CRM system receives the request, processes it and notifies the employee about the received request for an order. Also, CRM can selectively update data from the cloud, because. receiving a request can be a trigger for other actions.
7. Thus, the employee will be able to immediately respond to the request from the client and process it quickly.

   

## DBMS

The bus can use any DBMS that is supported by [ORM Peewee](http://docs.peewee-orm.com/en/latest/) for data storage. This repository uses the SQLite DBMS. You can easily connect such DBMS as: MySQL, PostgreSQL and Cockroach.

The bus uses [Redis](https://redis.io/) to store external data and as a queue. Redis uses the default connection settings: redis://localhost:6379/0.

   

## Installation

Installation sequence:

- Install and configure [Redis](https://redis.io/docs/getting-started/installation/)

- *conda* or *virtualenv* can be used to create a virtual environment

- Create a virtual environment `conda create -n venv`

- Activate the virtual environment `conda activate venv`

- Install packages `pip install -r requirements.txt`

- Go to the project folder

- Create a new database \<database\>

- Migrate `python pw_migrate.py migrate --database=postgresql://postgres@<host_postgres>:5432/<database>`

   *\<host_postgres\>* - working database host

   *\<database\>* - database name

- Add a user with administrative role

- Customize the configuration file *conf.yaml*

- Run API `uvicorn main:app --reload`

- Through the API, fill in the required database tables

   

## Debugging

Start debugging the `main.py` file

Run `receiver.py` as source source and `sender.py` as source source.

`python Receiver.py --detail false --server 127.0.0.1`
`python sender.py --detail false --server 127.0.0.1 --user admin --pass password --send all`

Take the API to check the machine: http://127.0.0.1:8000/

Access to Swagger REST API: http://127.0.0.1:8000/docs#/

Access to the Redoc REST API: http://127.0.0.1:8000/redoc

   

## Configuration

Set up the configuration file *conf.yaml*.

Authorization management via JWT token:

- SECRET_KEY - Secret key.

- ALGORITHM - Algorithm. usually HS256 is used.

- ACCESS_TOKEN_EXPIRE_MINUTES - Token expiration after a certain time (in the vicinity).

Tire:

- DB.DOMAIN - Current domain (address) to which requests are received.

- DB.PORT - Dedicated port. You are not supposed to assign a solution to this port in your firewall.

Data management:

- DB NAME - Location of the database.

- DB.USER - Database user.

- DB.ASYNC - Asynchronous interaction with the database (if the value is *True*).

- DB.REQUEST_HISTORY - Saving the history of receipt in the database.

   

## API

|      Group       |                   Type                    |        Endpoint        | Description                                                  |
| :--------------: | :---------------------------------------: | :--------------------: | ------------------------------------------------------------ |
|       user       |                   POST                    |         /login         | Getting the current token by credentials.                    |
|       user       |                   POST                    |        /signup         | Creating a new user.                                         |
|       user       |                    GET                    |       /api/user        | Information about the current user.                          |
|    HTTPMapApp    |                    GET                    |     /api/map/list      | Request mapping. List of all elements.                       |
|    HTTPMapApp    |                    GET                    |    /api/map/update     | Request mapping. Update global variables in the bus itself.  |
|    HTTPMapApp    |                    GET                    |   /api/map/{item_id}   | Request mapping. One element.                                |
|    HTTPMapApp    |                    PUT                    |   /api/map/{item_id}   | Request mapping. Update element fields.                      |
|    HTTPMapApp    |                   POST                    |      /api/map/new      | Request mapping. New element.                                |
|     RedisApp     |      GET<br/>PUT<br/>POST<br/>DELETE      |    /api/redis/{cmd}    | Executing a query in Redis. <br/>*{cmd}* - Redis command. List of commands [here](https://redis.io/commands/).<br/>*args* - Command parameters separated by spaces.<br/>Other parameters defined via *\<key\>=\<value \>*. |
|    Queue App     | GET<br/>PUT<br/>POST<br/>PATCH<br/>DELETE |   /api/queue/{name}    | Sending a request to the bus queue.<br/>*{name}* - The name of the queue. The queue determines (via mapping) where the request will go next. |
| CommonHeadersApp |                    GET                    |   /api/headers/list    | General headers. List of all elements.                       |
| CommonHeadersApp |                    GET                    |  /api/headers/update   | General headers. Update global variables in the bus itself.  |
| CommonHeadersApp |                    GET                    | /api/headers/{item_id} | General headers. One element.                                |
| CommonHeadersApp |                    PUT                    | /api/headers/{item_id} | General headers. Update element fields.                      |
| CommonHeadersApp |                   POST                    |    /api/headers/new    | General headers. New element.                                |
|  AdditionalApp   |                    GET                    |    /api/common/hash    | Hash for the password.                                       |
|  AdditionalApp   |                    GET                    |   /api/common/sha256   | SHA256 for text data (parameter *data*).                     |
|  AdditionalApp   |                   POST                    |   /api/common/sha256   | SHA256 for file (*file*).                                    |
|  AdditionalApp   |                    GET                    | /api/common/timestamp  | Date and time in a specific format.<br/>*sformat* - Specified format, *default value*: %Y-%m-%d %H:%M:%S |
|  AdditionalApp   |                    GET                    |    /api/common/now     | The current date and time.                                   |
|  AdditionalApp   |                    GET                    |    /api/common/uid     | Returns a random UUID.                                       |
|  AdditionalApp   |                    GET                    |   /api/common/srand    | Returns a random string.<br/>*size* - string size<br/>*chars* - character types to sample |
|                  |                                           |                        |                                                              |

   

## Models

#### User

*username* - Username.

*hashed_password* - Hashed password.

*email* - User's e-mail.

*full_name* - Full name.

*role* - User role: *restricted_user*, *user*, *admin*. The default is *restricted_user*.

*disabled* - Disable the user.

#### HTTPMap

*queue* - The name of the queue. This field is being selected.

*address* - End server address: protocol, IP address, port.

*url* - Path to endpoint.

*method* - The method to use. This field is being selected.

#### CommonHeaders

*queue* - The name of the queue. This field is being selected.

*key* - Header key.

*value* - Header value.

   

## Prepare request

To send a request to the bus, it must be prepared. Suppose there is an initial HTTP request for a recipient.

1. Change the URL to ***/api/queue/{name}*** . *{name}* queues are defined according to the mapping.
2. The names of the variables that will be used in the request URL template are put into a separate parameter-list ***params***.
3. URL variables are also set as separate parameters in the form ***\<key\>=\<value\>***.
4. For authorization, use the ***Authorization*** header.
5. Leave everything else unchanged.

   

## Performance

The performance of HTTP requests was measured directly (client - server) and with the bus. If you use request history storage (parameter *REQUEST_HISTORY*), then the bus speed drops by about 4.7 times. The measurement results are presented in the table below in seconds.

| Requests | Directly (First) | Bus + history | Directly (Second) | bus         |
| -------- | ---------------- | ------------- | ----------------- | ----------- |
| 100      | 7.479515913      | 22.38414639   | 5.861896894       | 4.703070805 |
| 100      | 3.209643742      | 21.44252342   | 4.956573356       | 4.263683129 |
| 100      | 3.249170097      | 22.14673435   | 3.713075762       | 3.458604061 |
| mean     | 4.646109917      | 21.99113472   | 4.843848671       | 4.141785999 |
|          |                  |               |                   |             |
