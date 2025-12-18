from flask import Flask, render_template, request, redirect, url_for, session
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = 'hack_demo_secret_key'  # 세션 암호화 키

# ==========================================
# [설정] Supabase 키를 여기에 붙여넣으세요!
# ==========================================
SUPABASE_URL = "https://porctgadcosjzgpkxiqw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBvcmN0Z2FkY29zanpncGt4aXF3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjYwMzc4MjYsImV4cCI6MjA4MTYxMzgyNn0.QmB0BnyLAYY0Rt3-fffExHQt4BGgWWr7USc5V9qbA2c"

# Supabase 클라이언트 연결
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/')
def index():
    # 게시글 가져오기 (작성자 정보 포함)
    try:
        response = supabase.table("posts").select("*, users(username)").order("id", desc=True).execute()
        posts = response.data
    except Exception as e:
        print(f"DB Error: {e}")
        posts = []
    return render_template('index.html', posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Supabase에서 유저 찾기
        response = supabase.table("users").select("*").eq("username", username).eq("password", password).execute()
        
        if response.data:
            user = response.data[0]
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            error = "아이디 또는 비밀번호가 틀렸습니다."
            
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            supabase.table("users").insert({"username": username, "password": password}).execute()
            return redirect(url_for('login'))
        except Exception as e:
            return f"오류 발생 (이미 있는 아이디일 수 있습니다): {e}"
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/write', methods=['POST'])
def write():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    title = request.form['title']
    content = request.form['content']
    
    supabase.table("posts").insert({
        "title": title,
        "content": content,
        "author_id": session['user_id']
    }).execute()
    
    return redirect(url_for('index'))

@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit(post_id):
    if 'user_id' not in session: return redirect(url_for('login'))

    # 게시글 정보 가져오기
    response = supabase.table("posts").select("*").eq("id", post_id).execute()
    if not response.data: return "글이 없습니다."
    post = response.data[0]

    # 권한 체크 (본인 글만 수정 가능)
    if post['author_id'] != session['user_id']:
        return "수정 권한이 없습니다!", 403

    if request.method == 'POST':
        supabase.table("posts").update({
            "title": request.form['title'],
            "content": request.form['content']
        }).eq("id", post_id).execute()
        return redirect(url_for('index'))
        
    return render_template('edit.html', post=post)

@app.route('/delete/<int:post_id>')
def delete(post_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    # 본인 확인 후 삭제 (author_id까지 조건에 넣어 안전하게 처리)
    supabase.table("posts").delete().eq("id", post_id).eq("author_id", session['user_id']).execute()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)