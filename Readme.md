# app/__ init __.py
Az alkalmazás inicializáló modulja. 

Itt történik:
- A Flask alkalmazás létrehozása
- Az adatbázis konfigurálása
- A migrációs rendszer inicializálása
- A bejelentkezési rendszer konfigurálása
- A route-ok (blueprintek) regisztrálása

Globális objektumok:
- db = SQLAlchemy() – Adatbázis kapcsolat kezelése
- migrate = Migrate() – Flask-Migrate integráci
- login_manager = LoginManager() – Flask-Login konfiguráció
    login_view = "auth.login" → ha nem bejelentkezett felhasználó védett oldalra megy, ide irányít

create_app() függvény, az alkalmazás factory függvénye, amely:
1. Létrehozza a Flask app-ot
2. Beállítja a globális/környezeti változókat
3. Dialektusfüggő SQLAlchemy engine opciókat ad meg
4. Inicializála:
    - db
    - migrate
    - login_manager
5. Regisztrálja a bp-ket

# app/models.py
Az adatbázis modellek definícióját tartalmazza.

User modell:
- Mezők:
    - id – elsődleges kulcs
    - email – egyedi email cím
    - password_hash – titkosított jelszó
    - created_at – létrehozás dátuma
- Metódusok:
    - set_password(pw)
    - check_password(pw)

Photo modell:
- Mezők:
    - id – elsődleges kulcs
    - user_id – idegen kulcs a User táblára
    - name – kép neve (max 40 karakter)
    - upload_dt – feltöltés ideje
    - s3_key – S3 objektum kulcs

# app/routes_auth.py
A hitelesítési végpontokat tartalmazza.

Végpontok:
1. GET /register: Megjeleníti a regisztrációs űrlapot.

2. POST /register: Felhasználó regisztráció

3. GET /login: Bejelentkezési oldal megjelenítése.

4. POST /login: Felhasználó belépése

5. POST /logout: Kijelentkezés és visszairányítás login oldalra

# app/routes_photos.py
A képfeltöltéssel, listázással és törléssel kapcsolatos végpontokat tartalmazza.

Engedélyezett formátumok: "jpg", "jpeg", "png", "webp"

Végpontok:
1. GET /: Főoldal, képek listázása.
    - sort → "date" vagy "name"
    - dir → "asc" vagy "desc"
2. POST /upload: Feltöltési folyamat
3. GET /photo/<photo_id>: Kép lekérdezése
4. POST /delete/<photo_id>: Jogosultság ellenőrzés, S3 objektum és DB rekord törlése

# app/s3.py
Az AWS S3 műveletek absztrakciója.
1. s3_client()
    - AWS régió beolvasása
    - boto3.client() létrehozása
    - signature_version="s3v4"
2. upload_fileobj(fileobj, bucket, key, content_type)
    - Fájl feltöltése S3-ba
3. delete_object(bucket, key)
    - Objektum törlése S3-ból
4. presigned_get_url(bucket, key, expires_sec)
    - Időkorlátos letöltési URL generálása
    - Időkorlát: 3600 mp

# app.py
Ez egy futtatható Flask belépési pont, ami a csomagban lévő create_app() factory-val létrehozza az appot, és ad néhány üzemeltetési (observability) extrát. Csak a lokális futtatás során volt használva.

# wsgi.py
Ez a WSGI entrypoint production futtatáshoz (Gunicorn/Elastic Beanstalk tipikus mintája).
- from app import create_app
- app = create_app()
- Tartalmaz egy GET /health endpointot is.
A Gunicorn ezt a fájlt importálja, és innen kapja meg az app objektumot, amit kiszolgál.

# Procfile
Egy process definíciós fájl (Heroku-s hagyomány, de Elastic Beanstalknál is szokás), ami megmondja, hogyan induljon a web szerver.

Tartalma és jelentése:
- wsgi:app → a wsgi.py modulban lévő app változót szolgálja ki
- --workers 1 → 1 worker process
- --threads 2 → 2 thread / worker
- --timeout 120 és --graceful-timeout 120 → 120 mp request timeout, illetve graceful leállási idő
- --keep-alive 5 → 5 mp keep-alive kapcsolat
Ezek a timeoutok és worker/thread értékek erősen befolyásolják a terhelhetőséget és azt, hogy hosszabb kérések ne essenek szét túl gyorsan.

# .github/workflows/deploy.yml
GitHub Actions workflow, ami automatikus deployt csinál AWS Elastic Beanstalkra, ha a main branch-re push történik.

Lépések:
- Repo checkout 
- Python setup (nálad: python-version: "3.14" – erre figyelj, mert ez nem tipikus/általános EB runtime verzió) 
- pip install -r requirements.txt 
- deploy.zip készítése, kihagyva pl. .git, .github, .venv, __pycache__, .env, local.db 
- AWS credential beállítás GitHub secret-ekből 
- Deploy Elastic Beanstalkra einaregilsson/beanstalk-deploy@v22 actionnel 
    - version_label: ${{ github.sha }}
    - wait_for_deployment: false → nem várja meg a deploy végét a workflow

# .ebextensions/healthcheck.config
Elastic Beanstalk környezeti beállítás: megmondja, hogy melyik URL-en healthcheckeljen az EB.

- HealthCheckPath: /health
- Össze van hangolva a wsgi.py /health endpointtal.

# .platform/hooks/postdeploy/01_migrate.sh
Deploy során futtatott shell script, ami adatbázis migrációt futtat.

Lépések:
- set -e → ha bármi hibázik, azonnal megáll
- cd /var/app/current → EB alatt tipikus az app könyvtár
- source /var/app/venv/*/bin/activate → aktiválja a virtualenvet
- export FLASK_APP=app
- flask db upgrade → lefuttatja az Alembic migrációkat (legfrissebb verzióra)

# .platform/nginx/conf.d/proxy_timeout.conf
Nginx/EB proxy konfigurációs részlet, ami a reverse proxy timeoutokat növeli.

Miket állít be:
- proxy_connect_timeout 120s
- proxy_send_timeout 120s
- proxy_read_timeout 120s
- send_timeout 120s
Ha a backend (Gunicorn/Flask) néha 30–60+ másodpercet dolgozik (pl. nagyobb S3 művelet, DB), az alapértelmezett proxy timeout túl rövid lehet, és a kliens idő előtt “gateway timeout”-ot kaphat.

# migrations/env.py
Ez Alembic/Flask-Migrate környezetfájl, ami megmondja a migrációs eszköznek:
- hogyan éri el az adatbázist,
- honnan vegye a SQLAlchemy metadata-t,
- hogyan fusson online/offline migráció.

Miket csinál:
- Betölti az Alembic konfigurációt, loggingot állít (fileConfig)
- get_engine() / get_engine_url():
    - kompatibilitást kezel Flask-SQLAlchemy verziók között (régi: get_engine(), újabb: db.engine)
    - beállítja az Alembic sqlalchemy.url értékét a Flask app DB URL-jéből
- get_metadata():
    - visszaadja a target metadata-t autogenerate-hez
- run_migrations_offline():
    - engine nélkül (csak URL-lel) konfigurál
- run_migrations_online():
    - engine connectionnel futtat migrációkat
    - tartalmaz egy process_revision_directives hook-ot: ha --autogenerate esetén nincs séma változás, akkor nem generál üres migrációt (“No changes in schema detected.”)