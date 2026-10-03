# أدوات تطوير دليل مسابقة الكويت الكبرى (29)

هذا المجلد لا يظهر في الموقع (GitHub Pages يتجاهل المجلدات التي تبدأ بـ `_`)، وهو مرجع لأي جلسة عمل قادمة.

## الملفات
| المسار | المحتوى |
|---|---|
| `src/guide_github.html` | **المصدر الكامل لنسخة GitHub** (بيانات حقيقية + شعار الأمانة + صور اللجنة). كل التعديلات تبدأ منه. |
| `src/guide_claude.html` | نسخة Claude (بيانات تجريبية، بلا شعار الأمانة) المنشورة على رابط Artifact. |
| `src/sw.js` | دعم العمل دون إنترنت لنسخة GitHub (يُنسخ إلى جذر المستودع باسم `sw.js`). عند تغيير ملفات البيانات أو الخط غيّر رقم `CACHE` فيه. |
| `build_gh.py` | يقسّم المصدر إلى `index.html` + `qz-data.txt` + `hafs.woff2` (تحميل بيانات اللعبة عند الحاجة). |
| `run_tests.sh` | يشغّل الاختبارات الرئيسية على النسختين. |
| `tests/` | اختبارات Playwright (test2–test32, a11y) و `mock_sb.py` (بديل محلي لـ Supabase مع PostgreSQL). |
| `sql/` | ملفات Supabase: `supabase_setup.sql` ثم `update_2` … `update_8` (كلها مطبّقة على القاعدة الحية؛ `update_8` لتقييم إجابات المساعد، طُبّق 3 أكتوبر 2026). |
| `team/` | صور اللجنة الدائمة بالخلفية الموحدة + رمز الحجاب. |
| `game/` | مصدر لعبة «اختبر حفظي». |

## خطوات أي تعديل
1. عدّل **الملفين معاً** في `src/` (منطقة البوابة بين `// PORTAL-EMBED-START` و `// PORTAL-EMBED-END` يجب أن تكون متطابقة فيهما ما عدا `GUIDE_URL`).
2. شغّل: `bash _dev/run_tests.sh` ويجب أن ينتهي بـ `ALL GREEN`.
3. انشر نسخة Claude على رابط الـ Artifact المعتمد واعرض النتيجة على خالد.
4. **لا رفع إلى GitHub ولا تشغيل SQL قبل أن يقول خالد «ارفع».**
5. عند الرفع:
   ```bash
   B=$(TZ=Asia/Kuwait date +%Y%m%d%H%M%S)
   sed -i -E "s/(<meta name=\"build\" content=\")[0-9]+/\1$B/" _dev/src/guide_github.html
   python3 _dev/build_gh.py _dev/src/guide_github.html /tmp/ghsplit
   bash _dev/run_tests.sh            # يجب ALL GREEN
   cp /tmp/ghsplit/index.html /tmp/ghsplit/qz-data.txt /tmp/ghsplit/hafs.woff2 .
   cp _dev/src/sw.js sw.js
   git add -A && git commit -m "..." && git push
   ```

## قواعد ثابتة
- البيان التوضيحي (PDF) هو المرجع في الصياغة والأرقام.
- البيانات الحقيقية في نسخة GitHub فقط؛ نسخة Claude بيانات تجريبية وبلا شعار الأمانة.
- لا يُطلب ولا يُستخدم مفتاح Supabase السري أبداً؛ المفتاح المنشور (publishable) فقط في الكود.
- ملفات SQL بأحرف ASCII فقط، وتُشغّل من SQL Editor في Supabase.
- قبل أي تغيير في الشكل: نموذج أو صورة للموافقة أولاً.
