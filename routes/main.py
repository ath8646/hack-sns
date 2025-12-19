from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from db_config import supabase

main_bp = Blueprint('main', __name__)



# routes/main.py

# routes/main.py

@main_bp.route('/')
def index():
    # 1. 갤러리 목록 가져오기
    try:
        official_galleries = supabase.table("galleries").select("*").eq("is_official", True).order("id").execute().data
        rec_galleries = supabase.table("galleries").select("*").eq("is_official", False).order("id", desc=True).limit(3).execute().data
    except:
        official_galleries = []
        rec_galleries = []

    gallery_id = request.args.get('g_id', '0')
    query_str = request.args.get('q', '')
    input_pw = request.args.get('pw')

    gallery_name = "📂 전체 게시글"
    searched_galleries = []
    
    # 2. 보안 갤러리 잠금 로직 & 갤러리 정보
    show_lock_screen = False
    gallery_info = None

    if gallery_id and gallery_id != '0':
        try:
            g_res = supabase.table("galleries").select("*").eq("id", gallery_id).single().execute()
            if g_res.data:
                gallery_info = g_res.data
                gallery_name = f"📁 {gallery_info['name']}"
                
                # 보안 갤러리 체크
                if gallery_info.get('is_secure'):
                    # DB에 저장된 실제 비밀번호
                    real_pw = gallery_info.get('password')
                    
                    # 세션에 저장된 (이전에 입력한) 비밀번호 확인
                    session_pw = session.get(f'access_pw_{gallery_id}')

                    # 1) 방금 비밀번호를 입력하고 들어온 경우
                    if input_pw:
                        if input_pw == real_pw:
                            session[f'access_pw_{gallery_id}'] = input_pw # 🔥 비밀번호 자체를 세션에 저장
                            return redirect(url_for('main.index', g_id=gallery_id))
                        else:
                            return "<script>alert('비밀번호가 틀렸습니다!'); history.back();</script>"
                    
                    # 2) 세션 비밀번호와 실제 비밀번호가 다르면 잠금 (비번 바뀌면 튕겨냄)
                    if session_pw != real_pw:
                        show_lock_screen = True
                        
        except Exception as e:
            print(f"Gallery Info Error: {e}")

    # 3. 게시글 데이터 가져오기
    posts = []
    top_posts = []
    notices = []

    try:
        # 🔒 잠금 상태가 아닐 때만 게시글 로드
        if not show_lock_screen:
            query = supabase.table("posts").select("*, users(username, is_admin, grade), galleries(name, creator_id, is_secure)").order("id", desc=True)
            
            if query_str:
                query = query.ilike("title", f"%{query_str}%")
                gallery_name = f"🔍 '{query_str}' 검색 결과"
                searched_galleries = supabase.table("galleries").select("*").ilike("name", f"%{query_str}%").execute().data
            
            if gallery_id and gallery_id != '0':
                # 특정 갤러리 안에서는 그 갤러리 글만 봄
                query = query.eq("gallery_id", gallery_id)
            else:
                # 🔥 [핵심] 전체보기(0) 일 때는 "보안 갤러리"의 글을 제외함!
                # 1. 보안 갤러리들의 ID 목록을 가져옴
                secure_g_res = supabase.table("galleries").select("id").eq("is_secure", True).execute()
                secure_ids = [g['id'] for g in secure_g_res.data]
                
                # 2. posts 쿼리에서 해당 ID들을 제외 (.not_.in_)
                if secure_ids:
                    query = query.not_.in_("gallery_id", secure_ids)
            
            posts = query.limit(7).execute().data

        # 인기글 & 공지사항
        # 🔥 인기글에서도 보안 갤러리 글은 제외해야 함
        top_query = supabase.table("posts").select("*, users(username, is_admin, grade), galleries(name, is_secure)").order("view_count", desc=True)
        
        # 보안 갤러리 제외 로직 동일 적용
        secure_g_res = supabase.table("galleries").select("id").eq("is_secure", True).execute()
        secure_ids = [g['id'] for g in secure_g_res.data]
        if secure_ids:
            top_query = top_query.not_.in_("gallery_id", secure_ids)
            
        top_posts = top_query.limit(3).execute().data
        notices = supabase.table("notices").select("*").order("id", desc=True).execute().data

    except Exception as e:
        print(f"Index Data Error: {e}")

    return render_template('index.html', 
                           posts=posts, 
                           top_posts=top_posts, 
                           notices=notices, 
                           galleries=official_galleries, 
                           rec_galleries=rec_galleries, 
                           searched_galleries=searched_galleries, 
                           gallery_name=gallery_name,
                           is_locked=show_lock_screen,
                           gallery_info=gallery_info)
