from flask import Blueprint, render_template

views = Blueprint('views', __name__)

#route for the home page
@views.route('/')
def home():
    return render_template('home.html')

#route for the settings page
@views.route('/settings')
def settings():
    return render_template('settings.html')

#route for the login page
@views.route('/login')
def login():
    return render_template('login.html')

#route for the register page
@views.route('/register')
def register():
    
  if current_user.is_authenticated:
        flash('You are already logged in', category='info')
        return redirect(url_for('views.home'))

    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if not username or not email or not password:
            flash('All fields are required', category='error')
            return redirect(url_for('views.register'))

        user = User.query.filter_by(email=email).first()

        if user:
            flash('A user with this email already exists', category='error')
            return redirect(url_for('views.login'))
        else:
            try:
                new_user = User(
                    username=username, 
                    email=email, 
                    password=generate_password_hash(password, method='pbkdf2:sha256')
                )
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user, remember=True)
                flash('Registration successful')
                return redirect(url_for('views.home'))
            except Exception as e:
                db.session.rollback()
                flash('An error occured while trying you register you, please try again')
                print(f"Error: {e}")


    return render_template('register.html', user=current_user)
