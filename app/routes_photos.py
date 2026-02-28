import os
from uuid import uuid4
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from . import db
from .models import Photo
from .s3 import upload_fileobj, delete_object, presigned_get_url
import logging

photos_bp = Blueprint("photos", __name__)

ALLOWED_EXT = {"jpg", "jpeg", "png", "webp"}

def allowed(filename: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXT

@photos_bp.get("/")
def index():
    sort = request.args.get("sort", "date")
    direction = request.args.get("dir", "desc")
    try:
        q = Photo.query
        if sort == "name":
            order_col = Photo.name
        else:
            order_col = Photo.upload_dt

        if direction == "asc":
            q = q.order_by(order_col.asc())
        else:
            q = q.order_by(order_col.desc())

        photos = q.all()
    except Exception:
        logging.exception("Index DB query failed")
        photos=[]
    return render_template("index.html", photos=photos, sort=sort, direction=direction)

@photos_bp.post("/upload")
@login_required
def upload():
    name = request.form.get("name", "").strip()
    file = request.files.get("file")

    if not name or len(name) > 40:
        flash("A név kötelező és max 40 karakter lehet.")
        return redirect(url_for("photos.index"))

    if not file or file.filename == "":
        flash("Válassz fájlt.")
        return redirect(url_for("photos.index"))

    if not allowed(file.filename):
        flash("Csak jpg/jpeg/png/webp engedélyezett.")
        return redirect(url_for("photos.index"))

    bucket = os.environ["S3_BUCKET"]
    ext = file.filename.rsplit(".", 1)[1].lower()
    key = f"user_{current_user.id}/{uuid4().hex}.{ext}"

    upload_fileobj(file, bucket=bucket, key=key, content_type=file.mimetype)

    p = Photo(
        user_id=current_user.id,
        name=name,
        upload_dt=datetime.utcnow(),
        s3_key=key
    )
    db.session.add(p)
    db.session.commit()

    flash("Feltöltve.")
    return redirect(url_for("photos.index"))

@photos_bp.get("/photo/<int:photo_id>")
def view_photo(photo_id: int):
    p = Photo.query.get_or_404(photo_id)
    bucket = os.environ["S3_BUCKET"]
    url = presigned_get_url(bucket, p.s3_key, expires_sec=300)
    return render_template("photo.html", photo=p, image_url=url)

@photos_bp.post("/delete/<int:photo_id>")
@login_required
def delete(photo_id: int):
    p = Photo.query.get_or_404(photo_id)
    if p.user_id != current_user.id:
        abort(403)

    bucket = os.environ["S3_BUCKET"]
    delete_object(bucket, p.s3_key)

    db.session.delete(p)
    db.session.commit()
    flash("Törölve.")
    return redirect(url_for("photos.index"))