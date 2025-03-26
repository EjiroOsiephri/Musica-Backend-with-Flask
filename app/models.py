from app import db, bcrypt

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)
    google_id = db.Column(db.String(255), unique=True, nullable=True)
    facebook_id = db.Column(db.String(255), unique=True, nullable=True)
    profile_picture = db.Column(db.String(256), nullable=True)  # ✅ Moved profile picture here

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)


class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    track_id = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    artist = db.Column(db.String(255), nullable=False)
    album = db.Column(db.String(255), nullable=False)  # ✅ Album field
    duration = db.Column(db.String(20), nullable=False)  # ✅ Duration field
    image = db.Column(db.String(255), nullable=False)  # ✅ Made image non-nullable
    preview = db.Column(db.String(255), nullable=False)  # ✅ Made preview non-nullable
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())  # ✅ Timestamp

    user = db.relationship('User', backref=db.backref('playlists', lazy=True))