# 갤러리 더보기 API 추가
# routes/main.py

@main_bp.route('/api/load_more_galleries')
def load_more_galleries():
    offset = int(request.args.get('offset', 0))
    limit = 6  # 한 번에 더 많이 보이게 3 -> 6으로 늘림
    q = request.args.get('q', '') # 검색어 받기

    try:
        # 기본 쿼리: 비공식 갤러리만
        query = supabase.table("galleries").select("*").eq("is_official", False).order("id", desc=True)
        
        # 검색어가 있으면 필터링 추가
        if q:
            query = query.ilike("name", f"%{q}%")
            
        res = query.range(offset, offset + limit - 1).execute()
        return jsonify(res.data)
    except Exception as e:
        print(f"Gallery load error: {e}")
        return jsonify([])
@main_bp.route('/post/<int:post_id>')
def post_detail(post_id):
    try:
        post_res = supabase.table("posts").select("*, users(username, is_admin, grade)").eq("id", post_id).execute()
        if not post_res.data: return "글이 삭제되었거나 없습니다."
        post = post_res.data[0]

        if 't' not in request.args:
            new_views = post.get('view_count', 0) + 1
            supabase.table("posts").update({"view_count": new_views}).eq("id", post_id).execute()
            post['view_count'] = new_views

        votes_res = supabase.table("likes").select("*").eq("post_id", post_id).execute()
        votes = votes_res.data
        like_count = len([v for v in votes if v['vote_type'] == 'like'])
        dislike_count = len([v for v in votes if v['vote_type'] == 'dislike'])
        my_vote = next((v['vote_type'] for v in votes if v.get('user_id') == session.get('user_id')), None)
        
        comment_res = supabase.table("comments").select("*, users(username, is_admin, grade)").eq("post_id", post_id).order("id").execute()
        all_comments = comment_res.data
        
        # 댓글 좋아요 개수 세기
        for cmt in all_comments:
            l_res = supabase.table("comment_likes").select("*", count='exact', head=True).eq("comment_id", cmt['id']).eq("vote_type", "like").execute()
            d_res = supabase.table("comment_likes").select("*", count='exact', head=True).eq("comment_id", cmt['id']).eq("vote_type", "dislike").execute()
            cmt['like_count'] = l_res.count
            cmt['dislike_count'] = d_res.count

        parents = [c for c in all_comments if c['parent_id'] is None]
        replies = [c for c in all_comments if c['parent_id'] is not None]
        
        return render_template('detail.html', post=post, parents=parents, replies=replies, like_count=like_count, dislike_count=dislike_count, my_vote=my_vote)
    except Exception as e:
        print(f"Detail Error: {e}")
        return f"오류 발생: {e}", 500

