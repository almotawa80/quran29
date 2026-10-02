import psycopg2, json, sys
DSN = "host=/tmp/pg16 port=5433 user=postgres dbname=q29"
fails = []
def ok(c, m):
    print(("OK   " if c else "FAIL ") + m)
    if not c: fails.append(m)

su = psycopg2.connect(DSN); su.autocommit = True
q = su.cursor()
q.execute("truncate public.candidates, public.entities cascade; delete from storage.objects; delete from auth.users where email<>'admin@quran29.local'")
q.execute("select id from auth.users where email='admin@quran29.local'"); ADMIN = q.fetchone()[0]
q.execute("insert into members(user_id,role) values(%s,'admin') on conflict do nothing", (ADMIN,))

def as_user(uid):
    c = psycopg2.connect(DSN); c.autocommit = False
    cur = c.cursor(); cur.execute("set role authenticated"); cur.execute("select set_config('request.jwt.claim.sub', %s, false)", (str(uid) if uid else "",))
    return c, cur
def run(uid, sql, args=()):
    """returns (rows|None, error|None); commits on success"""
    c, cur = as_user(uid)
    try:
        cur.execute(sql, args)
        rows = cur.fetchall() if cur.description else cur.rowcount
        c.commit(); return rows, None
    except Exception as e:
        c.rollback(); return None, str(e).split("\n")[0]
    finally: c.close()
def uid_of(u):
    q.execute("select id from auth.users where email=%s", (u + "@quran29.local",)); r = q.fetchone(); return r and r[0]
def cand(ent, cid, status="draft", br="youth", sl="j5"):
    return json.dumps({"br": br, "sl": sl, "name": "x"}), ent, cid, status

# --- admin creates two entities + accounts
r, e = run(ADMIN, "insert into entities(name,username,rev_username,rev_name) values('مركز الهدى','huda','sara.rev','سارة') returning id"); E1 = r[0][0]
r, e = run(ADMIN, "insert into entities(name,username) values('مدرسة الفرقان','furqan') returning id"); E3 = r[0][0]
ok(e is None, "admin can create entities")
for ent, role, u in [(E1, "entry", "huda"), (E1, "reviewer", "sara.rev"), (E3, "entry", "furqan")]:
    _, e = run(ADMIN, "select admin_create_account(%s,%s,%s,%s)", (ent, role, u, "pass123")); ok(e is None, f"admin creates account {u} ({role}) {e or ''}")
HUDA, SARA, FURQ = uid_of("huda"), uid_of("sara.rev"), uid_of("furqan")
q.execute("select encrypted_password = extensions.crypt('pass123', encrypted_password) from auth.users where id=%s", (HUDA,)); ok(q.fetchone()[0], "password stored as bcrypt hash and verifies")
_, e = run(HUDA, "select admin_create_account(%s,'entry','hacker','pass123')", (E1,)); ok(e and "not_allowed" in e, "non-admin cannot create accounts")
_, e = run(None, "select * from entities"); ok(e is not None or _ == [], "anonymous visitor cannot read entities")
_, e = run(HUDA, "select public._create_account('x','pass123')"); ok(e and "permission denied" in e, "internal account function is not callable")
_, e = run(ADMIN, "select admin_create_account(%s,'entry','furqan','pass123')", (E1,)); ok(e and "username_taken" in e, "duplicate username rejected")
q.execute("select count(*) from members where ent_id=%s and role='entry'", (E1,)); ok(q.fetchone()[0] == 1, "failed create did not remove the existing account (atomic)")

# --- visibility
r, _ = run(HUDA, "select name from entities"); ok([x[0] for x in r] == ["مركز الهدى"], "coordinator sees only own entity")
r, _ = run(SARA, "select name from entities"); ok([x[0] for x in r] == ["مركز الهدى"], "reviewer sees only own entity")
r, _ = run(ADMIN, "select count(*) from entities"); ok(r[0][0] == 2, "admin sees all entities")
_, e = run(HUDA, "update entities set name='x' where id=%s", (E1,)); r, _ = run(ADMIN, "select name from entities where id=%s", (E1,)); ok(r[0][0] == "مركز الهدى", "coordinator cannot edit entity record")
_, e = run(HUDA, "update members set role='admin' where user_id=%s", (HUDA,)); r, _ = run(ADMIN, "select role from members where user_id=%s", (HUDA,)); ok(r[0][0] == "entry", "coordinator cannot promote self to admin")

