import os
from datetime import datetime
from flask import Blueprint, request, redirect, url_for, session, jsonify, render_template
from werkzeug.utils import secure_filename
from db_config import supabase, allowed_file

post_bp = Blueprint('post', __name__)

@post_bp.route('/write', methods=['POST'])
def write():
    if 'user_id' not in session: 
        return redirect(url_for('auth.login'))
    
    title = request.form.get('title')
    content = request.form.get('content')
    external_link = request.form.get('external_link')
    
    # 갤러리 ID 받기
    gallery_id = request.form.get('gallery_id')
    
    # '전체보기(0)' 상태 처리
    if gallery_id == '0':
        gallery_id = None 

    # 1. 파일 업로드 처리
    files = request.files.getlist('file')
    file_urls = []
    
    for file in files:
        if file and file.filename != '' and allowed_file(file.filename):
            try:
                fn = secure_filename(file.filename)
                ts = datetime.now().strftime("%Y%m%d%H%M%S%f")
                fp = f"{session['user_id']}_{ts}_{fn}"
                
                # Supabase에 업로드
                supabase.storage.from_("images").upload(fp, file.read(), {"content-type": file.content_type})
                
                # 업로드된 주소 리스트에 추가
                url = supabase.storage.from_("images").get_public_url(fp)
                file_urls.append(url)
            except Exception as e:
                print(f"파일 업로드 오류: {e}")

    # 2. DB 저장 (업로드 후 실행)
    try:
        supabase.table("posts").insert({
            "title": title, 
            "content": content, 
            "file_urls": file_urls,
            "external_link": external_link,
            "author_id": session['user_id'],
            "gallery_id": gallery_id
        }).execute()
    except Exception as e:
        print(f"글쓰기 실패: {e}")
    
    # 3. 모든 작업이 끝난 후 페이지 이동 (Redirect)
    if gallery_id:
        return redirect(url_for('main.index', g_id=gallery_id))
    else:
        return redirect(url_for('main.index'))
    

@post_bp.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit(post_id):
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    # 1. DB에서 게시글 정보와 갤러리 장(creator_id) 정보를 함께 가져오기
    res = supabase.table("posts").select("*, galleries(creator_id)").eq("id", post_id).execute()
    if not res.data: return "글을 찾을 수 없습니다.", 404
    post = res.data[0]

    # 권한 확인 로직: 작성자 본인 OR 사이트 관리자 OR 해당 갤러리의 주인(갤러리 장)
    is_author = post['author_id'] == session['user_id']
    is_admin = session.get('is_admin')
    is_gallery_master = post.get('galleries') and post['galleries'].get('creator_id') == session['user_id']

    if not (is_author or is_admin or is_gallery_master):
        return "권한 없음", 403

    if request.method == 'POST':
        # (기존 파일 업로드 및 유지 로직 동일)
        keep_files = request.form.getlist('keep_files')
        new_files = request.files.getlist('file')
        new_urls = []
        for file in new_files:
            if file and file.filename != '' and allowed_file(file.filename):
                try:
                    fn = secure_filename(file.filename)
                    ts = datetime.now().strftime("%Y%m%d%H%M%S%f")
                    fp = f"{session['user_id']}_{ts}_{fn}"
                    supabase.storage.from_("images").upload(fp, file.read(), {"content-type": file.content_type})
                    url = supabase.storage.from_("images").get_public_url(fp)
                    new_urls.append(url)
                except Exception as e: 
                    print(f"추가 업로드 오류: {e}")

        final_files = keep_files + new_urls

        # DB 업데이트 (갤러리 정보는 수정하지 않음)
        supabase.table("posts").update({
            "title": request.form['title'],
            "content": request.form['content'],
            "external_link": request.form.get('external_link'),
            "file_urls": final_files
        }).eq("id", post_id).execute()

        return redirect(url_for('main.post_detail', post_id=post_id))

    return render_template('edit.html', post=post)

# routes/post.py

