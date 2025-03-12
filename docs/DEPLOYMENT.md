# Установка и запуск приложения на удаленном сервере

## Требования к предварительному наличию ПО на сервере
### Docker
Для запуска приложения рекомендуется использовать платформу [Docker](https://docs.docker.com/).
Таким образом, перед началом установки проекта убедитесь в наличии
установленного [Docker Engine](https://docs.docker.com/engine/install/).
### Nginx
Есть возможность миновать запуск контейнера с прокси-сервером nginx, 
если хотите использовать собственный установленный в системе сервер nginx.
### Git
Будет применяться для переноса проекта на наш сервер с Github.
## Скачивание исходного кода проекта
Склонируйте проект при помощи git
```shell
cd ~/hosted_apps/
git clone https://github.com/Gevorji/weather-app.git
```

## Файл переменных окружения .env
Файл должен располагаться в корневой директории приложения и содержать следующие переменные:
- `OPENWEATHERMAP_API_KEY` - секретный токен для подключения к api сервисов openweathermap
- `OPENWEATHERMAP_GEOCODINGAPI_URL` - базовая часть url для запросов к сервису Openweathermap Geocoding Api, 
- после которой следуют параметры запроса
- `OPENWEATHERMAP_CURRENTWEATHERDATA_API_URL` - базовая часть url для запросов к сервису Openweathermap CurrentWeather Api, 
- после которой следуют параметры запроса
- `DB_NAME` - имя базы данных, которую будет использовать приложение (значение должно совпадать с POSTGRES_USER)
- `DB_USER` - имя пользователя для подключения к БД (значение должно совпадать с POSTGRES_USER)
- `DB_PASSWORD` - пароль пользователя для подключения к БД (значение должно совпадать с POSTGRES_PASSWORD)
- `DB_HOST` - адрес хоста БД для подключения (при запуске через docker compose - имя сервиса)
- `DB_PORT` - порт для подключения БД
- `DJANGO_SECRET_KEY` - [секретный ключ Django](https://docs.djangoproject.com/en/5.1/ref/settings/#std-setting-SECRET_KEY)
- `DJANGO_ALLOWED_HOSTS` - список адресов разрешенных хостов для данного Django проекта
- `DJANGO_DEBUG` - переменная, контролирующая DEBUG режим проекта Django, если установлено какое-либо значение,
режим будет включен
- `POSTGRES_USER` - имя пользователя, который будет создан в Postgresql при запуске контейнера
- `POSTGRES_PASSWORD` - пароль пользователя, который будет создан в Postgresql при запуске контейнера

\* значения переменных, начинающихся с DJANGO, 
будут прочитаны в соотвествующие переменные модуля настроек проекта Django
## Запуск docker-контейнеров
Убедитесь, что вы в корневой директории приложения:
```shell
cd ~/hosted_apps/weather-app
```
Убедитесь, что в корневой директории приложения присутствует файл переменных окружения
[.env](#файл-переменных-окружения-env) с валидным содержимым.
### Без контейнера nginx
В этом случае будут запущены только контейнеры базы данных и приложения. Контейнер приложения будет привязан к внешнему
порту __8000__ на адресе __127.0.0.1__.

Предусмотрена возможность изменения внешнего порта и адреса контейнера приложения через переменную окружения 
WEATHERAPP_SERVER_ADDR_BIND. Корректные значения для переменной такие же, как для HOSTS в 
[синтаксисе](https://docs.docker.com/reference/compose-file/services/#short-syntax-3) 
значения ключа ports файла docker-compose. Переменная окружения должна быть установлена до запуска контейнеров:
```shell
export WEATHERAPP_SERVER_ADDR_BIND=your_value
```
Контейнеры запускаются командой:
```shell
docker compose -f docker/docker-compose.prod.yml up -d
```
Останавливаются командой:
```shell
docker compose -f docker/docker-compose.prod.yml down
```
### C контейнером nginx
Nginx займет порт 3035 по умолчанию. Это можно исправить в файле docker-compose.nginx.opt.prod.yml
в ключе ports сервиса nginx.

Запуск проекта с готовым контейнером nginx:
```shell
docker compose -f docker/docker-compose.prod.yml -f docker/nginx/docker-compose.nginx.opt.prod.yml up -d
```
Остановка контейнеров:
```shell
docker compose -f docker/docker-compose.prod.yml f docker/nginx/docker-compose.nginx.opt.prod.yml down
```
### Выполнение миграций для БД
После запуска контейнеров будет создана чистая база данных. Для работы приложеня необходимо выполнить
миграции Django внутри контейнера приложения:
```shell
docker compose -f docker/docker-compose.prod.yml exec weatherapp python weatherapp/manage.py migrate --noinput
```
## Удаление истекших сессий пользователей из БД
Рекомендуется периодически чистить базу данных от записей, которые соответствуют истекшим сессиям:
```shell
docker compose -f docker/docker-compose.prod.yml exec weatherapp python weatherapp/manage.py clearsessions
```
Можно настроить планировщик задач cron, имеющийся в Linux дистрибутиве, чтобы делать это на регулярной основе:
```shell
crontab -e
# следующую строку вставить в открывшемся текстовом редакторе
@weekly docker compose -f docker/docker-compose.prod.yml exec weatherapp python weatherapp/manage.py clearsessions
```
## Учетная запись администратора
Для доступа к админ-панели сайта, позволяющей редактировать данные приложения, необходимо создать администратора с паролем:
```shell
docker compose -f docker/docker-compose.prod.yml exec -it weatherapp python weatherapp/manage.py createsuperuser
# введите все запрашиваемые поля в интерактивном режиме
```
Админ панель будет доступна по адресу /admin/.