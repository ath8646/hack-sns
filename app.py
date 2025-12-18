import re
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from supabase import create_client, Client
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'hack_sns_secure_key'

# [Supabase 설정]
SUPABASE_URL = "https://porctgadcosjzgpkxiqw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBvcmN0Z2FkY29zanpncGt4aXF3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjYwMzc4MjYsImV4cCI6MjA4MTYxMzgyNn0.QmB0BnyLAYY0Rt3-fffExHQt4BGgWWr7USc5V9qbA2c"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ===========================
# [메인 & 게시판]
# ===========================
@app.route('/')
def index():
    try:
        # view_count도 같이 가져옴
        response = supabase.table("posts").select("*, users(username)").order("id", desc=True).execute()
        posts = response.data
    except Exception as e:
        print(e)
        posts = []
    return render_template('index.html', posts=posts)

# ===========================
# [글 상세 보기 (조회수 & 좋아요)]
# ===========================
@app.route('/post/<int:post_id>')
def post_detail(post_id):
    # 1. 글 정보 가져오기
    post_res = supabase.table("posts").select("*, users(username)").eq("id", post_id).execute()
    if not post_res.data: return "글이 삭제되었거나 없습니다."
    post = post_res.data[0]

    # 2. 🔥 조회수 1 증가 로직 (새로고침 할 때마다 오름) 🔥
    new_views = post.get('view_count', 0) + 1
    supabase.table("posts").update({"view_count": new_views}).eq("id", post_id).execute()
    post['view_count'] = new_views # 화면에도 반영

    # 3. 🔥 좋아요/싫어요 개수 계산 🔥
    votes_res = supabase.table("likes").select("*").eq("post_id", post_id).execute()
    votes = votes_res.data
    
    like_count = len([v for v in votes if v['vote_type'] == 'like'])
    dislike_count = len([v for v in votes if v['vote_type'] == 'dislike'])
    
    # 4. 내가 뭘 눌렀는지 확인 (버튼 색칠용)
    my_vote = None
    if 'user_id' in session:
        for v in votes:
            if v['user_id'] == session['user_id']:
                my_vote = v['vote_type']
                break
    
    # 5. 댓글 가져오기
    comment_res = supabase.table("comments").select("*, users(username)").eq("post_id", post_id).order("id").execute()
    all_comments = comment_res.data
    parents = [c for c in all_comments if c['parent_id'] is None]
    replies = [c for c in all_comments if c['parent_id'] is not None]
    
    return render_template('detail.html', post=post, parents=parents, replies=replies, 
                           like_count=like_count, dislike_count=dislike_count, my_vote=my_vote)

# ===========================
# [투표 기능 (좋아요/싫어요)]
# ===========================
@app.route('/vote/<int:post_id>/<vote_type>')
def vote(post_id, vote_type):
    if 'user_id' not in session: 
        return redirect(url_for('login')) # 로그인 안했으면 로그인 창으로
    
    user_id = session['user_id']
    
    # 기존 투표 확인
    existing = supabase.table("likes").select("*").eq("user_id", user_id).eq("post_id", post_id).execute()
    
    if existing.data:
        # 이미 투표한 기록이 있는 경우
        old_vote = existing.data[0]['vote_type']
        if old_vote == vote_type:
            # 같은 걸 또 누르면 -> 취소 (삭제)
            supabase.table("likes").delete().eq("id", existing.data[0]['id']).execute()
        else:
            # 다른 걸 누르면 -> 변경 (Update)
            supabase.table("likes").update({"vote_type": vote_type}).eq("id", existing.data[0]['id']).execute()
    else:
        # 투표한 적 없으면 -> 추가 (Insert)
        supabase.table("likes").insert({
            "user_id": user_id, "post_id": post_id, "vote_type": vote_type
        }).execute()
        
    return redirect(url_for('post_detail', post_id=post_id))

# ===========================
# [나머지 기능 (기존 유지)]
# ===========================
# ... 로그인, 회원가입, 글쓰기, 수정, 삭제, 관리자 등 기존 코드 그대로 유지 ...
# (아래 코드는 생략되었으니 기존 app.py의 나머지 부분을 꼭 유지해주세요!)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'ADMIN' and password == 'testpassword':
            session['user_id'] = 0; session['username'] = '관리자(ADMIN)'; session['is_admin'] = True
            return redirect(url_for('admin_list'))
        res = supabase.table("users").select("*").eq("username", username).execute()
        user = res.data[0] if res.data else None
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']; session['username'] = user['username']; session.pop('is_admin', None)
            return redirect(url_for('index'))
        else: return render_template('login.html', error="아이디 또는 비밀번호가 틀렸습니다.")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    username_error = None; password_error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            password_error = "특수문자 필수!"; return render_template('register.html', username_error=username_error, password_error=password_error, username=username)
        hashed_pw = generate_password_hash(password)
        try:
            supabase.table("users").insert({"username": username, "password": hashed_pw}).execute()
            return redirect(url_for('login'))
        except: username_error = "이미 사용 중인 아이디입니다."
    return render_template('register.html', username_error=username_error, password_error=password_error)

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('index'))

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session: return redirect(url_for('login'))
    msg = None
    if request.method == 'POST':
        current_pw = request.form['current_password']; new_pw = request.form['new_password']
        res = supabase.table("users").select("*").eq("id", session['user_id']).execute(); user = res.data[0]
        if not check_password_hash(user['password'], current_pw): msg = "❌ 현재 비밀번호 오류"
        elif not re.search(r'[!@#$%^&*(),.?":{}|<>]', new_pw): msg = "❌ 특수문자 필수"
        else:
            new_hashed = generate_password_hash(new_pw)
            supabase.table("users").update({"password": new_hashed}).eq("id", session['user_id']).execute()
            msg = "✅ 변경 완료!"
    return render_template('settings.html', msg=msg)

