"""Minimal local stand-in for Supabase (GoTrue + PostgREST + Storage) backed by a real
PostgreSQL with the project's schema, RLS policies and triggers. Test-only."""
import json, base64, time, uuid, re, sys, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, unquote
from email.parser import BytesParser
from email.policy import default as email_default
import psycopg2, psycopg2.extras

DSN = "host=/tmp/pg16 port=5433 user=postgres dbname=q29"
FILES = {}          # (bucket, path) -> (bytes, content_type)
REFRESH = {}        # refresh_token -> uid
LOG = []

def b64(d): return base64.urlsafe_b64encode(json.dumps(d).encode()).decode().rstrip("=")
def make_jwt(uid, email):
    now = int(time.time())
    return b64({"alg": "HS256", "typ": "JWT"}) + "." + b64({"sub": uid, "email": email, "role": "authenticated", "aud": "authenticated", "exp": now + 3600, "iat": now}) + ".sig"
def jwt_sub(tok):
    try:
        p = tok.split(".")[1]; p += "=" * (-len(p) % 4)
        return json.loads(base64.urlsafe_b64decode(p))["sub"]
    except Exception: return None
def user_json(uid, email):
    return {"id": uid, "aud": "authenticated", "role": "authenticated", "email": email, "email_confirmed_at": "2026-01-01T00:00:00Z",
            "app_metadata": {"provider": "email", "providers": ["email"]}, "user_metadata": {}, "identities": [], "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"}

