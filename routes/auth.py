import re
from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from db_config import supabase

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']; password = request.form['password']
        if username == 'ADMIN' and password == 'testpassword':
            session['user_id'] = 0; session['username'] = '관리자(ADMIN)'; session['is_admin'] = True; session['grade'] = '관리자'
            return redirect(url_for('admin.admin_list'))
        res = supabase.table("users").select("*").eq("username", username).execute()
        if res.data and check_password_hash(res.data[0]['password'], password):
            user = res.data[0]
            session['user_id'] = user['id']; session['username'] = user['username']; session['is_admin'] = user.get('is_admin', False)
            session['grade'] = user.get('grade') if user.get('grade') else '일반'
            return redirect(url_for('main.index'))
        else: return render_template('login.html', error="아이디 또는 비밀번호 오류")
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    username_error = None; password_error = None
    if request.method == 'POST':
        username = request.form['username']; password = request.form['password']
        if not re.match(r'^[a-zA-Z가-힣0-9]+$', username):
            username_error = "아이디는 영어, 한글, 숫자만 가능합니다!"
        elif not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            password_error = "특수문자 필수!"
        else:
            try:
                supabase.table("users").insert({"username": username, "password": generate_password_hash(password)}).execute()
                return redirect(url_for('auth.login'))
            except: username_error = "이미 사용 중인 아이디입니다."
    return render_template('register.html', username_error=username_error, password_error=password_error)

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))

@auth_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    # URL 파라미터 받기 (메시지 처리용)
    msg = request.args.get('msg')
    
    if request.method == 'POST':
        if request.form.get('action') == 'change_pw':
            cur = request.form['current_password']
            new = request.form['new_password']
            
            try:
                user = supabase.table("users").select("*").eq("id", session['user_id']).execute().data[0]
                if not check_password_hash(user['password'], cur): 
                    msg = "❌ 현재 비밀번호가 틀렸습니다."
                elif not re.search(r'[!@#$%^&*(),.?":{}|<>]', new): 
                    msg = "❌ 특수문자를 포함해야 합니다."
                else:
                    supabase.table("users").update({"password": generate_password_hash(new)}).eq("id", session['user_id']).execute()
                    msg = "✅ 비밀번호 변경 완료!"
            except Exception as e:
                msg = f"❌ 오류 발생: {e}"

    # 🔥 [수정됨] 내가 만든 갤러리만 가져오기
    try:
        user_id = session['user_id']
        # .eq("creator_id", user_id) <- 이 부분이 핵심입니다! (작성자가 나인 것만 필터링)
        my_galleries = supabase.table("galleries").select("*").eq("creator_id", user_id).order("id", desc=True).execute().data
    except Exception as e:
        print(f"갤러리 로드 에러: {e}")
        my_galleries = []

    return render_template('settings.html', msg=msg, my_galleries=my_galleries)