# --- candidates
_, e = run(HUDA, "insert into candidates(data,ent_id,cid,status) values(%s,%s,%s,%s)", cand(E1, "c1", "pending")); ok(e is None, f"coordinator adds candidate (pending) {e or ''}")
_, e = run(HUDA, "insert into candidates(data,ent_id,cid,status) values(%s,%s,%s,%s)", cand(E3, "c9")); ok(e is not None, "coordinator cannot add to another entity")
_, e = run(HUDA, "insert into candidates(data,ent_id,cid,status) values(%s,%s,%s,%s)", cand(E1, "c2", "approved")); ok(e and "reviewer_must_approve", "entity with reviewer: coordinator cannot self-approve")
_, e = run(FURQ, "insert into candidates(data,ent_id,cid,status) values(%s,%s,%s,%s)", cand(E3, "c1")); ok(e and "duplicate key" in e, "same civil ID cannot be registered in two entities")
_, e = run(FURQ, "insert into candidates(data,ent_id,cid,status) values(%s,%s,%s,%s)", cand(E3, "f1", "approved")); ok(e is None, "entity without reviewer: approves directly")
r, _ = run(HUDA, "select cid from candidates"); ok([x[0] for x in r] == ["c1"], "coordinator sees only own candidates")
r, _ = run(ADMIN, "select count(*) from candidates"); ok(r[0][0] == 2, "admin sees all candidates")
_, e = run(SARA, "update candidates set data=data||'{\"name\":\"y\"}' where cid='c1'"); ok(e and "reviewer_cannot_edit" in e, "reviewer cannot edit candidate data")
_, e = run(SARA, "update candidates set status='approved' where cid='c1'"); ok(e is None, "reviewer approves")
_, e = run(HUDA, "update candidates set data=data||'{\"name\":\"z\"}' where cid='c1'"); ok(e and "reviewer_must_approve" in e, "coordinator cannot silently edit an approved candidate (must go back to review)")
_, e = run(HUDA, "update candidates set data=data||'{\"name\":\"z\"}', status='pending' where cid='c1'"); ok(e is None, "coordinator edit sends it back to review")
_, e = run(HUDA, "update candidates set status='corrected' where cid='c1'"); ok(e and "bad_status" in e, "coordinator cannot set 'corrected'")
_, e = run(SARA, "update candidates set status='corrected', review_note='صورة غير واضحة' where cid='c1'"); ok(e is None, "reviewer returns with note")
_, e = run(ADMIN, "update candidates set status='corrected', review_note='x' where cid='f1'"); ok(e is None, "admin returns an approved candidate")
# slice cap
for i in range(5):
    run(FURQ, "insert into candidates(data,ent_id,cid,status) values(%s,%s,%s,%s)", cand(E3, f"s{i}", "approved", "youth", "j3"))
