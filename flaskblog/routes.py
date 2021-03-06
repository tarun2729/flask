import os
import secrets
from PIL import Image
from flask import render_template,url_for,flash,redirect,request,abort
from flaskblog import app,db,bcrypt,mail
from flaskblog.forms import RegistrationForm,LoginForm,UpdateAccountForm,Postform,RequestResetform,ResetPasswordform
from flaskblog.models import user,Post
from flask_login import login_user,current_user,logout_user,login_required
from flask_mail import Message

@app.route("/")
@app.route("/home")
def home():
    posts=Post.query.all()

    return render_template('home.html',posts=posts)
@app.route("/about")
def about():
    return render_template('about.html',title='about')
@app.route("/register",methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form=RegistrationForm()
    if form.validate_on_submit():
        hashed_password=bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        User=user(username=form.username.data,email=form.email.data,password=hashed_password)
        db.session.add(User)
        db.session.commit()
        flash('Your account is created!You are able to login now','success')
        return redirect(url_for('login'))
    return render_template('register.html',title='Register',form=form)
@app.route("/login",methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form=LoginForm()
    if form.validate_on_submit():
        u=user.query.filter_by(email=form.email.data).first()
        if u and bcrypt.check_password_hash(u.password,form.password.data):
            login_user(u,remember=form.remember.data)
            next_page=request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Your logged in was unsuccessful.Please check username and password','danger')
    return render_template('login.html',title='Login',form=form)
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))
def save_picture(form_picture):
    random_hex=secrets.token_hex(8)
    _,f_ext=os.path.splitext(form_picture,filename)
    picture_fn=random_hex+f_ext
    picture_path=os.path.join(app.root_path,'static/profile_pics',picture_fn)
    output_size=(125,125)
    i=Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)


    return picture_fn

@app.route("/account",methods=['GET','POST'])
@login_required
def account():
    form=UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file=save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username=form.username.data
        current_user.email=form.email.data
        db.session.commit()
        flash('Your account has been updated!','success')
        return redirect(url_for('account'))
    elif request.method=='GET':
        form.username.data=current_user.username
        form.email.data=current_user.email
    image_file=url_for('static',filename='profile_pics/' + current_user.image_file)
    return render_template('account.html',title='Account',image_file=image_file,form=form)

@app.route("/post/new",methods=['GET','POST'])
@login_required
def new_post():
    form = Postform()
    if form.validate_on_submit():
        post=Post(title=form.title.data,content=form.content.data,author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New post',legend='New post',form=form)

@app.route("/post/<int:post_id>",methods=['GET','POST'])
@login_required
def post(post_id):
    post=Post.query.get_or_404(post_id)
    return render_template('post.html',title=post.title,post=post)

@app.route("/post/<int:post_id>/update",methods=['GET','POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author!=current_user:
        abort(403)
    form=Postform()
    if form.validate_on_submit():
        post.title=form.title.data
        post.content=form.content.data
        db.session.commit()
        flash('Your post has been Updated!','success')
    elif request.method == "GET":
        form.title.data=post.title
        form.content.data=post.content
    return render_template('create_post.html', title='Update post',legend='Update post',form=form)


@app.route("/post/<int:post_id>/delete",methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!','success')
    return redirect(url_for('home'))

def send_reset_email(u):
    token=u.get_reset_token()
    msg=Message('Password reset Request',sender='tarunsaipanja@gmail.com',recipients=[u.email])
    msg.body=f'''To reset your password,Visit the following link:
    {url_for('reset_token',token=token,_external=True)}
    
    if you did not make this request then simply ignore this email and no change'''
    mail.send(msg)

@app.route("/reset_password",methods=['GET','POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetform()
    if form.validate_on_submit():
        u=user.query.filter_by(email=form.email.data).first()
        send_reset_email(u)
        flash('An email has been send with instructions to rest your password')
        return redirect(url_for('login'))
    return render_template('reset_request.html',title='Reset Password',form=form)

@app.route("/reset_password/<token>",methods=['GET','POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    u=user.verify_reset_token(token)
    if u is None:
        flash('That is an invalid or expired token','warning')
        return redirect(url_for('reset_request'))
    form=ResetPasswordform()
    if form.validate_on_submit():
        hashed_password=bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        u.password=hashed_password
        db.session.commit()
        flash('Your account is created!You are able to login now','success')
        return redirect(url_for('login'))
    return render_template('reset_token.html',title='Reset Password',form=form)

