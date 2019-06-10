from flask import render_template
from flask import current_app as app
from .models import db, User


@app.route('/new', methods=['GET'])
def entry():
    """Endpoint to create a user."""
    new_user = User(username='test',
                    email='test@example.com',
                    )
    try:
        db.session.add(new_user)
        db.session.commit()
    except:
        pass
    users = User.query.all()
    return render_template('users.html', users=users, title="Show Users")