_, e = run(FURQ, "insert into candidates(data,ent_id,cid,status) values(%s,%s,%s,%s)", cand(E3, "s5", "approved", "youth", "j3")); ok(e and "slice_full" in e, "6th approval in the same slice is blocked on the server")
_, e = run(FURQ, "insert into candidates(data,ent_id,cid,status) values(%s,%s,%s,%s)", cand(E3, "s6", "draft", "youth", "j3")); ok(e is None, "drafts don't take seats")
# per-gender cap: 5 males + 5 females in the same slice
def gcand(ent, cid, g): return json.dumps({"br": "youth", "sl": "j2", "gender": g}), ent, cid, "approved"
res = [run(FURQ, "insert into candidates(data,ent_id,cid,status) values(%s,%s,%s,%s)", gcand(E3, f"m{i}", "ذكر"))[1] for i in range(5)]
res += [run(FURQ, "insert into candidates(data,ent_id,cid,status) values(%s,%s,%s,%s)", gcand(E3, f"w{i}", "أنثى"))[1] for i in range(5)]
ok(all(x is None for x in res), "5 males and 5 females approved in the same slice")
_, e = run(FURQ, "insert into candidates(data,ent_id,cid,status) values(%s,%s,%s,%s)", gcand(E3, "m5", "ذكر")); ok(e and "slice_full" in e, "6th male blocked")
_, e = run(FURQ, "insert into candidates(data,ent_id,cid,status) values(%s,%s,%s,%s)", gcand(E3, "w5", "أنثى")); ok(e and "slice_full" in e, "6th female blocked")
_, e = run(FURQ, "insert into candidates(data,ent_id,cid,status) values(%s,%s,%s,%s)", (json.dumps({"br":"youth","sl":"j2","gender":"أنثى"}), E3, "w6", "draft"))
_, e2 = run(FURQ, "update candidates set status='approved', data=data||'{\"gender\":\"ذكر\"}' where cid='w6'"); ok(e2 and "slice_full" in e2, "switching gender into a full group is blocked")
# deactivate entity
run(ADMIN, "update entities set active=false where id=%s", (E3,))
r, _ = run(FURQ, "select count(*) from candidates"); ok(r[0][0] == 0, "deactivated entity loses access")
run(ADMIN, "update entities set active=true where id=%s", (E3,))
# passwords & removal
_, e = run(ADMIN, "select admin_set_password(%s,'entry','newpass9')", (E1,))
q.execute("select encrypted_password = extensions.crypt('newpass9', encrypted_password) from auth.users where id=%s", (HUDA,)); ok(e is None and q.fetchone()[0], "admin resets a password")
_, e = run(ADMIN, "select admin_remove_account(%s,'reviewer')", (E1,)); ok(e is None and uid_of("sara.rev") is None, "admin removes the reviewer account")
# storage
q.execute("insert into storage.objects(bucket_id,name) values('docs', %s), ('docs', %s)", (f"{E1}/c1/cid.jpg", f"{E3}/f1/cid.jpg"))
r, _ = run(HUDA, "select name from storage.objects"); ok(len(r) == 1 and r[0][0].startswith(str(E1)), "coordinator reads only own entity's documents")
_, e = run(HUDA, "insert into storage.objects(bucket_id,name) values('docs', %s)", (f"{E3}/x/cid.jpg",)); ok(e is not None, "coordinator cannot upload into another entity's folder")
_, e = run(HUDA, "insert into storage.objects(bucket_id,name) values('docs', %s)", (f"{E1}/c1/cid2.jpg",)); ok(e is None, "coordinator uploads into own folder")
r, _ = run(ADMIN, "select count(*) from storage.objects"); ok(r[0][0] == 3, "admin reads all documents")
r, _ = run(None, "select count(*) from storage.objects"); ok(r is None or r[0][0] == 0, "anonymous cannot read documents")
# entity delete cascades
_, e = run(ADMIN, "delete from entities where id=%s", (E3,)); r, _ = run(ADMIN, "select count(*) from candidates where ent_id=%s", (E3,)); ok(e is None and r[0][0] == 0, "deleting an entity removes its candidates")
# --- cancelled status
r, e = run(ADMIN, "insert into entities(name,username) values('جهة الإلغاء','cxent') returning id"); E4 = r[0][0]
run(ADMIN, "select admin_create_account(%s,'entry','cxent','pass123')", (E4,)); CX = uid_of("cxent")
for i in range(5): run(CX, "insert into candidates(data,ent_id,cid,status) values(%s,%s,%s,%s)", cand(E4, f"k{i}", "approved", "youth", "j3"))
_, e = run(CX, "insert into candidates(data,ent_id,cid,status) values(%s,%s,%s,%s)", cand(E4, "cx0", "cancelled")); ok(e and "bad_status" in e, "cannot insert a candidate as cancelled")
_, e = run(CX, "update candidates set status='cancelled' where cid='k0'"); ok(e is None, "coordinator cancels an approved candidate")
_, e = run(CX, "insert into candidates(data,ent_id,cid,status) values(%s,%s,%s,%s)", cand(E4, "k7", "approved", "youth", "j3")); ok(e is None, "cancelled candidate frees the seat")
_, e = run(CX, "update candidates set status='approved' where cid='k0'"); ok(e and "bad_status" in e, "cancelled cannot jump straight back to approved")
_, e = run(CX, "update candidates set data=data||'{\"name\":\"y\"}' where cid='k0'"); ok(e and "bad_status" in e, "cancelled candidate's data cannot be edited")
_, e = run(CX, "update candidates set status='draft' where cid='k0'"); ok(e is None, "coordinator restores a cancelled candidate as a draft")
r, e = run(CX, "delete from candidates where cid='k1' returning id"); ok(r == [] or r == 0, "coordinator cannot delete an approved candidate")
run(CX, "update candidates set status='cancelled' where cid='k1'")
r, e = run(CX, "delete from candidates where cid='k1' returning id"); ok(r and len(r) == 1, "coordinator deletes a cancelled candidate")
r, e = run(CX, "delete from candidates where cid='k0' returning id"); ok(r and len(r) == 1, "coordinator deletes a draft")
r, e = run(ADMIN, "delete from candidates where cid='k2' returning id"); ok(r and len(r) == 1, "admin deletes any candidate")
# --- visit counter
def run_anon(sql):
    c = psycopg2.connect(DSN); c.autocommit = False; cur = c.cursor(); cur.execute("set role anon")
    try: cur.execute(sql); rows = cur.fetchall() if cur.description else None; c.commit(); return rows, None
    except Exception as e: c.rollback(); return None, str(e).split("\n")[0]
    finally: c.close()
_, e = run_anon("select public.q29_hit()"); run_anon("select public.q29_hit()"); ok(e is None, "anonymous visitor can record a visit")
_, e = run_anon("select * from public.page_views"); ok(e is not None, "anonymous cannot read the visits table")
_, e = run_anon("select * from public.q29_views()"); ok(e is not None, "anonymous cannot read visit counts")
r, e = run(HUDA, "select * from public.q29_views()"); ok(e is None and r == [], "coordinator sees no visit counts")
r, e = run(ADMIN, "select n from public.q29_views()"); ok(e is None and r and r[-1][0] >= 2, f"admin reads visit counts {r}")
print("\nFAILS:", fails); sys.exit(1 if fails else 0)