class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *a): pass
    def cors(self):
        self.send_header("Access-Control-Allow-Origin", "*"); self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,PATCH,PUT,DELETE,OPTIONS"); self.send_header("Access-Control-Expose-Headers", "*")
    def reply(self, code, body=None, ctype="application/json"):
        data = b"" if body is None else (body if isinstance(body, bytes) else json.dumps(body).encode())
        self.send_response(code); self.cors(); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(data))); self.end_headers()
        if data: self.wfile.write(data)
    def body(self):
        n = int(self.headers.get("Content-Length") or 0); return self.rfile.read(n) if n else b""
    def uid(self):
        a = self.headers.get("Authorization", "")
        tok = a[7:] if a.startswith("Bearer ") else ""
        return jwt_sub(tok) if tok.count(".") == 2 else None
    def db(self, uid, fn):
        c = psycopg2.connect(DSN)
        try:
            cur = c.cursor()
            cur.execute("set local role " + ("authenticated" if uid else "anon"))
            cur.execute("select set_config('request.jwt.claim.sub', %s, true)", (uid or "",))
            out = fn(cur); c.commit(); return out, None
        except psycopg2.Error as e:
            c.rollback(); code = e.pgcode or ""
            st = 403 if code == "42501" else 409 if code == "23505" else 400
            return None, (st, {"code": code, "message": (e.diag.message_primary or str(e)).strip(), "details": None, "hint": None})
        finally: c.close()
    def do_OPTIONS(self): self.reply(204)
    def route(self, method):
        u = urlparse(self.path); path = u.path; q = parse_qs(u.query, keep_blank_values=True)
        LOG.append((method, path))
        try:
            if path.startswith("/auth/v1/"): return self.auth(method, path[9:], q)
            if path.startswith("/rest/v1/rpc/"): return self.rpc(path[13:])
            if path.startswith("/rest/v1/"): return self.rest(method, path[9:], u.query)
            if path.startswith("/storage/v1/"): return self.storage(method, path[12:], q)
            self.reply(404, {"message": "not found"})
        except Exception as e:
            import traceback; traceback.print_exc(); self.reply(500, {"message": str(e)})
    do_GET = lambda s: s.route("GET"); do_POST = lambda s: s.route("POST"); do_PATCH = lambda s: s.route("PATCH"); do_DELETE = lambda s: s.route("DELETE"); do_PUT = lambda s: s.route("PUT")

    # ---------------- auth ----------------
    def auth(self, method, p, q):
        if p == "token":
            b = json.loads(self.body() or b"{}"); gt = q.get("grant_type", [""])[0]
            c = psycopg2.connect(DSN); cur = c.cursor()
            if gt == "password":
                cur.execute("select id::text, email from auth.users where email=%s and encrypted_password = extensions.crypt(%s, encrypted_password)", (b.get("email", "").lower(), b.get("password", "")))
            else:
                uid = REFRESH.get(b.get("refresh_token")); cur.execute("select id::text, email from auth.users where id=%s", (uid,)) if uid else cur.execute("select null, null where false")
            r = cur.fetchone(); c.close()
            if not r: return self.reply(400, {"code": 400, "error_code": "invalid_credentials", "msg": "Invalid login credentials"})
            rt = uuid.uuid4().hex; REFRESH[rt] = r[0]
            return self.reply(200, {"access_token": make_jwt(r[0], r[1]), "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": rt, "user": user_json(r[0], r[1])})
        if p == "user":
            uid = self.uid()
            if not uid: return self.reply(401, {"code": 401, "error_code": "no_authorization", "msg": "no user"})
            c = psycopg2.connect(DSN); cur = c.cursor(); cur.execute("select email from auth.users where id=%s", (uid,)); r = cur.fetchone(); c.close()
            if not r: return self.reply(403, {"code": 403, "error_code": "user_not_found", "msg": "User from sub claim in JWT does not exist"})
            return self.reply(200, user_json(uid, r[0]))
        if p == "logout": self.body(); return self.reply(204)
        return self.reply(404, {"msg": "auth route " + p})

    # ---------------- rest ----------------
    def parse_filters(self, qs):
        where, args, order, sel = [], [], "", "*"
        for part in [x for x in qs.split("&") if x]:
            k, _, v = part.partition("="); k = unquote(k); v = unquote(v)
            if k == "select": sel = v; continue
            if k == "order":
                col, _, d = v.partition("."); order = f' order by "{col}" {"desc" if d.startswith("desc") else "asc"}'; continue
            if k in ("limit", "offset", "columns", "on_conflict"): continue
            op, _, val = v.partition(".")
            if op == "eq": where.append(f'"{k}"::text = %s'); args.append(val)
            elif op == "in": where.append(f'"{k}"::text = any(%s)'); args.append([x.strip('"') for x in val.strip("()").split(",")])
            else: raise Exception("op " + op)
        return (" where " + " and ".join(where) if where else ""), args, order
    def rest(self, method, table, qs):
        if not re.fullmatch(r"[a-z_]+", table): return self.reply(400, {"message": "bad table"})
        uid = self.uid(); where, args, order = self.parse_filters(qs)
        single = "vnd.pgrst.object" in (self.headers.get("Accept") or "")
        ret = "return=representation" in (self.headers.get("Prefer") or "") or method == "GET"
        raw = self.body() if method in ("POST", "PATCH") else b""
        def fn(cur):
            t = f"public.{table}"
            if method == "GET":
                cur.execute(f"select to_jsonb(x) from {t} x{where}{order}", args)
            elif method == "POST":
                rows = json.loads(raw); rows = rows if isinstance(rows, list) else [rows]; out = []
                for r in rows:
                    cols = ",".join(f'"{c}"' for c in r)
                    cur.execute(f"insert into {t} ({cols}) select {cols} from json_populate_record(null::{t}, %s::json) returning to_jsonb({t}.*)", (json.dumps(r),)); out += cur.fetchall()
                return [o[0] for o in out]
            elif method == "PATCH":
                r = json.loads(raw); cols = ",".join(f'"{c}"' for c in r)
                cur.execute(f"update {t} set ({cols}) = (select {cols} from json_populate_record(null::{t}, %s::json)){where} returning to_jsonb({t}.*)", [json.dumps(r)] + args)
            elif method == "DELETE":
                cur.execute(f"delete from {t}{where} returning to_jsonb({t}.*)", args)
            return [r[0] for r in cur.fetchall()]
        rows, err = self.db(uid, fn)
        if err: return self.reply(*err)
        if single:
            if len(rows) != 1: return self.reply(406, {"code": "PGRST116", "message": "JSON object requested, multiple (or no) rows returned", "details": f"{len(rows)} rows", "hint": None})
            return self.reply(200, rows[0])
        if not ret: return self.reply(201 if method == "POST" else 204)
        return self.reply(201 if method == "POST" else 200, rows)
    def rpc(self, fn_name):
        if not re.fullmatch(r"[a-z0-9_]+", fn_name): return self.reply(400, {"message": "bad fn"})
        a = json.loads(self.body() or b"{}"); uid = self.uid()
        named = ",".join(f"{k} => %s" for k in a)
        args = [json.dumps(v) if isinstance(v, (list, dict)) else v for v in a.values()]
        if fn_name == "q29_track": named = ",".join(f"{k} => %s::jsonb" for k in a)
        agg = fn_name in ("q29_views", "q29_stats", "q29_public_ann")
        sql = f"select coalesce(json_agg(t),'[]')::text from public.{fn_name}({named}) t" if agg else f"select public.{fn_name}({named})::text" if fn_name not in ("q29_hit", "q29_track") else f"select null::text from public.{fn_name}({named})"
        res, err = self.db(uid, lambda cur: (cur.execute(sql, args), cur.fetchone()[0])[1])
        if agg and not err: return self.reply(200, json.loads(res))
        if err: return self.reply(*err)
        return self.reply(200, res)

    # ---------------- storage ----------------
    def storage(self, method, p, q):
        uid = self.uid()
        m = re.fullmatch(r"object/sign/([^/]+)", p)
        if m and method == "POST":
            b = json.loads(self.body()); bucket = m.group(1); out = []
            for path in b.get("paths", []):
                ok, err = self.db(uid, lambda cur: (cur.execute("select count(*) from storage.objects where bucket_id=%s and name=%s", (bucket, path)), cur.fetchone()[0])[1])
                if ok: out.append({"path": path, "signedURL": f"/object/sign/{bucket}/{path}?token=t{uuid.uuid4().hex[:8]}", "error": None})
                else: out.append({"path": path, "signedURL": None, "error": "Either the object does not exist or you do not have access to it"})
            return self.reply(200, out)
        m = re.fullmatch(r"object/sign/([^/]+)/(.+)", p)
        if m and method == "GET":
            f = FILES.get((m.group(1), unquote(m.group(2))))
            return self.reply(200, f[0], f[1]) if f else self.reply(404, {"message": "not found"})
        m = re.fullmatch(r"object/([^/]+)", p)
        if m and method == "DELETE":
            b = json.loads(self.body()); bucket = m.group(1)
            rows, err = self.db(uid, lambda cur: (cur.execute("delete from storage.objects where bucket_id=%s and name = any(%s) returning name", (bucket, b.get("prefixes", []))), [r[0] for r in cur.fetchall()])[1])
            if err: return self.reply(*err)
            for n in rows: FILES.pop((bucket, n), None)
            return self.reply(200, [{"name": n} for n in rows])
        m = re.fullmatch(r"object/([^/]+)/(.+)", p)
        if m and method in ("POST", "PUT"):
            bucket, path = m.group(1), unquote(m.group(2)); raw = self.body(); ctype = self.headers.get("Content-Type", "")
            if ctype.startswith("multipart/form-data"):
                msg = BytesParser(policy=email_default).parsebytes(b"Content-Type: " + ctype.encode() + b"\r\n\r\n" + raw)
                data, ftype = b"", "application/octet-stream"
                for part in msg.iter_parts():
                    if part.get_filename() is not None or part.get_param("name", header="content-disposition") == "":
                        data = part.get_payload(decode=True); ftype = part.get_content_type()
            else: data, ftype = raw, ctype
            c = psycopg2.connect(DSN); cur = c.cursor(); cur.execute("select file_size_limit, allowed_mime_types from storage.buckets where id=%s", (bucket,)); bk = cur.fetchone(); c.close()
            if bk and bk[1] and ftype not in bk[1]: return self.reply(400, {"statusCode": "415", "error": "invalid_mime_type", "message": f"mime type {ftype} is not supported"})
            if bk and bk[0] and len(data) > bk[0]: return self.reply(400, {"statusCode": "413", "error": "Payload too large", "message": "The object exceeded the maximum allowed size"})
            _, err = self.db(uid, lambda cur: cur.execute("insert into storage.objects(bucket_id,name,owner) values(%s,%s,%s)", (bucket, path, uid)))
            if err: return self.reply(403, {"statusCode": "403", "error": "Unauthorized", "message": "new row violates row-level security policy"})
            FILES[(bucket, path)] = (data, ftype)
            return self.reply(200, {"Key": f"{bucket}/{path}", "Id": str(uuid.uuid4())})
        return self.reply(404, {"message": "storage route " + p})

def serve(port=54321):
    srv = ThreadingHTTPServer(("127.0.0.1", port), H); threading.Thread(target=srv.serve_forever, daemon=True).start(); return srv

if __name__ == "__main__":
    serve(); print("mock supabase on :54321"); threading.Event().wait()