# 게시글 좋아요
@main_bp.route('/vote/<int:post_id>/<vote_type>')
def vote_post(post_id, vote_type):
    if 'user_id' not in session: return jsonify({'error': 'login required'}), 401
    user_id = session['user_id']
    
    try:
        existing = supabase.table("likes").select("*").eq("user_id", user_id).eq("post_id", post_id).execute().data
        if existing:
            if existing[0]['vote_type'] == vote_type:
                supabase.table("likes").delete().eq("user_id", user_id).eq("post_id", post_id).execute()
            else:
                supabase.table("likes").update({"vote_type": vote_type}).eq("user_id", user_id).eq("post_id", post_id).execute()
        else:
            supabase.table("likes").insert({"user_id": user_id, "post_id": post_id, "vote_type": vote_type}).execute()
            
        votes = supabase.table("likes").select("*").eq("post_id", post_id).execute().data
        like_count = len([v for v in votes if v['vote_type'] == 'like'])
        dislike_count = len([v for v in votes if v['vote_type'] == 'dislike'])
        my_vote = next((v['vote_type'] for v in votes if v['user_id'] == user_id), None)
        
        return jsonify({'like_count': like_count, 'dislike_count': dislike_count, 'my_vote': my_vote})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 갤러리 생성
# routes/main.py

# 1. 갤러리 생성 (보안 옵션 추가)
# 1. 갤러리 생성
@main_bp.route('/create_gallery', methods=['POST'])
def create_gallery():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    try:
        is_secure = request.form.get('is_secure') == 'on'
        password = request.form.get('password') if is_secure else None

        supabase.table("galleries").insert({
            "name": request.form.get('name'), 
            "description": request.form.get('description'),
            "creator_id": session['user_id'],
            "is_official": False,
            "is_secure": is_secure,
            "password": password
        }).execute()
        # 🔥 tab='manage' 추가: 관리 탭으로 이동
        return redirect(url_for('auth.settings', msg="갤러리가 생성되었습니다!", tab="manage"))
    except Exception as e:
        print(f"생성 실패: {e}")
        return redirect(url_for('auth.settings', msg=f"생성 실패: {e}", tab="create"))

# 2. 갤러리 삭제
# routes/main.py

@main_bp.route('/gallery/delete/<int:gallery_id>')
def delete_gallery(gallery_id):
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    try:
        # 1. 본인이 만든 갤러리인지 확인
        g = supabase.table("galleries").select("*").eq("id", gallery_id).single().execute().data
        if not g or str(g['creator_id']) != str(session['user_id']):
            return redirect(url_for('auth.settings', msg="삭제 권한이 없습니다."))
        
        # 🔥 [추가된 부분] 갤러리에 속한 게시글들을 먼저 삭제해야 함 (외래키 오류 방지)
        # 주의: 게시글에 달린 댓글이 있을 경우, 댓글 삭제 로직도 필요하거나 DB에서 CASCADE 설정이 되어 있어야 함
        supabase.table("posts").delete().eq("gallery_id", gallery_id).execute()

        # 2. 갤러리 삭제
        supabase.table("galleries").delete().eq("id", gallery_id).execute()
        
        # 3. 관리 탭으로 이동
        return redirect(url_for('auth.settings', msg="갤러리가 삭제되었습니다.", tab="manage"))
    except Exception as e:
        print(f"삭제 오류: {e}")
        # 만약 댓글 때문에 또 오류가 난다면 메시지로 알려줌
        if '23503' in str(e) and 'comments' in str(e):
             return redirect(url_for('auth.settings', msg="게시글에 댓글이 있어 삭제할 수 없습니다. 관리자에게 문의하세요.", tab="manage"))
        return redirect(url_for('auth.settings', msg=f"오류: {e}", tab="manage"))

# 3. 비밀번호 변경
@main_bp.route('/gallery/update_pw', methods=['POST'])
def update_gallery_pw():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    try:
        g_id = request.form.get('gallery_id')
        new_pw = request.form.get('new_password')
        
        supabase.table("galleries").update({"password": new_pw}).eq("id", g_id).eq("creator_id", session['user_id']).execute()
        # 🔥 tab='manage' 추가
        return redirect(url_for('auth.settings', msg="비밀번호가 변경되었습니다.", tab="manage"))
    except Exception as e:
        return redirect(url_for('auth.settings', msg=f"오류: {e}", tab="manage"))