@post_bp.route('/delete/<int:post_id>')
def delete(post_id):
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    gallery_id = request.args.get('g_id', '0')
    
    # 게시글 정보와 함께 갤러리 장(creator_id) 정보 가져오기
    post_res = supabase.table("posts").select("*, galleries(creator_id)").eq("id", post_id).execute()
    
    if post_res.data:
        post = post_res.data[0]
        
        # 권한 확인 로직
        is_author = post['author_id'] == session['user_id']
        is_admin = session.get('is_admin')
        is_gallery_master = post.get('galleries') and post['galleries'].get('creator_id') == session['user_id']

        if is_author or is_admin or is_gallery_master:
            supabase.table("posts").delete().eq("id", post_id).execute()
            
    if gallery_id and gallery_id != '0':
        return redirect(url_for('main.index', g_id=gallery_id))
    else:
        return redirect(url_for('main.index'))

@post_bp.route('/vote/<int:post_id>/<vote_type>')
def vote(post_id, vote_type):
    if 'user_id' not in session: 
        return jsonify({'result': 'fail'}), 401
        
    user_id = session['user_id']
    # 기존 투표 기록 확인
    existing = supabase.table("likes").select("*").eq("user_id", user_id).eq("post_id", post_id).execute()
    
    if existing.data:
        old = existing.data[0]
        if old['vote_type'] == vote_type:
            # 같은 버튼을 다시 누르면 취소
            supabase.table("likes").delete().match({"user_id": user_id, "post_id": post_id}).execute()
            return jsonify({'result': 'success'}) # 취소 시에는 알림 안 보냄
        else:
            # 추천 <-> 비추천 변경
            supabase.table("likes").update({"vote_type": vote_type}).eq("id", old['id']).execute()
    else:
        # 처음 누르는 경우
        supabase.table("likes").insert({"user_id": user_id, "post_id": post_id, "vote_type": vote_type}).execute()
        
    # 🔥 알림 발송 로직 (새로 누르거나 변경했을 때 실행)
    # 추천(like)일 때만 알림을 보냄
    if vote_type == 'like':
        try:
            # 게시글 작성자 ID 가져오기
            post_res = supabase.table("posts").select("author_id").eq("id", post_id).single().execute()
            if post_res.data:
                author_id = post_res.data['author_id']
                
                # 본인의 글이 아닐 때만 알림 생성
                if str(author_id) != str(user_id):
                    supabase.table("notifications").insert({
                        "user_id": author_id,
                        "sender_name": session['username'],
                        "type": "post_like",
                        "target_id": post_id
                    }).execute()
                    print("추천 알림 전송 완료") # 디버깅용
        except Exception as e:
            print(f"추천 알림 생성 오류: {e}")
            
    return jsonify({'result': 'success'})

@post_bp.route('/comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    if 'user_id' not in session: 
        return redirect(url_for('auth.login'))
        
    content = request.form['content']
    parent_id = request.form.get('parent_id') or None
    data = {"content": content, "post_id": post_id, "author_id": session['user_id']}
    
    if parent_id: 
        data['parent_id'] = int(parent_id)
        
    supabase.table("comments").insert(data).execute()
    
    # 🔥 [추가/수정] 댓글 알림 로직
    try:
        # 게시글의 주인 정보를 가져옴
        post = supabase.table("posts").select("author_id").eq("id", post_id).single().execute().data
        
        if post:
            # 1. 게시글 주인에게 알림 (내가 내 글에 쓴 게 아닐 때)
            if str(post['author_id']) != str(session['user_id']):
                supabase.table("notifications").insert({
                    "user_id": post['author_id'],
                    "sender_name": session['username'],
                    "type": "comment",
                    "target_id": post_id,
                    "content": content[:20],  # 🔥 알림에 표시할 내용 추가
                    "is_read": False
                }).execute()
            
            # 2. 답글인 경우, 원댓글(부모댓글) 작성자에게도 알림 전송
            if parent_id:
                parent_cmt = supabase.table("comments").select("author_id").eq("id", parent_id).single().execute().data
                if parent_cmt and str(parent_cmt['author_id']) != str(session['user_id']):
                    # 게시글 주인과 원댓글 작성자가 다를 때만 중복 방지해서 보냄
                    if str(parent_cmt['author_id']) != str(post['author_id']):
                        supabase.table("notifications").insert({
                            "user_id": parent_cmt['author_id'],
                            "sender_name": session['username'],
                            "type": "comment", 
                            "target_id": post_id,
                            "content": content[:20],  # 🔥 알림에 표시할 내용 추가
                            "is_read": False
                        }).execute()
    except Exception as e:
        print(f"알림 전송 오류: {e}")
        
    return redirect(url_for('main.post_detail', post_id=post_id))