@app.route('/write', methods=['POST'])
def write():
    if 'user_id' not in session: return redirect(url_for('login'))
    title = request.form['title']; content = request.form['content']; file = request.files.get('file'); image_url = None
    if file and file.filename != '':
        try:
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            file_path = f"{session['user_id']}_{timestamp}_{filename}"
            file_content = file.read()
            supabase.storage.from_("images").upload(file_path, file_content, {"content-type": file.content_type})
            image_url = supabase.storage.from_("images").get_public_url(file_path)
        except Exception as e: print(f"이미지 업로드 실패: {e}")
    supabase.table("posts").insert({"title": title, "content": content, "image_url": image_url, "author_id": session['user_id']}).execute()
    return redirect(url_for('index'))

@app.route('/comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    content = request.form['content']; parent_id = request.form.get('parent_id')
    if parent_id == '': parent_id = None
    data = {"content": content, "post_id": post_id, "author_id": session['user_id']}
    if parent_id: data['parent_id'] = int(parent_id)
    supabase.table("comments").insert(data).execute()
    return redirect(url_for('post_detail', post_id=post_id))

@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit(post_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    res = supabase.table("posts").select("*").eq("id", post_id).execute()
    if not res.data: return "글 없음"
    post = res.data[0]
    if post['author_id'] != session['user_id'] and not session.get('is_admin'): return "권한 없음", 403
    if request.method == 'POST':
        supabase.table("posts").update({"title": request.form['title'], "content": request.form['content']}).eq("id", post_id).execute()
        if session.get('is_admin'): return redirect(url_for('admin_user_detail', user_id=post['author_id']))
        return redirect(url_for('index'))
    return render_template('edit.html', post=post)

@app.route('/delete/<int:post_id>')
def delete(post_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    res = supabase.table("posts").select("*").eq("id", post_id).execute()
    if not res.data: return redirect(url_for('index'))
    post = res.data[0]
    if post['author_id'] == session['user_id'] or session.get('is_admin'):
        supabase.table("posts").delete().eq("id", post_id).execute()
    if session.get('is_admin'): return redirect(url_for('admin_list'))
    return redirect(url_for('index'))

@app.route('/admin')
def admin_list():
    if not session.get('is_admin'): return redirect(url_for('index'))
    query = request.args.get('q', ''); res = supabase.table("users").select("*").ilike("username", f"%{query}%").order("id").execute() if query else supabase.table("users").select("*").order("id").execute()
    return render_template('admin_list.html', users=res.data, query=query)

@app.route('/admin/user/<int:user_id>', methods=['GET', 'POST'])
def admin_user_detail(user_id):
    if not session.get('is_admin'): return redirect(url_for('index'))
    if request.method == 'POST':
        try: supabase.table("users").update({"username": request.form['username']}).eq("id", user_id).execute()
        except: pass
        return redirect(url_for('admin_user_detail', user_id=user_id))
    user_res = supabase.table("users").select("*").eq("id", user_id).execute(); posts_res = supabase.table("posts").select("*").eq("author_id", user_id).order("id", desc=True).execute()
    return render_template('admin_user_detail.html', user=user_res.data[0], posts=posts_res.data)

@app.route('/admin/delete_user/<int:user_id>')
def admin_delete_user(user_id):
    if not session.get('is_admin'): return "권한 없음", 403
    supabase.table("users").delete().eq("id", user_id).execute(); return redirect(url_for('admin_list'))

@app.route('/admin/update_password/<int:user_id>', methods=['POST'])
def admin_update_password(user_id):
    if not session.get('is_admin'): return "권한 없음", 403
    hashed_pw = generate_password_hash(request.form['new_password'])
    supabase.table("users").update({"password": hashed_pw}).eq("id", user_id).execute()
    return redirect(url_for('admin_user_detail', user_id=user_id))

if __name__ == '__main__':
    app.run(debug=True)