# 🔥 [수정됨] 댓글 삭제 - 왜 권한이 없는지 터미널에 찍어줍니다.
@main_bp.route('/comment/delete/<int:comment_id>')
def delete_comment(comment_id):
    if 'user_id' not in session: 
        return "로그인 필요", 401
    
    try:
        comment = supabase.table("comments").select("*").eq("id", comment_id).single().execute().data
        if not comment: return "삭제할 댓글 없음", 404
        
        my_id = str(session.get('user_id')).strip()
        writer_id = str(comment.get('user_id')).strip()

        # 터미널에서 아래 내용을 확인하세요!
        print(f"\n--- 삭제 권한 확인 ---")
        print(f"내 아이디: {my_id}")
        print(f"작성자ID: {writer_id}")
        print(f"관리자여부: {session.get('is_admin')}")
        print(f"결과: {my_id == writer_id}")
        print(f"----------------------\n")

        if my_id == writer_id or session.get('is_admin'):
            supabase.table("comments").delete().eq("id", comment_id).execute()
            return "ok", 200
        else:
            return "권한 없음", 403
    except Exception as e:
        print(f"❌ 댓글 삭제 서버 에러: {e}")
        return str(e), 500

# 댓글 좋아요
# 댓글 투표 (좋아요/싫어요)
@main_bp.route('/comment/vote/<int:comment_id>/<vote_type>')
def vote_comment(comment_id, vote_type):
    if 'user_id' not in session: 
        return jsonify({'error': '로그인이 필요합니다.'}), 401
    
    # 🔥 사용자 아이디를 확실히 숫자(int)로 변환합니다.
    user_id = int(session['user_id']) 
    
    try:
        # 기존 투표 확인
        res = supabase.table("comment_likes").select("*").eq("user_id", user_id).eq("comment_id", comment_id).execute()
        existing = res.data
        
        if existing:
            if existing[0]['vote_type'] == vote_type:
                supabase.table("comment_likes").delete().eq("user_id", user_id).eq("comment_id", comment_id).execute()
            else:
                supabase.table("comment_likes").update({"vote_type": vote_type}).eq("user_id", user_id).eq("comment_id", comment_id).execute()
        else:
            # 새로 투표 저장
            supabase.table("comment_likes").insert({
                "user_id": user_id, 
                "comment_id": comment_id, 
                "vote_type": vote_type
            }).execute()
            
        return "ok", 200

    except Exception as e:
        print(f"❌ 투표 에러: {e}")
        return str(e), 500
    
# routes/main.py 에 추가

@main_bp.route('/api/load_more')
def load_more_posts():
    offset = int(request.args.get('offset', 0))
    limit = 7
    gallery_id = request.args.get('g_id', '0')
    
    try:
        query = supabase.table("posts").select("*, users(username, grade), galleries(name, creator_id, is_secure)").order("id", desc=True)
        
        if gallery_id and gallery_id != '0':
            query = query.eq("gallery_id", gallery_id)
        else:
            # 🔥 전체보기 더보기 시에도 보안 갤러리 제외
            secure_g_res = supabase.table("galleries").select("id").eq("is_secure", True).execute()
            secure_ids = [g['id'] for g in secure_g_res.data]
            if secure_ids:
                query = query.not_.in_("gallery_id", secure_ids)
            
        posts = query.range(offset, offset + limit - 1).execute().data
        return jsonify(posts)
    except Exception as e:
        print(f"Load more error: {e}")
        return jsonify([])
    

@main_bp.route('/showcase')
def showcase():
    return render_template('showcase.html')


@main_bp.route('/api/notifications')
def get_notifications():
    if 'user_id' not in session: return jsonify([])
    # 읽지 않은 알림 최신순 5개
    res = supabase.table("notifications").select("*")\
        .eq("user_id", session['user_id'])\
        .eq("is_read", False)\
        .order("id", desc=True).limit(5).execute()
    return jsonify(res.data)

@main_bp.route('/api/notifications/read', methods=['POST'])
def read_notifications():
    if 'user_id' in session:
        supabase.table("notifications").update({"is_read": True})\
            .eq("user_id", session['user_id']).execute()
    return "OK", 200