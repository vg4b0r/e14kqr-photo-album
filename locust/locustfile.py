from locust import HttpUser, task, between
import uuid
import random
import re


class PhotoAlbumUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.email = f"locust_{uuid.uuid4().hex[:12]}@example.com"
        self.password = "Teszt123!"
        self.owned_photo_ids = []

        self.register()
        self.login()

    def register(self):
        with self.client.post(
            "/register",
            data={
                "email": self.email,
                "password": self.password,
            },
            name="POST /register",
            allow_redirects=True,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Regisztráció sikertelen: {response.status_code}")

    def login(self):
        with self.client.post(
            "/login",
            data={
                "email": self.email,
                "password": self.password,
            },
            name="POST /login",
            allow_redirects=True,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Login sikertelen: {response.status_code}")

    @task(4)
    def browse_index(self):
        sort = random.choice(["date", "name"])
        direction = random.choice(["asc", "desc"])

        with self.client.get(
            f"/?sort={sort}&dir={direction}",
            name="GET /?sort&dir",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Főoldal lekérés sikertelen: {response.status_code}")

    @task(2)
    def upload_photo(self):
        photo_name = f"Locust kép {uuid.uuid4().hex[:8]}"
        filename = f"{uuid.uuid4().hex}.jpg"

        fake_jpeg = (
            b"\xff\xd8\xff\xe0"
            + b"JFIF\x00"
            + bytes(random.getrandbits(8) for _ in range(4096))
            + b"\xff\xd9"
        )

        files = {
            "file": (filename, fake_jpeg, "image/jpeg")
        }

        data = {
            "name": photo_name
        }

        with self.client.post(
            "/upload",
            data=data,
            files=files,
            name="POST /upload",
            allow_redirects=True,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                photo_id = self._extract_latest_photo_id(response.text)
                if photo_id:
                    self.owned_photo_ids.append(photo_id)
                response.success()
            else:
                response.failure(f"Feltöltés sikertelen: {response.status_code}")

    @task(3)
    def view_photo(self):
        photo_id = None

        if self.owned_photo_ids and random.random() < 0.7:
            photo_id = random.choice(self.owned_photo_ids)
        else:
            photo_id = random.randint(1, 30)

        with self.client.get(
            f"/photo/{photo_id}",
            name="GET /photo/[id]",
            catch_response=True,
        ) as response:
            if response.status_code in (200, 404):
                response.success()
            else:
                response.failure(f"Fotó megnyitás sikertelen: {response.status_code}")

    @task(1)
    def delete_own_photo(self):
        if not self.owned_photo_ids:
            return

        photo_id = random.choice(self.owned_photo_ids)

        with self.client.post(
            f"/delete/{photo_id}",
            name="POST /delete/[id]",
            allow_redirects=True,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                try:
                    self.owned_photo_ids.remove(photo_id)
                except ValueError:
                    pass
                response.success()
            else:
                response.failure(f"Törlés sikertelen: {response.status_code}")

    def _extract_latest_photo_id(self, html: str):
        matches = re.findall(r'/photo/(\\d+)', html)
        if matches:
            try:
                return int(matches[-1])
            except ValueError:
                return None
        return None